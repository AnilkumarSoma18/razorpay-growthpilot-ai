"""
Integration test for scripts/seed_database.py's core logic: given generator
output, rows land correctly in the DB with correct FKs and counts. This uses
a small scale (not the full 10,500-order production seed) so the test suite
stays fast; the full-scale run is exercised manually via
`python scripts/seed_database.py` and verified in docs/tasklist.md.
"""
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import func, select

from app.models.core import Customer, Merchant
from app.models.order import Order
from app.models.payment import Payment
from app.models.product import Product
from data.orders_and_events_generator import generate_orders_payments_and_carts
from data.synthetic_data_generator import (
    generate_categories,
    generate_customers,
    generate_products,
    link_product_affinity,
)


def test_seed_pipeline_small_scale_end_to_end(db_session):
    merchant = Merchant(
        id=uuid.uuid4(),
        name="Seed Pipeline Test Merchant",
        business_email=f"seedtest-{uuid.uuid4().hex[:8]}@example.test",
    )
    db_session.add(merchant)
    db_session.flush()

    categories = generate_categories()
    products = generate_products(categories, target_count=60)
    affinity = link_product_affinity(products)
    customers = generate_customers(count=80)

    product_rows = [
        Product(
            id=p.id, merchant_id=merchant.id, sku=p.sku, name=p.name,
            description=p.description, price=p.price, inventory=p.inventory,
            attributes=p.attributes, use_cases=p.use_cases,
            customer_segments=p.customer_segments, rating=p.rating,
        )
        for p in products
    ]
    db_session.bulk_save_objects(product_rows)

    customer_rows = [
        Customer(
            id=c.id, merchant_id=merchant.id, full_name=c.full_name, email=c.email,
            phone=c.phone, city=c.city, state=c.state, segment=c.segment,
            acquired_at=c.acquired_at,
        )
        for c in customers
    ]
    db_session.bulk_save_objects(customer_rows)
    db_session.flush()

    order_bundles, cart_events, _ = generate_orders_payments_and_carts(
        merchant_id=merchant.id, customers=customers, products=products,
        affinity=affinity, min_orders=120,
    )

    db_session.execute(Order.__table__.insert(), [b.order for b in order_bundles])
    db_session.execute(
        Payment.__table__.insert(), [b.payment for b in order_bundles]
    )
    db_session.commit()

    order_count = db_session.execute(
        select(func.count()).select_from(Order).where(Order.merchant_id == merchant.id)
    ).scalar_one()
    payment_count = db_session.execute(
        select(func.count()).select_from(Payment).where(Payment.merchant_id == merchant.id)
    ).scalar_one()
    product_count = db_session.execute(
        select(func.count()).select_from(Product).where(Product.merchant_id == merchant.id)
    ).scalar_one()

    assert order_count >= 120
    assert payment_count == order_count  # every order has exactly one payment
    assert product_count == len(products)
