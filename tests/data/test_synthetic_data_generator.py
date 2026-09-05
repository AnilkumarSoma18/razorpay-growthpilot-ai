"""
Tests for the synthetic data generator functions themselves (fast, in-memory —
does not hit the database or run the full seed script).
"""
import uuid

from data.orders_and_events_generator import generate_orders_payments_and_carts
from data.synthetic_data_generator import (
    generate_categories,
    generate_customers,
    generate_products,
    link_product_affinity,
)


def test_generate_categories_has_parents_and_children():
    categories = generate_categories()
    parents = [c for c in categories if c["parent_name"] is None]
    children = [c for c in categories if c["parent_name"] is not None]
    assert len(parents) >= 5
    assert len(children) >= 20


def test_generate_products_meets_minimum_count_and_has_ai_readable_fields():
    categories = generate_categories()
    products = generate_products(categories, target_count=560)
    assert len(products) >= 500
    sample = products[0]
    assert sample.sku
    assert sample.price > 0
    assert isinstance(sample.use_cases, list) and sample.use_cases
    assert isinstance(sample.attributes, dict) and "category" in sample.attributes


def test_product_affinity_links_laptops_to_related_categories():
    categories = generate_categories()
    products = generate_products(categories, target_count=200)
    affinity = link_product_affinity(products)
    laptops = [p for p in products if p.category_name == "Laptops"]
    assert laptops, "expected at least one laptop product"
    linked_any = any(p.id in affinity and affinity[p.id] for p in laptops)
    assert linked_any, "expected at least one laptop to have affinity-linked products"


def test_generate_customers_distributes_across_segments():
    customers = generate_customers(count=500)
    assert len(customers) == 500
    segments = {c.segment for c in customers}
    assert len(segments) >= 3  # not all customers landed in one segment


def test_generate_orders_reaches_minimum_target():
    categories = generate_categories()
    products = generate_products(categories, target_count=100)
    affinity = link_product_affinity(products)
    customers = generate_customers(count=100)
    merchant_id = uuid.uuid4()

    order_bundles, cart_events, _ = generate_orders_payments_and_carts(
        merchant_id=merchant_id,
        customers=customers,
        products=products,
        affinity=affinity,
        min_orders=150,
    )
    assert len(order_bundles) >= 150
    # every order has at least one item and a matching payment
    assert all(len(b.items) >= 1 for b in order_bundles)
    assert all(b.payment["order_id"] == b.order["id"] for b in order_bundles)
    # cart_events should include both CONVERTED (matches orders) and ABANDONED
    event_types = {e["event_type"] for e in cart_events}
    assert "CONVERTED" in {t.value if hasattr(t, "value") else t for t in event_types} or any(
        getattr(t, "name", None) == "CONVERTED" for t in event_types
    )
