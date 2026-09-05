"""
Analytics tests.

`seeded_merchant` (see tests/conftest.py) builds a small, fully-known dataset:
- Customer A: 2 PAID orders (1000, 2000) -> returning
- Customer B: 1 PAID order (500), 1 FAILED order (300) -> not returning
- Cart events: 2 CONVERTED carts, 1 ABANDONED cart

Expected, hand-computed values:
- total_revenue = 1000 + 2000 + 500 = 3500 (FAILED orders excluded)
- order_count = 4, paid_order_count = 3, failed_order_count = 1, refunded = 0
- converted_carts = 2, abandoned_carts = 1, total_carts = 3
  -> conversion_rate = 66.67%, abandonment_rate = 33.33%
- aov = 3500 / 3 = 1166.67
- total_customers = 2, returning_customers = 1 (only Customer A has >1 paid order)
  -> returning_customer_rate = 50.0%
"""
import uuid

from app.services import analytics_service


def test_revenue_metrics_service(db_session, seeded_merchant):
    result = analytics_service.get_revenue_metrics(db_session, seeded_merchant.id)
    assert result["total_revenue"] == 3500.0
    assert result["order_count"] == 4
    assert result["paid_order_count"] == 3
    assert result["failed_order_count"] == 1
    assert result["refunded_order_count"] == 0
    assert result["is_synthetic_demo_data"] is True


def test_conversion_metrics_service(db_session, seeded_merchant):
    result = analytics_service.get_conversion_metrics(db_session, seeded_merchant.id)
    assert result["converted_carts"] == 2
    assert result["abandoned_carts"] == 1
    assert result["total_carts"] == 3
    assert round(result["conversion_rate_percent"], 2) == 66.67
    assert round(result["cart_abandonment_rate_percent"], 2) == 33.33


def test_aov_metrics_service(db_session, seeded_merchant):
    result = analytics_service.get_aov_metrics(db_session, seeded_merchant.id)
    assert result["paid_order_count"] == 3
    assert round(result["average_order_value"], 2) == round(3500 / 3, 2)


def test_retention_metrics_service(db_session, seeded_merchant):
    result = analytics_service.get_retention_metrics(db_session, seeded_merchant.id)
    assert result["total_customers"] == 2
    assert result["returning_customers"] == 1
    assert result["returning_customer_rate_percent"] == 50.0


def test_revenue_metrics_unknown_merchant_raises(db_session):
    import pytest

    with pytest.raises(ValueError):
        analytics_service.get_revenue_metrics(db_session, uuid.uuid4())


# --- API-level tests (HTTP layer + schema) ---

def test_revenue_endpoint(client, seeded_merchant):
    resp = client.get(f"/api/analytics/revenue?merchant_id={seeded_merchant.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_revenue"] == 3500.0
    assert body["is_synthetic_demo_data"] is True


def test_dashboard_summary_endpoint(client, seeded_merchant):
    resp = client.get(f"/api/dashboard/summary?merchant_id={seeded_merchant.id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["revenue"]["total_revenue"] == 3500.0
    assert body["conversion"]["total_carts"] == 3
    assert body["aov"]["paid_order_count"] == 3
    assert body["retention"]["returning_customers"] == 1


def test_analytics_endpoint_404_for_unknown_merchant(client):
    resp = client.get(f"/api/analytics/revenue?merchant_id={uuid.uuid4()}")
    assert resp.status_code == 404


def test_analytics_endpoint_422_for_invalid_uuid(client):
    resp = client.get("/api/analytics/revenue?merchant_id=not-a-uuid")
    assert resp.status_code == 422
