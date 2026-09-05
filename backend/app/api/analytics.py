"""
Analytics API — thin routers over app/services/analytics_service.py.

No business logic lives here; every response is built from a real DB query.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.analytics import (
    AOVMetrics,
    ConversionMetrics,
    DashboardSummary,
    RetentionMetrics,
    RevenueMetrics,
)
from app.services import analytics_service

router = APIRouter(prefix="/api", tags=["analytics"])


def _handle(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/analytics/revenue", response_model=RevenueMetrics)
def revenue(
    merchant_id: uuid.UUID = Query(..., description="Merchant UUID"),
    db: Session = Depends(get_db),
):
    return _handle(analytics_service.get_revenue_metrics, db, merchant_id)


@router.get("/analytics/conversion", response_model=ConversionMetrics)
def conversion(
    merchant_id: uuid.UUID = Query(..., description="Merchant UUID"),
    db: Session = Depends(get_db),
):
    return _handle(analytics_service.get_conversion_metrics, db, merchant_id)


@router.get("/analytics/aov", response_model=AOVMetrics)
def aov(
    merchant_id: uuid.UUID = Query(..., description="Merchant UUID"),
    db: Session = Depends(get_db),
):
    return _handle(analytics_service.get_aov_metrics, db, merchant_id)


@router.get("/analytics/retention", response_model=RetentionMetrics)
def retention(
    merchant_id: uuid.UUID = Query(..., description="Merchant UUID"),
    db: Session = Depends(get_db),
):
    return _handle(analytics_service.get_retention_metrics, db, merchant_id)


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary(
    merchant_id: uuid.UUID = Query(..., description="Merchant UUID"),
    db: Session = Depends(get_db),
):
    return _handle(analytics_service.get_dashboard_summary, db, merchant_id)
