
from app.agents.state import AgentState, Strategy
from sqlalchemy.orm import Session
from app.models.agent import AgentAction
import uuid
from datetime import datetime, timezone

def strategy_node(state: AgentState, db: Session) -> dict:
    action = AgentAction(
        id=uuid.uuid4(),
        agent_run_id=state["run_id"],
        step="STRATEGY_GENERATED",
        tool_name="strategy_engine",
        input_summary="Generating deterministic strategies",
        status="COMPLETED"
    )
    db.add(action)
    
    strategies = []
    for opp in state.get("opportunities", []):
        if opp["type"] == "CROSS_SELL":
            s = Strategy(
                strategy_id=uuid.uuid4(),
                opportunity_id=uuid.UUID(opp["id"]),
                strategy_type="BUNDLE_RECOMMENDATION",
                title=f"Bundle Strategy for {opp['title']}",
                summary="Recommend the associated target product after a customer interacts with the source product.",
                rationale="Deterministic fallback strategy based on observed strong co-purchase signal.",
                target="Customers interacting with the source product.",
                recommended_action="Present a dynamic bundle offer during checkout.",
                constraints=["Do not automatically change price", "Do not automatically activate discount", "Merchant approval required"],
                risk_level="LOW",
                approval_required=True,
                expected_effect="Observed historical co-purchases suggest baseline interest.",
                prediction_status="UNAVAILABLE",
                created_at=datetime.now(timezone.utc)
            )
            strategies.append(s.model_dump(mode='json'))
            
        elif opp["type"] == "FAILED_PAYMENT_RECOVERY":
            s = Strategy(
                strategy_id=uuid.uuid4(),
                opportunity_id=uuid.UUID(opp["id"]),
                strategy_type="RECOVERY_CAMPAIGN",
                title="Failed Payment Recovery Segment",
                summary="Create a merchant-reviewable recovery segment containing customers with failed payments.",
                rationale="Deterministic fallback strategy based on high failure rate.",
                target="Customers with failed order events in the past 7 days.",
                recommended_action="Send a targeted recovery email.",
                constraints=["Do not automatically retry payment", "Merchant approval required"],
                risk_level="LOW",
                approval_required=True,
                expected_effect="Provides a pathway to recover abandoned revenue.",
                prediction_status="UNAVAILABLE",
                created_at=datetime.now(timezone.utc)
            )
            strategies.append(s.model_dump(mode='json'))
            
    action.output_summary = f"Generated {len(strategies)} strategies"
    db.commit()
    
    return {"strategies": strategies, "agent_action_ids": [action.id]}
