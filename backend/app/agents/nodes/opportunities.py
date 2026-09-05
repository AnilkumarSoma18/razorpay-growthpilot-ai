
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.agents.state import AgentState
import uuid
from app.models.growth import GrowthOpportunity
from app.models.enums import OpportunityType, OpportunityRisk
from app.models.agent import AgentAction
import json

def calculate_normalized_score(evidence_strength: float, population: float, business_value: float, confidence: float, risk_penalty: float) -> dict:
    final_score = (
        (evidence_strength * 0.4) +
        (population * 0.2) +
        (business_value * 0.2) +
        (confidence * 0.2)
    ) - risk_penalty
    
    final_score = max(0.0, min(100.0, final_score))
    
    return {
        "evidence_strength": round(evidence_strength, 2),
        "population_relevance": round(population, 2),
        "business_value_signal": round(business_value, 2),
        "confidence": round(confidence, 2),
        "risk_penalty": round(risk_penalty, 2),
        "final_score": round(final_score, 2)
    }

def deduplicate_opportunity(db: Session, merchant_id: uuid.UUID, title: str) -> GrowthOpportunity | None:
    # Basic deduplication: look for an existing opportunity with the exact same title for this merchant
    stmt = select(GrowthOpportunity).where(
        GrowthOpportunity.merchant_id == merchant_id,
        GrowthOpportunity.title == title
    ).order_by(GrowthOpportunity.created_at.desc()).limit(1)
    existing = db.execute(stmt).scalar_one_or_none()
    return existing

def generate_opportunities_node(state: AgentState, db: Session) -> dict:
    merchant_id = state["merchant_id"]
    new_opportunities = []
    
    action = AgentAction(
        id=uuid.uuid4(),
        agent_run_id=state["run_id"],
        step="OPPORTUNITY_DETECTED",
        tool_name="opportunity_engine",
        input_summary="Analyzing observed signals",
        status="COMPLETED"
    )
    db.add(action)
    
    # 1. CROSS_SELL
    cross_sells = state.get("product_signals", {}).get("cross_sell_pairs", [])
    for pair in cross_sells[:2]: 
        title = f"Bundle {pair['product_a_name']} with {pair['product_b_name']}"
        existing = deduplicate_opportunity(db, merchant_id, title)
        
        evidence_strength = min(100.0, pair["co_purchases"] * 5)
        population = 50.0 
        business_value = 75.0 
        confidence = 80.0
        risk_penalty = 5.0
        
        score_components = calculate_normalized_score(evidence_strength, population, business_value, confidence, risk_penalty)
        
        evidence = {
            "source_product_id": pair["product_a_id"],
            "source_product_name": pair["product_a_name"],
            "target_product_id": pair["product_b_id"],
            "target_product_name": pair["product_b_name"],
            "co_purchase_count": pair["co_purchases"],
            "signal": "Strong product association",
            "score_components": score_components,
            "impact_estimate_status": "UNAVAILABLE"
        }
        
        if existing:
            # Update existing
            existing.evidence = evidence
            existing.score = score_components["final_score"]
            new_opportunities.append(existing)
        else:
            opp = GrowthOpportunity(
                id=uuid.uuid4(),
                merchant_id=merchant_id,
                type=OpportunityType.CROSS_SELL,
                title=title,
                description=f"Observed behavior: Customers frequently buy {pair['product_a_name']} and {pair['product_b_name']} together.",
                evidence=evidence,
                confidence=0.8,
                expected_revenue=0.0, 
                expected_profit=0.0,
                risk=OpportunityRisk.LOW,
                priority=int(score_components["final_score"]),
                score=score_components["final_score"],
                recommended_action="Create a product bundle.",
                requires_approval=True
            )
            db.add(opp)
            new_opportunities.append(opp)

    # 2. FAILED PAYMENT RECOVERY
    failed_rate = state.get("failed_payments", {}).get("failed_rate_percent", 0)
    failed_orders = state.get("failed_payments", {}).get("failed_orders", 0)
    if failed_rate > 2.0:
        title = "Recover failed payments"
        existing = deduplicate_opportunity(db, merchant_id, title)
        
        evidence_strength = min(100.0, failed_rate * 10)
        score_components = calculate_normalized_score(evidence_strength, 80.0, 90.0, 95.0, 10.0)
        
        evidence = {
            "failed_payment_count": failed_orders,
            "failed_payment_rate": failed_rate,
            "signal": "High failure rate detected",
            "score_components": score_components,
            "impact_estimate_status": "UNAVAILABLE"
        }
        
        if existing:
            existing.evidence = evidence
            existing.score = score_components["final_score"]
            new_opportunities.append(existing)
        else:
            opp = GrowthOpportunity(
                id=uuid.uuid4(),
                merchant_id=merchant_id,
                type=OpportunityType.FAILED_PAYMENT_RECOVERY,
                title=title,
                description=f"Observed {failed_rate}% payment failure rate affecting {failed_orders} orders.",
                evidence=evidence,
                confidence=0.9,
                expected_revenue=0.0, 
                expected_profit=0.0,
                risk=OpportunityRisk.LOW,
                priority=int(score_components["final_score"]),
                score=score_components["final_score"],
                recommended_action="Enable automated payment retry emails.",
                requires_approval=True
            )
            db.add(opp)
            new_opportunities.append(opp)
        
    db.commit()
    
    action.output_summary = f"Generated {len(new_opportunities)} opportunities"
    db.commit()
    
    return {
        "opportunities": [
            {
                "id": str(o.id),
                "title": o.title,
                "type": o.type.value if hasattr(o.type, 'value') else str(o.type),
                "score": float(o.score),
                "evidence": o.evidence,
                "recommended_action": o.recommended_action
            } for o in new_opportunities
        ],
        "agent_action_ids": [action.id]
    }
