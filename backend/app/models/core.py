"""Core entities: merchants, users, customers, product categories."""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPKMixin
from app.models.enums import CustomerSegment, UserRole


class Merchant(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "merchants"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    business_email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    industry: Mapped[Optional[str]] = mapped_column(String(120))
    country: Mapped[str] = mapped_column(String(2), default="IN", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)

    # Money-safety policy limits (spec S5 / S17) — enforced server-side, never
    # trusted from an LLM tool call.
    discount_limit_percent: Mapped[int] = mapped_column(default=20, nullable=False)
    transaction_limit_inr: Mapped[int] = mapped_column(default=100000, nullable=False)

    # Razorpay TEST MODE key id only (public identifier; secret lives in env,
    # never in the DB).
    razorpay_key_id: Mapped[Optional[str]] = mapped_column(String(64))

    is_demo_data: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    users: Mapped[list["User"]] = relationship(back_populates="merchant")
    customers: Mapped[list["Customer"]] = relationship(back_populates="merchant")


class User(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "users"

    merchant_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE")
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(default=UserRole.MERCHANT_OWNER, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    merchant: Mapped[Optional["Merchant"]] = relationship(back_populates="users")


class Customer(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "customers"

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    external_ref: Mapped[Optional[str]] = mapped_column(String(64))
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(32))
    city: Mapped[Optional[str]] = mapped_column(String(120))
    state: Mapped[Optional[str]] = mapped_column(String(120))
    segment: Mapped[CustomerSegment] = mapped_column(
        default=CustomerSegment.NEW, nullable=False
    )
    acquired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    merchant: Mapped["Merchant"] = relationship(back_populates="customers")


class ProductCategory(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "product_categories"

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_categories.id", ondelete="SET NULL")
    )
