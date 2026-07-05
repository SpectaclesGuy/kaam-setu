from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.disputes.models import Dispute
from app.disputes.schemas import DisputeCreate, DisputeUpdate
from app.users.models import User


def create_dispute(db: Session, user: User, payload: DisputeCreate) -> Dispute:
    dispute = Dispute(
        raised_by_user_id=user.id,
        issue_type=payload.issue_type,
        description=payload.description,
        evidence_urls=",".join(payload.evidence_urls),
        booking_id=payload.booking_id,
        against_user_id=payload.against_user_id,
    )
    db.add(dispute)
    db.commit()
    db.refresh(dispute)
    return dispute


def update_dispute(db: Session, user: User, dispute: Dispute, payload: DisputeUpdate):
    if user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    dispute.status = payload.status
    dispute.admin_notes = payload.admin_notes
    db.commit()
    db.refresh(dispute)
    return dispute
