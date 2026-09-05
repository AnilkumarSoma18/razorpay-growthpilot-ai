"""
Shared pytest fixtures.

Tests run against a dedicated PostgreSQL database (growthpilot_test), never
against the dev/demo database, so the test suite is safe to run repeatedly
without disturbing seeded demo data. DATABASE_URL is overridden *before*
any `app.*` module is imported so the app's engine is built against the
test database from the start.
"""
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(REPO_ROOT))

TEST_DATABASE_URL = "postgresql+psycopg2://growthpilot:growthpilot@localhost:5432/growthpilot_test"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import app.models  # noqa: E402  populates Base.metadata
from app.models.base import Base  # noqa: E402
from app.models.core import Customer, Merchant  # noqa: E402
from app.models.enums import (  # noqa: E402
    CartEventType,
    CustomerSegment,
    OrderSource,
    OrderStatus,
    PaymentStatus,
)
from app.models.events import CartEvent  # noqa: E402
from app.models.order import Order  # noqa: E402
from app.models.payment import Payment  # noqa: E402

test_engine = create_engine(TEST_DATABASE_URL, future=True)
TestSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def db_session():
    session = TestSessionLocal()
    try:
        yield session
        session.rollback()
    finally:
        session.close()


@pytest.fixture()
def client(db_session):
    """FastAPI TestClient with get_db overridden to use the test session."""
    from app.database.session import get_db
    from app.main import app as fastapi_app

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    fastapi_app.dependency_overrides[get_db] = _override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def seeded_merchant(db_session):
    """A small, hand-built dataset (not the full synthetic generator) with
    known, hand-computable analytics values, so tests assert against exact
    expected numbers rather than 'some positive number'."""
    merchant = Merchant(
        id=uuid.uuid4(),
        name="Test Merchant",
        business_email=f"test-{uuid.uuid4().hex[:8]}@example.test",
        country="IN",
        currency="INR",
        is_demo_data=True,
    )
    db_session.add(merchant)
    db_session.flush()

    now = datetime.now(timezone.utc)

    # Customer A: 2 paid orders -> "returning"
    cust_a = Customer(
        id=uuid.uuid4(), merchant_id=merchant.id, full_name="Customer A",
        email="a@example.test", segment=CustomerSegment.RETURNING,
        acquired_at=now - timedelta(days=100),
    )
    # Customer B: 1 paid order -> not returning
    cust_b = Customer(
        id=uuid.uuid4(), merchant_id=merchant.id, full_name="Customer B",
        email="b@example.test", segment=CustomerSegment.NEW,
        acquired_at=now - timedelta(days=10),
    )
    db_session.add_all([cust_a, cust_b])
    db_session.flush()

    orders_and_amounts = [
        (cust_a.id, OrderStatus.PAID, 1000.0),
        (cust_a.id, OrderStatus.PAID, 2000.0),
        (cust_b.id, OrderStatus.PAID, 500.0),
        (cust_b.id, OrderStatus.FAILED, 300.0),
    ]
    for customer_id, status, amount in orders_and_amounts:
        order = Order(
            id=uuid.uuid4(), merchant_id=merchant.id, customer_id=customer_id,
            status=status, subtotal=amount, discount_amount=0, total_amount=amount,
            currency="INR", source=OrderSource.WEB, placed_at=now,
        )
        db_session.add(order)
        db_session.flush()
        payment_status = PaymentStatus.CAPTURED if status == OrderStatus.PAID else PaymentStatus.FAILED
        db_session.add(Payment(
            id=uuid.uuid4(), order_id=order.id, merchant_id=merchant.id,
            status=payment_status, amount=amount, currency="INR", is_test_mode=True,
        ))

    # Cart events: 3 carts total, 2 converted, 1 abandoned -> 66.67% conversion
    for _ in range(2):
        cart_id = uuid.uuid4()
        db_session.add(CartEvent(
            id=uuid.uuid4(), merchant_id=merchant.id, customer_id=cust_a.id,
            cart_id=cart_id, event_type=CartEventType.CONVERTED, created_at=now,
        ))
    abandoned_cart_id = uuid.uuid4()
    db_session.add(CartEvent(
        id=uuid.uuid4(), merchant_id=merchant.id, customer_id=cust_b.id,
        cart_id=abandoned_cart_id, event_type=CartEventType.ABANDONED, created_at=now,
    ))

    db_session.commit()
    return merchant
