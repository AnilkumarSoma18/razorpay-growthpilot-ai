"""Pydantic response schemas for the health and analytics endpoints."""
from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    app_env: str
    database: str
    timestamp: datetime


class RevenueMetrics(BaseModel):
    is_synthetic_demo_data: bool = Field(
        default=True,
        description="True whenever the underlying merchant is demo/synthetic data.",
    )
    total_revenue: float
    order_count: int
    paid_order_count: int
    failed_order_count: int
    refunded_order_count: int
    period_start: datetime | None = None
    period_end: datetime | None = None


class ConversionMetrics(BaseModel):
    is_synthetic_demo_data: bool = True
    converted_carts: int
    abandoned_carts: int
    total_carts: int
    conversion_rate_percent: float
    cart_abandonment_rate_percent: float


class AOVMetrics(BaseModel):
    is_synthetic_demo_data: bool = True
    average_order_value: float
    paid_order_count: int


class RetentionMetrics(BaseModel):
    is_synthetic_demo_data: bool = True
    total_customers: int
    returning_customers: int
    returning_customer_rate_percent: float


class DashboardSummary(BaseModel):
    is_synthetic_demo_data: bool = True
    revenue: RevenueMetrics
    conversion: ConversionMetrics
    aov: AOVMetrics
    retention: RetentionMetrics
