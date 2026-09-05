"""Growth opportunity engine output and campaign execution records."""
import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from sqlalchemy import DateTime, func

from app.models.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import OpportunityRisk, OpportunityStatus, OpportunityType
from datetime import datetime


class GrowthOpportunity(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "growth_opportunities"

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    type: Mapped[OpportunityType] = mapped_column(nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric(5, 4), nullable=False)
    expected_revenue: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    expected_profit: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    risk: Mapped[OpportunityRisk] = mapped_column(default=OpportunityRisk.LOW, nullable=False)
    priority: Mapped[int] = mapped_column(default=0, nullable=False)
    score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    recommended_action: Mapped[str] = mapped_column(String(1000), nullable=False)
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[OpportunityStatus] = mapped_column(
        default=OpportunityStatus.NEW, nullable=False
    )


class Campaign(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "campaigns"

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    opportunity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("growth_opportunities.id", ondelete="SET NULL")
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="draft", nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)


class CampaignEvent(Base, UUIDPKMixin):
    __tablename__ = "campaign_events"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False
    )
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    event_metadata: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
