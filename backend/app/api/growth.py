
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
import uuid
from typing import Optional
from app.database.session import get_db
from app.agents.graph import create_growth_agent
from pydantic import BaseModel
from app.models.growth import GrowthOpportunity
from app.models.agent import AgentRun, AgentAction, AuditLog
from app.models.enums import AgentRunStatus, AgentType, AuditActor
from sqlalchemy import select
import traceback

router = APIRouter(prefix="/api/agents", tags=["growth_agent"])

class RunAgentRequest(BaseModel):
    merchant_id: uuid.UUID

@router.post("/growth/run")
def run_growth_agent(req: RunAgentRequest, idempotency_key: Optional[str] = Header(None), db: Session = Depends(get_db)):
    # Idempotency check
    if idempotency_key:
        existing_run = db.execute(select(AgentRun).where(AgentRun.input_summary.like(f"%{idempotency_key}%"))).scalar_one_or_none()
        if existing_run and existing_run.status == AgentRunStatus.COMPLETED:
            return {"run_id": str(existing_run.id), "status": "COMPLETED_IDEMPOTENT"}

    run_id = uuid.uuid4()
    run_record = AgentRun(
        id=run_id,
        merchant_id=req.merchant_id,
        agent_type=AgentType.MERCHANT_GROWTH,
        status=AgentRunStatus.RUNNING,
        input_summary=f"Key: {idempotency_key}" if idempotency_key else "Standard manual run"
    )
    db.add(run_record)
    
    audit = AuditLog(
        id=uuid.uuid4(),
        merchant_id=req.merchant_id,
        agent_run_id=run_id,
        actor=AuditActor.SYSTEM,
        action="AGENT_RUN_STARTED",
        execution_status="SUCCESS"
    )
    db.add(audit)
    db.commit()
    
    agent = create_growth_agent(db)
    
    initial_state = {
        "merchant_id": req.merchant_id,
        "run_id": run_id,
        "agent_action_ids": [],
        "observed_metrics": {},
        "product_signals": {},
        "failed_payments": {},
        "analysis_summary": "",
        "opportunities": [],
        "strategies": [],
        "warnings": [],
        "errors": []
    }
    
    try:
        final_state = agent.invoke(initial_state)
        
        run_record.status = AgentRunStatus.COMPLETED
        run_record.output_summary = f"Generated {len(final_state.get('opportunities', []))} opportunities."
        
        audit_complete = AuditLog(
            id=uuid.uuid4(),
            merchant_id=req.merchant_id,
            agent_run_id=run_id,
            actor=AuditActor.SYSTEM,
            action="AGENT_RUN_COMPLETED",
            execution_status="SUCCESS"
        )
        db.add(audit_complete)
        db.commit()
        
        return {
            "run_id": str(run_id),
            "status": "COMPLETED",
            "opportunities": final_state.get("opportunities", []),
            "strategies": final_state.get("strategies", []),
            "warnings": final_state.get("warnings", []),
            "prediction_status": "PREDICTION_UNAVAILABLE"
        }
    except Exception as e:
        run_record.status = AgentRunStatus.FAILED
        run_record.output_summary = f"Error: {str(e)}"
        
        audit_failed = AuditLog(
            id=uuid.uuid4(),
            merchant_id=req.merchant_id,
            agent_run_id=run_id,
            actor=AuditActor.SYSTEM,
            action="AGENT_RUN_FAILED",
            execution_status="FAILED",
            error=str(e)
        )
        db.add(audit_failed)
        db.commit()
        
        return {
            "run_id": str(run_id),
            "status": "FAILED",
            "errors": [str(e)],
            "trace": traceback.format_exc()
        }

@router.get("/growth/opportunities")
def get_opportunities(merchant_id: uuid.UUID, db: Session = Depends(get_db)):
    stmt = select(GrowthOpportunity).where(GrowthOpportunity.merchant_id == merchant_id).order_by(GrowthOpportunity.created_at.desc())
    results = db.execute(stmt).scalars().all()
    
    return [
        {
            "id": str(o.id),
            "title": o.title,
            "type": str(o.type),
            "description": o.description,
            "evidence": o.evidence,
            "score": float(o.score),
            "confidence": float(o.confidence),
            "risk": str(o.risk),
            "recommended_action": o.recommended_action,
            "status": str(o.status),
            "requires_approval": o.requires_approval,
            "prediction_status": "UNAVAILABLE"
        }
        for o in results
    ]

@router.get("/runs")
def get_runs(merchant_id: uuid.UUID, db: Session = Depends(get_db)):
    stmt = select(AgentRun).where(AgentRun.merchant_id == merchant_id).order_by(AgentRun.started_at.desc())
    runs = db.execute(stmt).scalars().all()
    
    return [
        {
            "run_id": str(r.id),
            "status": str(r.status),
            "started_at": r.started_at,
            "ended_at": r.ended_at,
            "output_summary": r.output_summary
        }
        for r in runs
    ]

@router.get("/runs/{run_id}/actions")
def get_run_actions(run_id: uuid.UUID, db: Session = Depends(get_db)):
    stmt = select(AgentAction).where(AgentAction.agent_run_id == run_id).order_by(AgentAction.created_at.asc())
    actions = db.execute(stmt).scalars().all()
    
    return [
        {
            "id": str(a.id),
            "step": a.step,
            "tool_name": a.tool_name,
            "input_summary": a.input_summary,
            "output_summary": a.output_summary,
            "status": a.status,
            "created_at": a.created_at
        }
        for a in actions
    ]
