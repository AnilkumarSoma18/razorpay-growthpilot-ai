#!/usr/bin/env python3
"""
scripts/seed_database.py

Seeds the database with SYNTHETIC DEMO DATA for local development and demos.

Usage:
    python scripts/seed_database.py            # seed if not already seeded
    python scripts/seed_database.py --reset     # wipe demo data and reseed

This script does not call Razorpay. Payment rows it creates are synthetic
*historical* records for analytics purposes (see data/synthetic_data_generator.py).
"""
from __future__ import annotations

import argparse
import sys
import time
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import delete, select  # noqa: E402

from app.database.session import SessionLocal, engine  # noqa: E402
from app.models.core import Customer, Merchant, ProductCategory  # noqa: E402
from app.models.product import Product  # noqa: E402
from app.models.order import Order, OrderItem  # noqa: E402
from app.models.payment import Payment, PaymentEvent  # noqa: E402
from app.models.events import CartEvent, CustomerEvent  # noqa: E402

from data.synthetic_data_generator import (  # noqa: E402
    generate_categories,
    generate_customers,
    generate_products,
    link_product_affinity,
)
from data.orders_and_events_generator import (  # noqa: E402
    generate_customer_events,
    generate_orders_payments_and_carts,
)

DEMO_MERCHANT_EMAIL = "growth@growthpilot-demo.test"


def wipe_demo_data(session) -> None:
    merchant = session.execute(
        select(Merchant).where(Merchant.business_email == DEMO_MERCHANT_EMAIL)
    ).scalar_one_or_none()
    if merchant is None:
        return
    print(f"Wiping existing demo data for merchant {merchant.id} ...")
    # Delete children first to satisfy FK constraints (no ON DELETE CASCADE
    # relied on here for clarity/safety in a destructive script).
    order_ids = [
        row[0]
        for row in session.execute(select(Order.id).where(Order.merchant_id == merchant.id))
    ]
    payment_ids = [
        row[0]
        for row in session.execute(select(Payment.id).where(Payment.merchant_id == merchant.id))
    ]
    if payment_ids:
        session.execute(delete(PaymentEvent).where(PaymentEvent.payment_id.in_(payment_ids)))
    session.execute(delete(Payment).where(Payment.merchant_id == merchant.id))
    if order_ids:
        session.execute(delete(OrderItem).where(OrderItem.order_id.in_(order_ids)))
    session.execute(delete(Order).where(Order.merchant_id == merchant.id))
    session.execute(delete(CartEvent).where(CartEvent.merchant_id == merchant.id))
    session.execute(delete(CustomerEvent).where(CustomerEvent.merchant_id == merchant.id))
    session.execute(delete(Product).where(Product.merchant_id == merchant.id))
    session.execute(delete(ProductCategory).where(ProductCategory.merchant_id == merchant.id))
    session.execute(delete(Customer).where(Customer.merchant_id == merchant.id))
    session.execute(delete(Merchant).where(Merchant.id == merchant.id))
    session.commit()
    print("Wipe complete.")


def seed(reset: bool = False) -> None:
    session = SessionLocal()
    t0 = time.time()
    try:
        existing = session.execute(
            select(Merchant).where(Merchant.business_email == DEMO_MERCHANT_EMAIL)
        ).scalar_one_or_none()

        if existing and reset:
            wipe_demo_data(session)
            existing = None

        if existing:
            print(
                f"Demo merchant already seeded (id={existing.id}). "
                "Re-run with --reset to wipe and regenerate."
            )
            _print_counts(session, existing.id)
            return

        print("=== Seeding SYNTHETIC DEMO DATA ===")

        # 1. Merchant
        merchant = Merchant(
            id=uuid.uuid4(),
            name="Nimbus Retail (Demo)",
            business_email=DEMO_MERCHANT_EMAIL,
            industry="Ecommerce - General Retail",
            country="IN",
            currency="INR",
            discount_limit_percent=20,
            transaction_limit_inr=100000,
            razorpay_key_id=None,
            is_demo_data=True,
        )
        session.add(merchant)
        session.flush()
        print(f"Merchant created: {merchant.id}")

        # 2. Categories
        raw_categories = generate_categories()
        name_to_id: dict[str, uuid.UUID] = {c["name"]: c["id"] for c in raw_categories}
        category_rows = [
            ProductCategory(
                id=c["id"],
                merchant_id=merchant.id,
                name=c["name"],
                parent_id=name_to_id.get(c["parent_name"]) if c["parent_name"] else None,
            )
            for c in raw_categories
        ]
        session.bulk_save_objects(category_rows)
        session.flush()
        print(f"Categories created: {len(category_rows)}")

        # 3. Products
        gen_products = generate_products(raw_categories, target_count=560)
        affinity = link_product_affinity(gen_products)
        product_rows = []
        for p in gen_products:
            related_ids = affinity.get(p.id, [])
            product_rows.append(
                Product(
                    id=p.id,
                    merchant_id=merchant.id,
                    category_id=name_to_id[p.category_name],
                    sku=p.sku,
                    name=p.name,
                    description=p.description,
                    price=p.price,
                    currency="INR",
                    inventory=p.inventory,
                    attributes=p.attributes,
                    use_cases=p.use_cases,
                    compatible_products=related_ids,
                    frequently_bought_with=related_ids,
                    customer_segments=p.customer_segments,
                    rating=p.rating,
                    is_active=True,
                )
            )
        session.bulk_save_objects(product_rows)
        session.flush()
        print(f"Products created: {len(product_rows)}")

        # 4. Customers
        gen_customers = generate_customers(count=2200)
        customer_rows = [
            Customer(
                id=c.id,
                merchant_id=merchant.id,
                external_ref=None,
                full_name=c.full_name,
                email=c.email,
                phone=c.phone,
                city=c.city,
                state=c.state,
                segment=c.segment,
                acquired_at=c.acquired_at,
            )
            for c in gen_customers
        ]
        session.bulk_save_objects(customer_rows)
        session.flush()
        print(f"Customers created: {len(customer_rows)}")

        # 5. Orders, order items, payments, payment events, cart events
        order_bundles, cart_event_dicts, _ = generate_orders_payments_and_carts(
            merchant_id=merchant.id,
            customers=gen_customers,
            products=gen_products,
            affinity=affinity,
            min_orders=10500,
        )

        order_dicts = [b.order for b in order_bundles]
        item_dicts = [item for b in order_bundles for item in b.items]
        payment_dicts = [b.payment for b in order_bundles]
        payment_event_dicts = [pe for b in order_bundles for pe in b.payment_events]

        _bulk_insert(session, Order, order_dicts)
        _bulk_insert(session, OrderItem, item_dicts)
        _bulk_insert(session, Payment, payment_dicts)
        if payment_event_dicts:
            _bulk_insert(session, PaymentEvent, payment_event_dicts)
        _bulk_insert(session, CartEvent, cart_event_dicts)

        print(f"Orders created: {len(order_dicts)}")
        print(f"Order items created: {len(item_dicts)}")
        print(f"Payments created: {len(payment_dicts)}")
        print(f"Payment events created: {len(payment_event_dicts)}")
        print(f"Cart events created: {len(cart_event_dicts)}")

        # 6. Customer behavioral events
        customer_event_dicts = generate_customer_events(merchant.id, gen_customers, gen_products)
        _bulk_insert(session, CustomerEvent, customer_event_dicts)
        print(f"Customer events created: {len(customer_event_dicts)}")

        session.commit()
        elapsed = time.time() - t0
        print(f"=== Seed complete in {elapsed:.1f}s ===")
        _print_counts(session, merchant.id)

    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _bulk_insert(session, model, dicts: list[dict], batch_size: int = 2000) -> None:
    if not dicts:
        return
    for i in range(0, len(dicts), batch_size):
        session.execute(model.__table__.insert(), dicts[i : i + batch_size])


def _print_counts(session, merchant_id) -> None:
    from sqlalchemy import func

    def count(model, *filters):
        q = select(func.count()).select_from(model)
        for f in filters:
            q = q.where(f)
        return session.execute(q).scalar_one()

    print("\n--- Row counts for demo merchant ---")
    print(f"Products:        {count(Product, Product.merchant_id == merchant_id)}")
    print(f"Customers:       {count(Customer, Customer.merchant_id == merchant_id)}")
    print(f"Orders:          {count(Order, Order.merchant_id == merchant_id)}")
    print(f"Payments:        {count(Payment, Payment.merchant_id == merchant_id)}")
    print(f"Cart events:     {count(CartEvent, CartEvent.merchant_id == merchant_id)}")
    print(f"Customer events: {count(CustomerEvent, CustomerEvent.merchant_id == merchant_id)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reset", action="store_true", help="Wipe existing demo data and reseed")
    args = parser.parse_args()
    seed(reset=args.reset)
