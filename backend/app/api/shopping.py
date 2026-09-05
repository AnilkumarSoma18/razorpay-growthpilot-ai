from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
import uuid
from typing import Optional, List, Dict, Any
from app.database.session import get_db
from pydantic import BaseModel
from app.ml.recommendation_model import RecommendationModel
ml_model = RecommendationModel(version="1.0-alpha")
# Mock load
ml_model.popular_products = ["some_id"]
from app.agents.shopping_agent import shopping_app
from app.services.shopping_service import search_products, get_or_create_cart, get_cart_items, add_to_cart, create_order_from_cart
from app.models.core import Customer

router = APIRouter(prefix="/api/shopping", tags=["shopping"])

class ChatRequest(BaseModel):
    merchant_id: uuid.UUID
    session_id: str
    message: str
    customer_id: Optional[uuid.UUID] = None

class ActionRequest(BaseModel):
    merchant_id: uuid.UUID
    session_id: str
    product_id: uuid.UUID
    action: str # add_to_cart, checkout

@router.post("/chat")
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    # Run agent
    initial_state = {
        "merchant_id": str(req.merchant_id),
        "session_id": req.session_id,
        "message": req.message,
        "intent": None,
        "constraints": {},
        "candidate_products": [],
        "response": ""
    }
    
    final_state = shopping_app.invoke(initial_state)
    
    # Deterministic Tool Execution based on Agent Intent
    products = []
    if final_state.get("intent") == "SEARCH":
        constraints = final_state.get("constraints", {})
        query = constraints.get("query", "")
        max_price = constraints.get("max_price", None)
        
        db_products = search_products(db, req.merchant_id, query, max_price)

        raw_products = []
        for p in db_products:
            raw_products.append({
                "id": str(p.id),
                "name": p.name,
                "price": round(Decimal(str(p.price)), 2),
                "description": p.description
            })
            
        ranked = ml_model.predict_rank(raw_products, customer_history=None)
        
        for r in ranked:
            p = r["product"]
            p["reason"] = r["reason"] + (f" (Budget {max_price})" if max_price else "")
            p["score"] = r["score"]
            p["ml_version"] = r["ml_version"]
            products.append(p)
            
    if final_state.get("intent") == "SEARCH" and not products:
        response = "I couldn't find any products matching your constraints."
    else:
        response = final_state.get("response", "How can I help?")

    return {
        "response": response,
        "intent": final_state.get("intent"),
        "products": products
    }

@router.post("/action")
def shopping_action(req: ActionRequest, db: Session = Depends(get_db)):
    cart = get_or_create_cart(db, req.merchant_id, req.session_id)
    
    if req.action == "add_to_cart":
        add_to_cart(db, cart.id, req.product_id, 1)
        return {"status": "success", "message": "Added to cart"}
        
    elif req.action == "checkout":
        # Usually requires customer_id, use a dummy or fetch
        customer = db.execute(select(Customer).where(Customer.merchant_id == req.merchant_id)).scalars().first()
        if not customer:
            raise HTTPException(status_code=400, detail="No customer found for checkout")
            
        try:
            order = create_order_from_cart(db, cart, customer.id)
            return {"status": "success", "internal_order_id": str(order.id)}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
            
    raise HTTPException(status_code=400, detail="Unknown action")

@router.get("/cart")
def get_cart_view(merchant_id: uuid.UUID, session_id: str, db: Session = Depends(get_db)):
    cart = get_or_create_cart(db, merchant_id, session_id)
    items = get_cart_items(db, cart.id)
    
    res = []
    total = 0.0
    for item, product in items:
        res.append({
            "id": str(item.id),
            "product_id": str(product.id),
            "name": product.name,
            "quantity": item.quantity,
            "price": float(product.price),
            "subtotal": round(Decimal(str(product.price)) * Decimal(item.quantity), 2)
        })
        total += round(Decimal(str(product.price)) * Decimal(item.quantity), 2)
        
    return {"items": res, "total": total}
