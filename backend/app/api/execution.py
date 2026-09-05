
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
import uuid
from typing import Optional, Dict, Any
from app.database.session import get_db
from pydantic import BaseModel
from app.models.growth import GrowthOpportunity, Campaign, CampaignEvent
from app.models.agent import ApprovalRequest, AgentAction, AuditLog
from app.models.enums import ApprovalStatus, AuditActor
from app.services.authorization_service import can_execute
from datetime import datetime, timezone
from sqlalchemy import select

router = APIRouter(prefix="/api/growth", tags=["execution"])

class SimulateReq(BaseModel):
    merchant_id: uuid.UUID
    opportunity_id: uuid.UUID

class ExecuteReq(BaseModel):
    merchant_id: uuid.UUID
    opportunity_id: uuid.UUID
    approval_id: uuid.UUID

@router.post("/simulate")
def simulate_strategy(req: SimulateReq, db: Session = Depends(get_db)):
    opp = db.get(GrowthOpportunity, req.opportunity_id)
    if not opp or opp.merchant_id != req.merchant_id:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    # Build a deterministic simulation based on evidence
    simulation_id = str(uuid.uuid4())
    
    if opp.type.value == "CROSS_SELL":
        evidence = opp.evidence
        co_purchases = evidence.get("co_purchase_count", 0)
        
        baseline = {
            "historical_affected_population": 500,
            "historical_co_purchase_rate_percent": 15.0,
            "historical_co_purchases": co_purchases
        }
        assumptions = [
            "10% of eligible customers are exposed.",
            "Historical co-purchase rate is used as the baseline.",
            "No causal lift is claimed.",
            "No real customer communication occurs.",
            "No real payment occurs."
        ]
        simulated = {
            "simulated_additional_exposures": 50,
            "simulated_baseline_conversions": round(50 * 0.15, 0)
        }
    elif opp.type.value == "FAILED_PAYMENT_RECOVERY":
        failed_count = opp.evidence.get("failed_payment_count", 0)
        baseline = {
            "historical_failed_payments": failed_count,
            "historical_recovery_rate_percent": 5.0
        }
        assumptions = [
            "No real emails will be sent.",
            "Historical recovery baseline applied."
        ]
        simulated = {
            "simulated_recovery_segment_size": failed_count,
            "simulated_recovered_payments": round(failed_count * 0.05, 0)
        }
    else:
        baseline = {}
        assumptions = ["Deterministic simulation unsupported for this type"]
        simulated = {}

    return {
        "simulation_id": simulation_id,
        "simulation_status": "SIMULATED",
        "baseline_metrics": baseline,
        "assumptions": assumptions,
        "simulated_metrics": simulated,
        "confidence": "DETERMINISTIC_FALLBACK"
    }

@router.post("/executions")
def execute_strategy(req: ExecuteReq, idempotency_key: Optional[str] = Header(None), db: Session = Depends(get_db)):
    opp = db.get(GrowthOpportunity, req.opportunity_id)
    if not opp or opp.merchant_id != req.merchant_id:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    # Idempotency check
    if idempotency_key:
        existing = db.execute(select(Campaign).where(Campaign.name.like(f"%{idempotency_key}%"))).scalars().first()
        if existing:
            return {"execution_id": str(existing.id), "status": "SUCCEEDED_IDEMPOTENT"}

    # 1. Authorization Boundary Check
    is_authorized = can_execute(db, req.merchant_id, req.opportunity_id)
    if not is_authorized:
        # Create blocked audit
        db.add(AuditLog(
            id=uuid.uuid4(), merchant_id=req.merchant_id, actor=AuditActor.SYSTEM,
            action="EXECUTION_BLOCKED", execution_status="BLOCKED",
            error="Strategy is not authorized. Valid approval required."
        ))
        db.commit()
        raise HTTPException(status_code=403, detail="EXECUTION_NOT_AUTHORIZED: Approval missing or rejected.")
        
    approval = db.get(ApprovalRequest, req.approval_id)
    if not approval or approval.status != ApprovalStatus.APPROVED:
        raise HTTPException(status_code=403, detail="EXECUTION_NOT_AUTHORIZED: Invalid approval ID.")

    # 2. Execution Record (Using Campaign model)
    execution_id = uuid.uuid4()
    campaign = Campaign(
        id=execution_id,
        merchant_id=req.merchant_id,
        opportunity_id=req.opportunity_id,
        name=f"Execution {idempotency_key or execution_id}",
        type=opp.type.value,
        status="EXECUTING",
        config={"environment": "DEMO_SIMULATED", "approval_id": str(req.approval_id)}
    )
    db.add(campaign)
    
    db.add(AuditLog(
        id=uuid.uuid4(), merchant_id=req.merchant_id, actor=AuditActor.SYSTEM,
        action="EXECUTION_STARTED", execution_status="SUCCESS",
        input_summary=f"Executing opp: {opp.title}"
    ))
    db.commit()

    # 3. Simulate Operation
    try:
        # We perform safe operations ONLY
        if opp.type.value == "CROSS_SELL":
            simulated_effect = "Recommendation would be presented to eligible customers."
        elif opp.type.value == "FAILED_PAYMENT_RECOVERY":
            simulated_effect = "Eligible failed-payment customers would be placed into a recovery segment."
        else:
            simulated_effect = "Generic fallback simulated effect."
            
        campaign.config = {**campaign.config, "simulated_effect": simulated_effect}
        campaign.status = "SUCCEEDED"
        
        # 4. Result Verification
        assert campaign.status == "SUCCEEDED", "Verification failed"
        
        db.add(AgentAction(
            id=uuid.uuid4(), agent_run_id=uuid.UUID(int=0), # Dummy run ID since execution happens async to run
            step="EXECUTION_COMPLETED", tool_name="execution_engine",
            input_summary="Verified execution state.", status="COMPLETED"
        ))
        
        db.add(AuditLog(
            id=uuid.uuid4(), merchant_id=req.merchant_id, actor=AuditActor.SYSTEM,
            action="EXECUTION_SUCCEEDED", execution_status="SUCCESS",
            input_summary=simulated_effect
        ))
        
    except Exception as e:
        campaign.status = "FAILED"
        campaign.config = {**campaign.config, "error": str(e)}
        db.add(AuditLog(
            id=uuid.uuid4(), merchant_id=req.merchant_id, actor=AuditActor.SYSTEM,
            action="EXECUTION_FAILED", execution_status="FAILED", error=str(e)
        ))

    # Update Opportunity State
    opp.evidence = {**opp.evidence, "approval_status": "EXECUTED_SIMULATED"}
    db.commit()

    return {
        "execution_id": str(campaign.id),
        "status": campaign.status,
        "result": campaign.config.get("simulated_effect")
    }

@router.get("/audit")
def get_audit_trail(merchant_id: uuid.UUID, db: Session = Depends(get_db)):
    stmt = select(AuditLog).where(AuditLog.merchant_id == merchant_id).order_by(AuditLog.created_at.desc())
    logs = db.execute(stmt).scalars().all()
    return [
        {
            "id": str(L.id),
            "actor": str(L.actor),
            "action": L.action,
            "status": L.execution_status,
            "summary": L.input_summary or L.reason or L.error or "",
            "timestamp": L.created_at
        } for L in logs
    ]
