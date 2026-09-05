"""Centralized environment configuration.

All configuration is read from environment variables (optionally via a .env
file for local dev). Nothing here has a production secret baked in.
"""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+psycopg2://growthpilot:growthpilot@localhost:5432/growthpilot"
    redis_url: str = "redis://localhost:6379/0"

    razorpay_key_id: str | None = None
    razorpay_key_secret: str | None = None
    razorpay_webhook_secret: str | None = None
    demo_webhook_mode: bool = True

    llm_provider: str = "gemini"
    llm_api_key: str | None = None
    llm_model: str | None = None

    jwt_secret: str = "dev-only-change-me"
    jwt_expiry_minutes: int = 60

    discount_limit_percent: int = 20
    transaction_limit_inr: int = 100000

    api_base_url: str = "http://localhost:8000"
    frontend_base_url: str = "http://localhost:5173"


@lru_cache
def get_settings() -> Settings:
    return Settings()
