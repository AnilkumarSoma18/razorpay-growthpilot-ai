
import uuid
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.models.agent import ApprovalRequest, AuditLog, AgentAction
from app.models.enums import ApprovalStatus, AuditActor
from app.models.growth import GrowthOpportunity

def can_execute(db: Session, merchant_id: uuid.UUID, opportunity_id: uuid.UUID) -> bool:
    """
    Authorization boundary: Execution is allowed ONLY IF:
    - approval exists
    - approval.status == APPROVED
    - approval belongs to same merchant
    - approval references same opportunity
    """
    stmt = select(ApprovalRequest).where(
        ApprovalRequest.merchant_id == merchant_id,
        ApprovalRequest.opportunity_id == opportunity_id,
        ApprovalRequest.status == ApprovalStatus.APPROVED
    ).order_by(ApprovalRequest.requested_at.desc())
    
    approval = db.execute(stmt).scalars().first()
    
    if not approval:
        return False
        
    return True

def create_approval_audit(db: Session, merchant_id: uuid.UUID, approval_id: uuid.UUID, action: str, reason: str = None):
    audit = AuditLog(
        id=uuid.uuid4(),
        merchant_id=merchant_id,
        actor=AuditActor.MERCHANT,
        action=action,
        execution_status="SUCCESS",
        input_summary=f"Approval ID: {approval_id}",
        reason=reason
    )
    db.add(audit)
