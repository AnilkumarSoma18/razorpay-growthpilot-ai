"""Health check endpoint — verifies the app is up and the DB is reachable."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.session import get_db
from app.schemas.analytics import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    settings = get_settings()
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as exc:  # pragma: no cover - defensive
        db_status = f"error: {exc}"

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        app_env=settings.app_env,
        database=db_status,
        timestamp=datetime.now(timezone.utc),
    )
