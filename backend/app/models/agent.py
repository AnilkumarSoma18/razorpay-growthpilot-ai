"""Agent execution records, approval gate, and audit trail.

These tables are the backbone of spec S17/S18/S19: nothing the agent does to
money or merchant configuration is allowed to happen without a row here.
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import AgentRunStatus, AgentType, ApprovalStatus, AuditActor


class AgentRun(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "agent_runs"

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    agent_type: Mapped[AgentType] = mapped_column(nullable=False)
    status: Mapped[AgentRunStatus] = mapped_column(
        default=AgentRunStatus.RUNNING, nullable=False
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    input_summary: Mapped[Optional[str]] = mapped_column(String(2000))
    output_summary: Mapped[Optional[str]] = mapped_column(String(2000))


class AgentAction(Base, UUIDPKMixin):
    __tablename__ = "agent_actions"

    agent_run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="CASCADE"), nullable=False
    )
    step: Mapped[str] = mapped_column(String(120), nullable=False)
    tool_name: Mapped[Optional[str]] = mapped_column(String(120))
    input_summary: Mapped[Optional[str]] = mapped_column(String(2000))
    output_summary: Mapped[Optional[str]] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class ApprovalRequest(Base, UUIDPKMixin):
    __tablename__ = "approval_requests"

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    opportunity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("growth_opportunities.id", ondelete="SET NULL")
    )
    agent_action_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_actions.id", ondelete="SET NULL")
    )
    action_description: Mapped[str] = mapped_column(String(1000), nullable=False)
    reason: Mapped[str] = mapped_column(String(2000), nullable=False)
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    expected_impact: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    risk: Mapped[str] = mapped_column(String(32), nullable=False)
    scope: Mapped[Optional[str]] = mapped_column(String(255))
    limit_amount: Mapped[Optional[float]] = mapped_column(Numeric(12, 2))
    status: Mapped[ApprovalStatus] = mapped_column(
        default=ApprovalStatus.PENDING, nullable=False
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    decided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    decided_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class AuditLog(Base, UUIDPKMixin):
    __tablename__ = "audit_logs"

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    agent_run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("agent_runs.id", ondelete="SET NULL")
    )
    actor: Mapped[AuditActor] = mapped_column(nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    tool_name: Mapped[Optional[str]] = mapped_column(String(120))
    input_summary: Mapped[Optional[str]] = mapped_column(String(2000))
    reason: Mapped[Optional[str]] = mapped_column(String(2000))
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 4))
    approval_status: Mapped[Optional[str]] = mapped_column(String(32))
    execution_status: Mapped[str] = mapped_column(String(32), nullable=False)
    error: Mapped[Optional[str]] = mapped_column(String(2000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
