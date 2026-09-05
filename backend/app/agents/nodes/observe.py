
from sqlalchemy.orm import Session
from app.agents.state import AgentState
from app.models.agent import AgentAction
import uuid
from app.agents.tools.analytics_tools import (
    get_merchant_summary,
    get_top_products,
    get_failed_payment_signals,
    get_cross_sell_signals
)

def observe_node(state: AgentState, db: Session) -> dict:
    merchant_id = state["merchant_id"]
    action = AgentAction(
        id=uuid.uuid4(),
        agent_run_id=state["run_id"],
        step="OBSERVE_COMPLETED",
        tool_name="analytics_tools",
        input_summary="Collecting merchant analytical signals",
        status="COMPLETED"
    )
    db.add(action)
    
    summary = get_merchant_summary(db, merchant_id)
    top_products = get_top_products(db, merchant_id)
    failed_payments = get_failed_payment_signals(db, merchant_id)
    cross_sells = get_cross_sell_signals(db, merchant_id)
    
    action.output_summary = "Successfully extracted revenue, product, and failure signals."
    db.commit()
    
    return {
        "observed_metrics": summary,
        "product_signals": {"top_products": top_products, "cross_sell_pairs": cross_sells},
        "failed_payments": failed_payments,
        "agent_action_ids": [action.id]
    }
