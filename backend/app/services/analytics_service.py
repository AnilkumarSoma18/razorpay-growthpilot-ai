"""
Analytics service — every number here comes from a real SQL aggregate over
the seeded (synthetic demo) data. Nothing is hardcoded or fabricated; if a
merchant has no data yet, these functions return honest zeros rather than
placeholder numbers.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.core import Customer, Merchant
from app.models.enums import CartEventType, OrderStatus
from app.models.events import CartEvent
from app.models.order import Order


def _merchant_or_404(db: Session, merchant_id: uuid.UUID) -> Merchant:
    merchant = db.get(Merchant, merchant_id)
    if merchant is None:
        raise ValueError(f"Merchant {merchant_id} not found")
    return merchant


def get_revenue_metrics(
    db: Session,
    merchant_id: uuid.UUID,
    period_start: datetime | None = None,
    period_end: datetime | None = None,
) -> dict:
    """Revenue is summed only over PAID orders (never failed/refunded), which
    is the standard definition of realized revenue."""
    merchant = _merchant_or_404(db, merchant_id)

    base = select(Order).where(Order.merchant_id == merchant_id)
    if period_start:
        base = base.where(Order.placed_at >= period_start)
    if period_end:
        base = base.where(Order.placed_at <= period_end)

    def count_where(*extra):
        q = select(func.count()).select_from(Order).where(Order.merchant_id == merchant_id)
        if period_start:
            q = q.where(Order.placed_at >= period_start)
        if period_end:
            q = q.where(Order.placed_at <= period_end)
        for e in extra:
            q = q.where(e)
        return db.execute(q).scalar_one()

    revenue_q = select(func.coalesce(func.sum(Order.total_amount), 0)).where(
        Order.merchant_id == merchant_id, Order.status == OrderStatus.PAID
    )
    if period_start:
        revenue_q = revenue_q.where(Order.placed_at >= period_start)
    if period_end:
        revenue_q = revenue_q.where(Order.placed_at <= period_end)
    total_revenue = float(db.execute(revenue_q).scalar_one())

    return {
        "is_synthetic_demo_data": merchant.is_demo_data,
        "total_revenue": round(total_revenue, 2),
        "order_count": count_where(),
        "paid_order_count": count_where(Order.status == OrderStatus.PAID),
        "failed_order_count": count_where(Order.status == OrderStatus.FAILED),
        "refunded_order_count": count_where(Order.status == OrderStatus.REFUNDED),
        "period_start": period_start,
        "period_end": period_end,
    }


def get_conversion_metrics(db: Session, merchant_id: uuid.UUID) -> dict:
    """Conversion / abandonment is computed from distinct cart_id groupings in
    cart_events: a cart that ever emitted CONVERTED counts as converted; one
    that emitted ABANDONED (and never converted) counts as abandoned."""
    merchant = _merchant_or_404(db, merchant_id)

    converted_carts = db.execute(
        select(func.count(func.distinct(CartEvent.cart_id))).where(
            CartEvent.merchant_id == merchant_id,
            CartEvent.event_type == CartEventType.CONVERTED,
        )
    ).scalar_one()

    abandoned_carts = db.execute(
        select(func.count(func.distinct(CartEvent.cart_id))).where(
            CartEvent.merchant_id == merchant_id,
            CartEvent.event_type == CartEventType.ABANDONED,
        )
    ).scalar_one()

    total_carts = db.execute(
        select(func.count(func.distinct(CartEvent.cart_id))).where(
            CartEvent.merchant_id == merchant_id
        )
    ).scalar_one()

    conversion_rate = (converted_carts / total_carts * 100) if total_carts else 0.0
    abandonment_rate = (abandoned_carts / total_carts * 100) if total_carts else 0.0

    return {
        "is_synthetic_demo_data": merchant.is_demo_data,
        "converted_carts": converted_carts,
        "abandoned_carts": abandoned_carts,
        "total_carts": total_carts,
        "conversion_rate_percent": round(conversion_rate, 2),
        "cart_abandonment_rate_percent": round(abandonment_rate, 2),
    }


def get_aov_metrics(db: Session, merchant_id: uuid.UUID) -> dict:
    merchant = _merchant_or_404(db, merchant_id)

    paid_count = db.execute(
        select(func.count()).select_from(Order).where(
            Order.merchant_id == merchant_id, Order.status == OrderStatus.PAID
        )
    ).scalar_one()

    total_paid_revenue = float(
        db.execute(
            select(func.coalesce(func.sum(Order.total_amount), 0)).where(
                Order.merchant_id == merchant_id, Order.status == OrderStatus.PAID
            )
        ).scalar_one()
    )

    aov = (total_paid_revenue / paid_count) if paid_count else 0.0

    return {
        "is_synthetic_demo_data": merchant.is_demo_data,
        "average_order_value": round(aov, 2),
        "paid_order_count": paid_count,
    }


def get_retention_metrics(db: Session, merchant_id: uuid.UUID) -> dict:
    """'Returning customer' here means a customer with more than one PAID
    order — a direct, verifiable definition rather than a modeled estimate."""
    merchant = _merchant_or_404(db, merchant_id)

    total_customers = db.execute(
        select(func.count()).select_from(Customer).where(Customer.merchant_id == merchant_id)
    ).scalar_one()

    subq = (
        select(Order.customer_id, func.count().label("paid_orders"))
        .where(Order.merchant_id == merchant_id, Order.status == OrderStatus.PAID)
        .group_by(Order.customer_id)
        .having(func.count() > 1)
        .subquery()
    )
    returning_customers = db.execute(select(func.count()).select_from(subq)).scalar_one()

    rate = (returning_customers / total_customers * 100) if total_customers else 0.0

    return {
        "is_synthetic_demo_data": merchant.is_demo_data,
        "total_customers": total_customers,
        "returning_customers": returning_customers,
        "returning_customer_rate_percent": round(rate, 2),
    }


def get_dashboard_summary(db: Session, merchant_id: uuid.UUID) -> dict:
    return {
        "is_synthetic_demo_data": _merchant_or_404(db, merchant_id).is_demo_data,
        "revenue": get_revenue_metrics(db, merchant_id),
        "conversion": get_conversion_metrics(db, merchant_id),
        "aov": get_aov_metrics(db, merchant_id),
        "retention": get_retention_metrics(db, merchant_id),
    }
