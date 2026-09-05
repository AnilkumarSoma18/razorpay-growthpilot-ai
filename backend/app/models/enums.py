
"""Python enums backing PostgreSQL ENUM / constrained string columns."""
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MERCHANT_OWNER = "merchant_owner"
    STAFF = "staff"

class CustomerSegment(str, enum.Enum):
    NEW = "new"
    RETURNING = "returning"
    HIGH_VALUE = "high_value"
    PRICE_SENSITIVE = "price_sensitive"
    INACTIVE = "inactive"

class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"

class OrderSource(str, enum.Enum):
    WEB = "web"
    AI_SHOPPING_AGENT = "ai_shopping_agent"

class PaymentStatus(str, enum.Enum):
    CREATED = "created"
    PAYMENT_PENDING = "payment_pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    REFUNDED = "refunded"

class CartEventType(str, enum.Enum):
    ITEM_ADDED = "item_added"
    ITEM_REMOVED = "item_removed"
    CART_VIEWED = "cart_viewed"
    CHECKOUT_STARTED = "checkout_started"
    ABANDONED = "abandoned"
    CONVERTED = "converted"

class CustomerEventType(str, enum.Enum):
    PAGE_VIEW = "page_view"
    PRODUCT_VIEW = "product_view"
    SEARCH = "search"
    LOGIN = "login"
    SIGNUP = "signup"

class RecommendationType(str, enum.Enum):
    CROSS_SELL = "cross_sell"
    UPSELL = "upsell"
    SIMILAR = "similar"
    TRENDING = "trending"

class RecommendationSource(str, enum.Enum):
    ITEM_ITEM_CF = "item_item_cf"
    CONTENT_BASED = "content_based"
    CO_PURCHASE = "co_purchase"

class OpportunityType(str, enum.Enum):
    CROSS_SELL = "cross_sell"
    UPSELL = "upsell"
    BUNDLE = "bundle"
    CART_RECOVERY = "cart_recovery"
    REPEAT_PURCHASE = "repeat_purchase"
    RETENTION = "retention"
    FAILED_PAYMENT = "failed_payment"
    LOW_CONVERSION = "low_conversion"
    HIGH_VALUE_CUSTOMER = "high_value_customer"

class OpportunityRisk(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class OpportunityStatus(str, enum.Enum):
    NEW = "new"
    SIMULATED = "simulated"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTED = "executed"
    EXPIRED = "expired"

class AgentType(str, enum.Enum):
    MERCHANT_GROWTH = "merchant_growth"
    SHOPPING = "shopping"

class AgentRunStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class AuditActor(str, enum.Enum):
    SYSTEM = "system"
    AGENT = "agent"
    USER = "user"

class ExperimentStatus(str, enum.Enum):
    DRAFT = "draft"
    RUNNING = "running"
    COMPLETED = "completed"

class ExperimentVariant(str, enum.Enum):
    CONTROL = "control"
    VARIANT = "variant"

class ExperimentEventType(str, enum.Enum):
    IMPRESSION = "impression"
    CLICK = "click"
    ORDER = "order"
