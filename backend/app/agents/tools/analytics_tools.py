
from sqlalchemy.orm import Session
import uuid
from typing import Dict, Any
from app.services.analytics_service import (
    get_revenue_metrics,
    get_conversion_metrics,
    get_aov_metrics,
    get_retention_metrics,
    _merchant_or_404
)
from sqlalchemy import select, func, desc
from app.models.order import OrderItem, Order
from app.models.product import Product
from app.models.enums import OrderStatus

def get_merchant_summary(db: Session, merchant_id: uuid.UUID) -> Dict[str, Any]:
    revenue = get_revenue_metrics(db, merchant_id)
    conversion = get_conversion_metrics(db, merchant_id)
    aov = get_aov_metrics(db, merchant_id)
    retention = get_retention_metrics(db, merchant_id)
    
    return {
        "revenue": revenue,
        "conversion": conversion,
        "aov": aov,
        "retention": retention
    }

def get_top_products(db: Session, merchant_id: uuid.UUID, limit: int = 5) -> list[Dict[str, Any]]:
    # Deterministic calculation of top products by revenue
    stmt = (
        select(
            Product.id,
            Product.name,
            func.sum(OrderItem.total_price).label("revenue"),
            func.sum(OrderItem.quantity).label("units_sold")
        )
        .join(OrderItem, OrderItem.product_id == Product.id)
        .join(Order, Order.id == OrderItem.order_id)
        .where(Order.merchant_id == merchant_id, Order.status == OrderStatus.PAID)
        .group_by(Product.id, Product.name)
        .order_by(desc("revenue"))
        .limit(limit)
    )
    results = db.execute(stmt).all()
    return [
        {
            "product_id": str(r.id),
            "name": r.name,
            "revenue": float(r.revenue or 0),
            "units_sold": int(r.units_sold or 0)
        } for r in results
    ]

def get_cross_sell_signals(db: Session, merchant_id: uuid.UUID) -> list[Dict[str, Any]]:
    # Simplified cross-sell detection: products frequently bought in the same order
    # (Since writing complex SQL might be out of scope for a quick demo, we'll do a basic co-occurrence query)
    stmt = """
        SELECT 
            oi1.product_id as p1_id,
            p1.name as p1_name,
            oi2.product_id as p2_id,
            p2.name as p2_name,
            count(DISTINCT o.id) as co_purchases
        FROM orders o
        JOIN order_items oi1 ON o.id = oi1.order_id
        JOIN order_items oi2 ON o.id = oi2.order_id AND oi1.product_id != oi2.product_id
        JOIN products p1 ON oi1.product_id = p1.id
        JOIN products p2 ON oi2.product_id = p2.id
        WHERE o.merchant_id = :merchant_id AND o.status = 'PAID'
        GROUP BY p1_id, p1_name, p2_id, p2_name
        HAVING count(DISTINCT o.id) > 2
        ORDER BY co_purchases DESC
        LIMIT 10
    """
    from sqlalchemy import text
    results = db.execute(text(stmt), {"merchant_id": merchant_id}).all()
    
    signals = []
    seen = set()
    for r in results:
        pair = tuple(sorted([str(r.p1_id), str(r.p2_id)]))
        if pair in seen: continue
        seen.add(pair)
        signals.append({
            "product_a_id": str(r.p1_id),
            "product_a_name": r.p1_name,
            "product_b_id": str(r.p2_id),
            "product_b_name": r.p2_name,
            "co_purchases": r.co_purchases
        })
    return signals

def get_failed_payment_signals(db: Session, merchant_id: uuid.UUID) -> Dict[str, Any]:
    revenue = get_revenue_metrics(db, merchant_id)
    failed = revenue.get("failed_order_count", 0)
    total = revenue.get("order_count", 1) # prevent div/0
    return {
        "failed_orders": failed,
        "failed_rate_percent": round((failed / total) * 100, 2)
    }
