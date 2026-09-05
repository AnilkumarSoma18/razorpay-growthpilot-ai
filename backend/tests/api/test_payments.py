
import pytest
import uuid
from unittest.mock import MagicMock
from app.api.payments import create_razorpay_order, verify_payment, razorpay_webhook
from app.api.payments import RazorpayOrderReq, VerifyPaymentReq
from fastapi import HTTPException, Request

def test_create_razorpay_order_validates_status():
    mock_db = MagicMock()
    mock_order = MagicMock()
    mock_order.status.value = "paid" # not pending
    mock_db.get.return_value = mock_order
    
    req = RazorpayOrderReq(internal_order_id=uuid.uuid4())
    with pytest.raises(HTTPException) as excinfo:
        create_razorpay_order(req, mock_db)
    
    assert excinfo.value.status_code == 400

def test_verify_payment_signature():
    mock_db = MagicMock()
    mock_payment = MagicMock()
    mock_db.execute.return_value.scalars.return_value.first.return_value = mock_payment
    
    req = VerifyPaymentReq(
        razorpay_order_id="order_123",
        razorpay_payment_id="pay_123",
        razorpay_signature="valid_mock"
    )
    
    res = verify_payment(req, mock_db)
    assert res["status"] == "PAYMENT_PENDING"

def test_verify_payment_invalid_signature():
    mock_db = MagicMock()
    mock_payment = MagicMock()
    mock_db.execute.return_value.scalars.return_value.first.return_value = mock_payment
    
    req = VerifyPaymentReq(
        razorpay_order_id="order_123",
        razorpay_payment_id="pay_123",
        razorpay_signature="invalid"
    )
    
    with pytest.raises(HTTPException):
        verify_payment(req, mock_db)
