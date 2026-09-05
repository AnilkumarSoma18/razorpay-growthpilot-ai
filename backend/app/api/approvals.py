
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from app.database.session import get_db
from app.models.agent import ApprovalRequest, AuditLog, AgentAction
from app.models.enums import ApprovalStatus, AuditActor
from app.models.growth import GrowthOpportunity
from app.services.authorization_service import create_approval_audit
from sqlalchemy import select
from pydantic import BaseModel

router = APIRouter(prefix="/api/approvals", tags=["approvals"])

class ApprovalCreateReq(BaseModel):
    merchant_id: uuid.UUID
    opportunity_id: uuid.UUID
    
from pydantic import BaseModel
class RejectReq(BaseModel):
    reason: str

@router.post("")
def create_approval(req: ApprovalCreateReq, db: Session = Depends(get_db)):
    # Validate opportunity exists and belongs to merchant
    opp = db.get(GrowthOpportunity, req.opportunity_id)
    if not opp or opp.merchant_id != req.merchant_id:
        raise HTTPException(status_code=404, detail="Opportunity not found")
        
    # Check for existing PENDING approval
    existing = db.execute(select(ApprovalRequest).where(
        ApprovalRequest.opportunity_id == req.opportunity_id,
        ApprovalRequest.status == ApprovalStatus.PENDING
    )).scalars().first()
    
    if existing:
        raise HTTPException(status_code=400, detail="A pending approval already exists for this opportunity.")
        
    # Snapshot important decision data
    snapshot = {
        "opportunity_title": opp.title,
        "evidence_summary": opp.evidence.get("signal", "No signal"),
        "score_components": opp.evidence.get("score_components", {}),
        "rule_based_score": float(opp.score),
        "prediction_status": opp.evidence.get("impact_estimate_status", "UNAVAILABLE"),
        "constraints": ["Do not automatically change price", "Do not automatically activate discount"]
    }
    
    approval_id = uuid.uuid4()
    approval = ApprovalRequest(
        id=approval_id,
        merchant_id=req.merchant_id,
        opportunity_id=req.opportunity_id,
        action_description=opp.recommended_action,
        reason=opp.description,
        evidence=snapshot,
        risk=str(opp.risk),
        status=ApprovalStatus.PENDING
    )
    db.add(approval)
    
    # Audit log
    create_approval_audit(db, req.merchant_id, approval_id, "APPROVAL_REQUESTED")
    db.commit()
    
    # Also update opportunity status
    opp.requires_approval = True
    # We'll use evidence to track local UI state since we don't have an opportunity status enum for "PENDING_APPROVAL"
    opp.evidence = {**opp.evidence, "approval_status": "PENDING", "approval_id": str(approval_id)}
    db.commit()
    
    return {"approval_id": str(approval_id), "status": "PENDING"}

@router.get("")
def list_approvals(merchant_id: uuid.UUID, db: Session = Depends(get_db)):
    stmt = select(ApprovalRequest).where(ApprovalRequest.merchant_id == merchant_id).order_by(ApprovalRequest.requested_at.desc())
    results = db.execute(stmt).scalars().all()
    
    return [
        {
            "id": str(a.id),
            "opportunity_id": str(a.opportunity_id) if a.opportunity_id else None,
            "action_description": a.action_description,
            "reason": a.reason,
            "status": str(a.status),
            "requested_at": a.requested_at,
            "risk": a.risk,
            "evidence_snapshot": a.evidence
        } for a in results
    ]

@router.get("/{approval_id}")
def get_approval(approval_id: uuid.UUID, db: Session = Depends(get_db)):
    a = db.get(ApprovalRequest, approval_id)
    if not a:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    return {
        "id": str(a.id),
        "merchant_id": str(a.merchant_id),
        "opportunity_id": str(a.opportunity_id) if a.opportunity_id else None,
        "action_description": a.action_description,
        "reason": a.reason,
        "status": str(a.status),
        "requested_at": a.requested_at,
        "risk": a.risk,
        "evidence_snapshot": a.evidence
    }

@router.post("/{approval_id}/approve")
def approve_request(approval_id: uuid.UUID, db: Session = Depends(get_db)):
    approval = db.get(ApprovalRequest, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only PENDING requests can be approved.")
        
    approval.status = ApprovalStatus.APPROVED
    approval.decided_at = datetime.now(timezone.utc)
    
    if approval.opportunity_id:
        opp = db.get(GrowthOpportunity, approval.opportunity_id)
        if opp:
            opp.evidence = {**opp.evidence, "approval_status": "APPROVED"}
    
    create_approval_audit(db, approval.merchant_id, approval_id, "APPROVAL_GRANTED")
    db.commit()
    return {"status": "APPROVED"}

@router.post("/{approval_id}/reject")
def reject_request(approval_id: uuid.UUID, req: RejectReq, db: Session = Depends(get_db)):
    approval = db.get(ApprovalRequest, approval_id)
    if not approval:
        raise HTTPException(status_code=404, detail="Approval not found")
        
    if approval.status != ApprovalStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only PENDING requests can be rejected.")
        
    approval.status = ApprovalStatus.REJECTED
    approval.decided_at = datetime.now(timezone.utc)
    
    if approval.opportunity_id:
        opp = db.get(GrowthOpportunity, approval.opportunity_id)
        if opp:
            opp.evidence = {**opp.evidence, "approval_status": "REJECTED"}
    
    create_approval_audit(db, approval.merchant_id, approval_id, "APPROVAL_REJECTED", reason=req.reason)
    db.commit()
    return {"status": "REJECTED"}
