"""Import every model module here so Base.metadata is fully populated for
Alembic autogenerate and for Base.metadata.create_all() in tests."""
from app.models.base import Base  # noqa: F401

from app.models.core import Merchant, User, Customer, ProductCategory  # noqa: F401
from app.models.product import Product  # noqa: F401
from app.models.order import Order, OrderItem  # noqa: F401
from app.models.payment import Payment, PaymentEvent  # noqa: F401
from app.models.events import CartEvent, CustomerEvent, Recommendation  # noqa: F401
from app.models.growth import GrowthOpportunity, Campaign, CampaignEvent  # noqa: F401
from app.models.agent import AgentRun, AgentAction, ApprovalRequest, AuditLog  # noqa: F401
from app.models.experiment import Experiment, ExperimentEvent, ModelPrediction  # noqa: F401

__all__ = [
    "Base",
    "Merchant",
    "User",
    "Customer",
    "ProductCategory",
    "Product",
    "Order",
    "OrderItem",
    "Payment",
    "PaymentEvent",
    "CartEvent",
    "CustomerEvent",
    "Recommendation",
    "GrowthOpportunity",
    "Campaign",
    "CampaignEvent",
    "AgentRun",
    "AgentAction",
    "ApprovalRequest",
    "AuditLog",
    "Experiment",
    "ExperimentEvent",
    "ModelPrediction",
]
