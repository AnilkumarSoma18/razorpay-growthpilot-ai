"""Tests for the ORM layer: tables exist, constraints hold, relationships work."""
import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import inspect

from app.models.base import Base
from app.models.core import Customer, Merchant
from app.models.enums import CustomerSegment
from app.models.product import Product


EXPECTED_TABLES = {
    "merchants", "users", "customers", "product_categories", "products",
    "orders", "order_items", "payments", "payment_events", "cart_events",
    "customer_events", "recommendations", "growth_opportunities", "campaigns",
    "campaign_events", "agent_runs", "agent_actions", "approval_requests",
    "audit_logs", "experiments", "experiment_events", "model_predictions",
}


def test_all_expected_tables_exist_in_metadata():
    """Guards against a model being written but never imported into
    app/models/__init__.py (which would silently drop it from migrations)."""
    table_names = set(Base.metadata.tables.keys())
    missing = EXPECTED_TABLES - table_names
    assert not missing, f"Tables missing from Base.metadata: {missing}"


def test_all_expected_tables_exist_in_test_database(db_session):
    inspector = inspect(db_session.get_bind())
    db_tables = set(inspector.get_table_names())
    missing = EXPECTED_TABLES - db_tables
    assert not missing, f"Tables missing from actual database: {missing}"


def test_create_and_query_merchant(db_session):
    merchant = Merchant(
        id=uuid.uuid4(),
        name="Unit Test Merchant",
        business_email=f"unit-{uuid.uuid4().hex[:8]}@example.test",
        country="IN",
        currency="INR",
    )
    db_session.add(merchant)
    db_session.commit()

    fetched = db_session.get(Merchant, merchant.id)
    assert fetched is not None
    assert fetched.name == "Unit Test Merchant"
    assert fetched.is_demo_data is True  # default
    assert fetched.discount_limit_percent == 20  # default policy limit


def test_customer_requires_merchant_fk(db_session):
    """A customer without a valid merchant_id must fail — this is the
    guardrail that keeps analytics scoped correctly per merchant."""
    from sqlalchemy.exc import IntegrityError

    orphan = Customer(
        id=uuid.uuid4(),
        merchant_id=uuid.uuid4(),  # does not exist
        full_name="Ghost Customer",
        email="ghost@example.test",
        segment=CustomerSegment.NEW,
        acquired_at=datetime.now(timezone.utc),
    )
    db_session.add(orphan)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_product_unique_sku_enforced(db_session):
    from sqlalchemy.exc import IntegrityError

    merchant = Merchant(
        id=uuid.uuid4(), name="M", business_email=f"m-{uuid.uuid4().hex[:8]}@example.test",
    )
    db_session.add(merchant)
    db_session.flush()

    sku = f"SKU-{uuid.uuid4().hex[:8]}"
    p1 = Product(id=uuid.uuid4(), merchant_id=merchant.id, sku=sku, name="P1", price=100)
    db_session.add(p1)
    db_session.commit()

    p2 = Product(id=uuid.uuid4(), merchant_id=merchant.id, sku=sku, name="P2", price=200)
    db_session.add(p2)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
