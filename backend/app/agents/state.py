
import uuid
from typing import TypedDict, Annotated, Sequence, Any, Optional
import operator
from pydantic import BaseModel, Field
from datetime import datetime

class Strategy(BaseModel):
    strategy_id: uuid.UUID
    opportunity_id: uuid.UUID
    strategy_type: str
    title: str
    summary: str
    rationale: str
    target: str
    recommended_action: str
    constraints: list[str]
    risk_level: str
    approval_required: bool
    expected_effect: str
    prediction_status: str
    created_at: datetime
    
class AgentState(TypedDict):
    merchant_id: uuid.UUID
    run_id: uuid.UUID
    
    # Trace tracking
    agent_action_ids: Annotated[list[uuid.UUID], operator.add]
    
    # Observe Node
    observed_metrics: dict
    product_signals: dict
    failed_payments: dict
    
    # Analyze Node
    analysis_summary: str
    
    # Opportunity Node
    opportunities: Annotated[list[dict], operator.add]
    
    # Strategy Node
    strategies: Annotated[list[dict], operator.add]
    
    # Global
    warnings: Annotated[list[str], operator.add]
    errors: Annotated[list[str], operator.add]
