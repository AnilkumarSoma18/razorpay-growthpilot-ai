"""Product catalog."""
import uuid
from typing import Optional

from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPKMixin


class Product(Base, UUIDPKMixin, TimestampMixin):
    __tablename__ = "products"

    merchant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False
    )
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("product_categories.id", ondelete="SET NULL")
    )
    sku: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(2000))
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    inventory: Mapped[int] = mapped_column(default=0, nullable=False)

    # AI-readable catalog fields (spec S12)
    attributes: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    use_cases: Mapped[list] = mapped_column(ARRAY(String), default=list, nullable=False)
    compatible_products: Mapped[list] = mapped_column(
        ARRAY(UUID(as_uuid=True)), default=list, nullable=False
    )
    frequently_bought_with: Mapped[list] = mapped_column(
        ARRAY(UUID(as_uuid=True)), default=list, nullable=False
    )
    customer_segments: Mapped[list] = mapped_column(ARRAY(String), default=list, nullable=False)

    rating: Mapped[float] = mapped_column(Numeric(2, 1), default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
