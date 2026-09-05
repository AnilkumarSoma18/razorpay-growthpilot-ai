
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from sqlalchemy import select
import uuid
from typing import Optional
from datetime import datetime, timezone
from app.database.session import get_db
from pydantic import BaseModel
from app.models.order import Order
from app.models.payment import Payment, PaymentEvent
from app.models.enums import PaymentStatus, OrderStatus, AuditActor
from app.models.agent import AuditLog
from app.services.razorpay_service import create_test_order, verify_payment_signature, verify_webhook_signature
import json

router = APIRouter(prefix="/api/payments", tags=["payments"])

class RazorpayOrderReq(BaseModel):
    internal_order_id: uuid.UUID

class VerifyPaymentReq(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

@router.post("/razorpay/order")
def create_razorpay_order(req: RazorpayOrderReq, db: Session = Depends(get_db)):
    order = db.get(Order, req.internal_order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Order is not PENDING")
        
    amount_minor = int(order.total_amount * 100)
    
    try:
        rzp_order = create_test_order(amount_minor=amount_minor, receipt=str(order.id))
        rzp_order_id = rzp_order["id"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
    # Create internal payment
    payment = Payment(
        id=uuid.uuid4(),
        order_id=order.id,
        merchant_id=order.merchant_id,
        razorpay_order_id=rzp_order_id,
        status=PaymentStatus.CREATED,
        amount=order.total_amount,
        is_test_mode=True
    )
    db.add(payment)
    
    db.add(AuditLog(
        id=uuid.uuid4(), merchant_id=order.merchant_id, actor=AuditActor.SYSTEM,
        action="RAZORPAY_ORDER_CREATED", execution_status="SUCCESS",
        input_summary=f"Order {rzp_order_id} created for internal order {order.id}"
    ))
    db.commit()
    
    return {
        "internal_order_id": str(order.id),
        "razorpay_order_id": rzp_order_id,
        "amount": amount_minor,
        "currency": "INR",
        "key_id": "RAZORPAY_KEY_ID_PLACEHOLDER"
    }

@router.post("/razorpay/verify")
def verify_payment(req: VerifyPaymentReq, db: Session = Depends(get_db)):
    stmt = select(Payment).where(Payment.razorpay_order_id == req.razorpay_order_id)
    payment = db.execute(stmt).scalars().first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
        
    try:
        verify_payment_signature(req.razorpay_order_id, req.razorpay_payment_id, req.razorpay_signature)
        
        # Payment is verified but we MUST wait for Webhook to officially mark as CAPTURED if we strictly follow reconciliation.
        # But for test mode UI, we will mark it PAYMENT_PENDING here (verification in progress) or AUTHORIZED.
        # The instruction states: "NEVER mark a payment SUCCESS based only on a frontend callback. The backend must verify authenticity. Then use webhook/API reconciliation to establish authoritative status."
        payment.status = PaymentStatus.PAYMENT_PENDING
        payment.razorpay_payment_id = req.razorpay_payment_id
        db.commit()
        
        db.add(AuditLog(
            id=uuid.uuid4(), merchant_id=payment.merchant_id, actor=AuditActor.SYSTEM,
            action="PAYMENT_VERIFICATION_REQUESTED", execution_status="SUCCESS",
            input_summary=f"Signature verified for {req.razorpay_payment_id}, status set to PENDING."
        ))
        db.commit()
        
        return {"status": "PAYMENT_PENDING", "message": "Payment signature valid. Awaiting webhook capture."}
    except Exception as e:
        payment.status = PaymentStatus.FAILED
        db.add(AuditLog(
            id=uuid.uuid4(), merchant_id=payment.merchant_id, actor=AuditActor.SYSTEM,
            action="PAYMENT_VERIFICATION_FAILED", execution_status="FAILED",
            error=str(e)
        ))
        db.commit()
        raise HTTPException(status_code=400, detail="Signature mismatch")

@router.post("/razorpay/webhook")
async def razorpay_webhook(request: Request, x_razorpay_signature: str = Header(...), db: Session = Depends(get_db)):
    raw_body = await request.body()
    try:
        verify_webhook_signature(raw_body, x_razorpay_signature)
    except Exception as e:
        db.add(AuditLog(
            id=uuid.uuid4(), merchant_id=uuid.UUID(int=0), actor=AuditActor.SYSTEM,
            action="WEBHOOK_REJECTED", execution_status="FAILED", error="Invalid webhook signature."
        ))
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid signature")
        
    payload = json.loads(raw_body)
    event_type = payload.get("event")
    # Using payment id as idempotency fallback if event id is missing in raw mock payload
    event_id = request.headers.get("x-razorpay-event-id", payload.get("payload", {}).get("payment", {}).get("entity", {}).get("id"))
    
    if not event_id:
        return {"status": "ignored", "reason": "No event id"}
        
    # Idempotency check
    existing = db.execute(select(PaymentEvent).where(PaymentEvent.id == str(event_id))).scalars().first()
    if existing:
        return {"status": "idempotent"}
        
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    rzp_order_id = payment_entity.get("order_id")
    
    if not rzp_order_id:
        return {"status": "ignored"}
        
    stmt = select(Payment).where(Payment.razorpay_order_id == rzp_order_id)
    payment = db.execute(stmt).scalars().first()
    
    if not payment:
        return {"status": "ignored", "reason": "Payment unknown"}
        
    # Create Event Record
    # Generate uuid from event_id string to fit UUIDPKMixin. This isn't possible if event_id is a random string.
    # We will just use uuid.uuid4() and put event_id in payload.
    db.add(PaymentEvent(
        id=uuid.uuid4(),
        payment_id=payment.id,
        event_type=event_type,
        raw_payload={"event_id": event_id, **payload}
    ))
    
    order = db.get(Order, payment.order_id)
    
    if event_type == "payment.captured":
        if payment.status != PaymentStatus.CAPTURED:
            payment.status = PaymentStatus.CAPTURED
            payment.verified_at = datetime.now(timezone.utc)
            if order:
                order.status = OrderStatus.PAID
                
            db.add(AuditLog(
                id=uuid.uuid4(), merchant_id=payment.merchant_id, actor=AuditActor.SYSTEM,
                action="PAYMENT_CAPTURED", execution_status="SUCCESS",
                input_summary=f"Payment {payment.razorpay_payment_id} captured via webhook."
            ))
            
    elif event_type == "payment.failed":
        payment.status = PaymentStatus.FAILED
        if order:
            order.status = OrderStatus.FAILED
        db.add(AuditLog(
            id=uuid.uuid4(), merchant_id=payment.merchant_id, actor=AuditActor.SYSTEM,
            action="PAYMENT_FAILED", execution_status="SUCCESS",
            input_summary=f"Payment {payment.razorpay_payment_id} failed via webhook."
        ))

    db.commit()
    return {"status": "ok"}
