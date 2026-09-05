"""FastAPI application entrypoint for Razorpay GrowthPilot AI (backend)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import analytics, health
from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Razorpay GrowthPilot AI",
    description=(
        "Merchant Growth Agent + AI Shopping Agent backend. "
        "P0 foundation slice: database, analytics. "
        "Agentic workflows, ML, and Razorpay integration land in later slices."
    ),
    version="0.1.0-p0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_base_url, "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import analytics, health, growth, approvals, execution, payments, shopping

app.include_router(health.router)
app.include_router(analytics.router)
app.include_router(growth.router)
app.include_router(approvals.router)
app.include_router(execution.router)
app.include_router(payments.router)
app.include_router(shopping.router)

@app.get("/", tags=["root"])
def root():
    return {
        "name": "Razorpay GrowthPilot AI",
        "status": "P0 foundation",
        "docs": "/docs",
    }
