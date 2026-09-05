"""
Order, payment, cart-event, and customer-event generation.

Continues from synthetic_data_generator.py (categories, products, customers).
All data here is SYNTHETIC DEMO DATA — see module docstring in
synthetic_data_generator.py for the full disclaimer.
"""
from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

import numpy as np

from app.models.enums import (
    CartEventType,
    CustomerEventType,
    CustomerSegment,
    OrderSource,
    OrderStatus,
    PaymentStatus,
)
from data.synthetic_data_generator import GeneratedCustomer, GeneratedProduct, NOW

# Segment-driven purchase behavior. These multipliers/probabilities directly
# drive order volume and payment outcomes per customer segment so that the
# resulting analytics (conversion, AOV, cart abandonment, retention) are
# internally consistent rather than randomly noisy.
SEGMENT_ORDER_COUNT_RANGE = {
    CustomerSegment.NEW: (0, 2),
    CustomerSegment.RETURNING: (2, 8),
    CustomerSegment.HIGH_VALUE: (5, 15),
    CustomerSegment.PRICE_SENSITIVE: (1, 5),
    CustomerSegment.INACTIVE: (0, 1),
}

SEGMENT_AOV_MULTIPLIER = {
    CustomerSegment.NEW: 1.0,
    CustomerSegment.RETURNING: 1.1,
    CustomerSegment.HIGH_VALUE: 2.2,
    CustomerSegment.PRICE_SENSITIVE: 0.6,
    CustomerSegment.INACTIVE: 0.9,
}

PAYMENT_FAILURE_RATE = 0.06
REFUND_RATE = 0.03


@dataclass
class GeneratedOrderBundle:
    order: dict
    items: list[dict]
    payment: dict
    payment_events: list[dict]


def _weighted_category_products(products: list[GeneratedProduct]) -> dict[str, list[GeneratedProduct]]:
    by_cat: dict[str, list[GeneratedProduct]] = {}
    for p in products:
        by_cat.setdefault(p.category_name, []).append(p)
    return by_cat


def _pick_cart(
    products: list[GeneratedProduct],
    affinity: dict[uuid.UUID, list[uuid.UUID]],
    products_by_id: dict[uuid.UUID, GeneratedProduct],
) -> list[GeneratedProduct]:
    """Pick 1-4 products for a cart, biased toward realistic bundles: if an
    anchor product (one with affinity entries) is chosen, frequently also
    include one of its related products."""
    anchor = random.choice(products)
    cart = [anchor]
    if anchor.id in affinity and random.random() < 0.55:
        related_id = random.choice(affinity[anchor.id])
        related = products_by_id.get(related_id)
        if related:
            cart.append(related)
    if random.random() < 0.2:
        cart.append(random.choice(products))
    # de-dup
    seen = set()
    deduped = []
    for p in cart:
        if p.id not in seen:
            deduped.append(p)
            seen.add(p.id)
    return deduped


def generate_orders_payments_and_carts(
    merchant_id: uuid.UUID,
    customers: list[GeneratedCustomer],
    products: list[GeneratedProduct],
    affinity: dict[uuid.UUID, list[uuid.UUID]],
    min_orders: int = 10500,
) -> tuple[list[GeneratedOrderBundle], list[dict], list[dict]]:
    """
    Returns (order_bundles, cart_events, extra_abandoned_cart_events).

    Every *converted* cart (one that resulted in an order) also emits a
    matching cart_events sequence ending in CONVERTED, so cart_events and
    orders are consistent with each other rather than independently random.
    Additional carts are generated with no matching order, ending in
    ABANDONED, to produce a realistic cart-abandonment rate.
    """
    products_by_id = {p.id: p for p in products}
    order_bundles: list[GeneratedOrderBundle] = []
    cart_events: list[dict] = []

    total_orders_target = max(min_orders, len(customers) * 3)

    for customer in customers:
        low, high = SEGMENT_ORDER_COUNT_RANGE[customer.segment]
        n_orders = random.randint(low, high)
        for _ in range(n_orders):
            cart_products = _pick_cart(products, affinity, products_by_id)
            cart_id = uuid.uuid4()

            days_ago = random.randint(0, 365)
            placed_at = NOW - timedelta(days=days_ago, hours=random.randint(0, 23))

            # cart lifecycle events leading to conversion
            cart_events.append(_cart_event(merchant_id, customer.id, cart_id, CartEventType.ITEM_ADDED, cart_products[0].id, placed_at - timedelta(minutes=12)))
            for extra in cart_products[1:]:
                cart_events.append(_cart_event(merchant_id, customer.id, cart_id, CartEventType.ITEM_ADDED, extra.id, placed_at - timedelta(minutes=8)))
            cart_events.append(_cart_event(merchant_id, customer.id, cart_id, CartEventType.CART_VIEWED, None, placed_at - timedelta(minutes=5)))
            cart_events.append(_cart_event(merchant_id, customer.id, cart_id, CartEventType.CHECKOUT_STARTED, None, placed_at - timedelta(minutes=2)))
            cart_events.append(_cart_event(merchant_id, customer.id, cart_id, CartEventType.CONVERTED, None, placed_at))

            subtotal = sum(p.price for p in cart_products)
            aov_mult = SEGMENT_AOV_MULTIPLIER[customer.segment]
            discount_amount = 0.0
            if random.random() < 0.15:
                discount_amount = round(subtotal * random.uniform(0.05, 0.15), 2)
            total_amount = round(max(subtotal * aov_mult - discount_amount, subtotal * 0.5), 2)

            order_id = uuid.uuid4()
            is_failed = random.random() < PAYMENT_FAILURE_RATE
            is_refunded = (not is_failed) and random.random() < REFUND_RATE

            if is_failed:
                order_status = OrderStatus.FAILED
                payment_status = PaymentStatus.FAILED
            elif is_refunded:
                order_status = OrderStatus.REFUNDED
                payment_status = PaymentStatus.REFUNDED
            else:
                order_status = OrderStatus.PAID
                payment_status = PaymentStatus.CAPTURED

            order = {
                "id": order_id,
                "merchant_id": merchant_id,
                "customer_id": customer.id,
                "status": order_status,
                "subtotal": round(subtotal, 2),
                "discount_amount": discount_amount,
                "total_amount": total_amount,
                "currency": "INR",
                "source": OrderSource.WEB,
                "placed_at": placed_at,
            }

            items = []
            for p in cart_products:
                qty = random.randint(1, 2)
                items.append({
                    "id": uuid.uuid4(),
                    "order_id": order_id,
                    "product_id": p.id,
                    "quantity": qty,
                    "unit_price": p.price,
                    "total_price": round(p.price * qty, 2),
                })

            payment_id = uuid.uuid4()
            payment = {
                "id": payment_id,
                "order_id": order_id,
                "merchant_id": merchant_id,
                # Synthetic historical identifiers — NOT real Razorpay ids,
                # deliberately not shaped like `order_...`/`pay_...` so they
                # can never be confused with a live Razorpay reference.
                "razorpay_order_id": f"sim_hist_order_{uuid.uuid4().hex[:12]}",
                "razorpay_payment_id": f"sim_hist_pay_{uuid.uuid4().hex[:12]}" if not is_failed else None,
                "status": payment_status,
                "amount": total_amount,
                "currency": "INR",
                "method": random.choice(["card", "upi", "netbanking", "wallet"]),
                "is_test_mode": True,
                "verified_at": placed_at + timedelta(minutes=1) if not is_failed else None,
            }

            payment_events = []
            if is_failed:
                payment_events.append({
                    "id": uuid.uuid4(),
                    "payment_id": payment_id,
                    "event_type": "payment.failed",
                    "raw_payload": {"reason": random.choice(["insufficient_funds", "card_declined", "timeout"]), "synthetic": True},
                    "is_simulated": True,
                })
            if is_refunded:
                payment_events.append({
                    "id": uuid.uuid4(),
                    "payment_id": payment_id,
                    "event_type": "payment.refunded",
                    "raw_payload": {"reason": random.choice(["customer_request", "quality_issue"]), "synthetic": True},
                    "is_simulated": True,
                })

            order_bundles.append(GeneratedOrderBundle(order=order, items=items, payment=payment, payment_events=payment_events))

    # Top up with extra orders from randomly chosen (non-inactive) customers
    # until we hit the target volume — segment-driven per-customer counts
    # above intentionally don't guarantee reaching 10,000+ on their own.
    toppable_customers = [c for c in customers if c.segment != CustomerSegment.INACTIVE]
    while len(order_bundles) < total_orders_target:
        customer = random.choice(toppable_customers)
        cart_products = _pick_cart(products, affinity, products_by_id)
        cart_id = uuid.uuid4()

        days_ago = random.randint(0, 365)
        placed_at = NOW - timedelta(days=days_ago, hours=random.randint(0, 23))

        cart_events.append(_cart_event(merchant_id, customer.id, cart_id, CartEventType.ITEM_ADDED, cart_products[0].id, placed_at - timedelta(minutes=12)))
        for extra in cart_products[1:]:
            cart_events.append(_cart_event(merchant_id, customer.id, cart_id, CartEventType.ITEM_ADDED, extra.id, placed_at - timedelta(minutes=8)))
        cart_events.append(_cart_event(merchant_id, customer.id, cart_id, CartEventType.CART_VIEWED, None, placed_at - timedelta(minutes=5)))
        cart_events.append(_cart_event(merchant_id, customer.id, cart_id, CartEventType.CHECKOUT_STARTED, None, placed_at - timedelta(minutes=2)))
        cart_events.append(_cart_event(merchant_id, customer.id, cart_id, CartEventType.CONVERTED, None, placed_at))

        subtotal = sum(p.price for p in cart_products)
        aov_mult = SEGMENT_AOV_MULTIPLIER[customer.segment]
        discount_amount = round(subtotal * random.uniform(0.05, 0.15), 2) if random.random() < 0.15 else 0.0
        total_amount = round(max(subtotal * aov_mult - discount_amount, subtotal * 0.5), 2)

        order_id = uuid.uuid4()
        is_failed = random.random() < PAYMENT_FAILURE_RATE
        is_refunded = (not is_failed) and random.random() < REFUND_RATE
        if is_failed:
            order_status, payment_status = OrderStatus.FAILED, PaymentStatus.FAILED
        elif is_refunded:
            order_status, payment_status = OrderStatus.REFUNDED, PaymentStatus.REFUNDED
        else:
            order_status, payment_status = OrderStatus.PAID, PaymentStatus.CAPTURED

        order = {
            "id": order_id, "merchant_id": merchant_id, "customer_id": customer.id,
            "status": order_status, "subtotal": round(subtotal, 2),
            "discount_amount": discount_amount, "total_amount": total_amount,
            "currency": "INR", "source": OrderSource.WEB, "placed_at": placed_at,
        }
        items = []
        for p in cart_products:
            qty = random.randint(1, 2)
            items.append({
                "id": uuid.uuid4(), "order_id": order_id, "product_id": p.id,
                "quantity": qty, "unit_price": p.price, "total_price": round(p.price * qty, 2),
            })
        payment_id = uuid.uuid4()
        payment = {
            "id": payment_id, "order_id": order_id, "merchant_id": merchant_id,
            "razorpay_order_id": f"sim_hist_order_{uuid.uuid4().hex[:12]}",
            "razorpay_payment_id": f"sim_hist_pay_{uuid.uuid4().hex[:12]}" if not is_failed else None,
            "status": payment_status, "amount": total_amount, "currency": "INR",
            "method": random.choice(["card", "upi", "netbanking", "wallet"]),
            "is_test_mode": True,
            "verified_at": placed_at + timedelta(minutes=1) if not is_failed else None,
        }
        payment_events = []
        if is_failed:
            payment_events.append({
                "id": uuid.uuid4(), "payment_id": payment_id, "event_type": "payment.failed",
                "raw_payload": {"reason": random.choice(["insufficient_funds", "card_declined", "timeout"]), "synthetic": True},
                "is_simulated": True,
            })
        if is_refunded:
            payment_events.append({
                "id": uuid.uuid4(), "payment_id": payment_id, "event_type": "payment.refunded",
                "raw_payload": {"reason": random.choice(["customer_request", "quality_issue"]), "synthetic": True},
                "is_simulated": True,
            })
        order_bundles.append(GeneratedOrderBundle(order=order, items=items, payment=payment, payment_events=payment_events))

    # Additional abandoned-only carts (no order) for a realistic abandonment rate.
    n_abandoned = int(len(order_bundles) * 0.35)
    active_customers = [c for c in customers if c.segment != CustomerSegment.INACTIVE]
    for _ in range(n_abandoned):
        customer = random.choice(active_customers)
        cart_products = _pick_cart(products, affinity, products_by_id)
        cart_id = uuid.uuid4()
        days_ago = random.randint(0, 365)
        ts = NOW - timedelta(days=days_ago, hours=random.randint(0, 23))
        cart_events.append(_cart_event(merchant_id, customer.id, cart_id, CartEventType.ITEM_ADDED, cart_products[0].id, ts - timedelta(minutes=10)))
        cart_events.append(_cart_event(merchant_id, customer.id, cart_id, CartEventType.CART_VIEWED, None, ts - timedelta(minutes=6)))
        if random.random() < 0.4:
            cart_events.append(_cart_event(merchant_id, customer.id, cart_id, CartEventType.CHECKOUT_STARTED, None, ts - timedelta(minutes=3)))
        cart_events.append(_cart_event(merchant_id, customer.id, cart_id, CartEventType.ABANDONED, None, ts))

    return order_bundles, cart_events, []


def _cart_event(merchant_id, customer_id, cart_id, event_type: CartEventType, product_id, created_at) -> dict:
    return {
        "id": uuid.uuid4(),
        "merchant_id": merchant_id,
        "customer_id": customer_id,
        "cart_id": cart_id,
        "event_type": event_type,
        "product_id": product_id,
        "event_metadata": {"synthetic": True},
        "created_at": created_at,
    }


CUSTOMER_EVENT_WEIGHTS = {
    CustomerEventType.PAGE_VIEW: 0.35,
    CustomerEventType.PRODUCT_VIEW: 0.35,
    CustomerEventType.SEARCH: 0.20,
    CustomerEventType.LOGIN: 0.07,
    CustomerEventType.SIGNUP: 0.03,
}


def generate_customer_events(
    merchant_id: uuid.UUID,
    customers: list[GeneratedCustomer],
    products: list[GeneratedProduct],
    events_per_customer_range: tuple[int, int] = (2, 12),
) -> list[dict]:
    types = list(CUSTOMER_EVENT_WEIGHTS.keys())
    weights = list(CUSTOMER_EVENT_WEIGHTS.values())
    events = []
    for customer in customers:
        n = random.randint(*events_per_customer_range)
        for _ in range(n):
            event_type = random.choices(types, weights=weights, k=1)[0]
            days_ago = random.randint(0, 365)
            metadata = {"synthetic": True}
            if event_type == CustomerEventType.PRODUCT_VIEW:
                metadata["product_id"] = str(random.choice(products).id)
            elif event_type == CustomerEventType.SEARCH:
                metadata["query"] = random.choice([
                    "wireless headphones", "laptop bag", "running shoes",
                    "kitchen appliance", "camera tripod", "office chair",
                ])
            events.append({
                "id": uuid.uuid4(),
                "merchant_id": merchant_id,
                "customer_id": customer.id,
                "event_type": event_type,
                "event_metadata": metadata,
                "created_at": NOW - timedelta(days=days_ago, hours=random.randint(0, 23)),
            })
    return events
