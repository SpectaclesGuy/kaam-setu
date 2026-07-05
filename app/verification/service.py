from datetime import datetime

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.common.enums import UserRole, VerificationStatus
from app.users.models import User
from app.verification.models import VerificationDocument
from app.verification.schemas import VerificationReview, VerificationUpload


def upload_document(db: Session, user: User, payload: VerificationUpload) -> VerificationDocument:
    document = VerificationDocument(user_id=user.id, **payload.model_dump())
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def review_document(db: Session, reviewer: User, document: VerificationDocument, payload: VerificationReview):
    if reviewer.role not in {UserRole.admin, UserRole.operator}:
        raise HTTPException(status_code=403, detail="Admin or operator access required")
    document.status = payload.status
    document.remarks = payload.remarks
    document.reviewed_by = reviewer.id
    document.reviewed_at = datetime.utcnow().isoformat()
    db.commit()
    db.refresh(document)
    if payload.status == VerificationStatus.approved:
        document_owner = db.get(User, document.user_id)
        if document_owner:
            document_owner.is_verified_user = True
            if document_owner.worker_profile:
                document_owner.worker_profile.verification_status = VerificationStatus.approved
            db.commit()
    return document
