from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.enums import VerificationStatus
from app.common.utils import api_response
from app.core.dependencies import get_current_user, get_db
from app.users.models import User
from app.verification.models import VerificationDocument
from app.verification.schemas import VerificationReview, VerificationUpload
from app.verification.service import review_document, upload_document

router = APIRouter(prefix="/verification", tags=["verification"])


@router.post("/upload")
def upload(payload: VerificationUpload, user=Depends(get_current_user), db: Session = Depends(get_db)):
    document = upload_document(db, user, payload)
    return api_response("Verification document uploaded", {"id": document.id})


@router.get("/me")
def my_documents(user=Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(VerificationDocument).filter(VerificationDocument.user_id == user.id).all()
    data = [
        {
            "id": item.id,
            "document_type": item.document_type.value,
            "document_url": item.document_url,
            "status": item.status.value,
            "remarks": item.remarks,
            "reviewed_at": item.reviewed_at,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in items
    ]
    return api_response("Verification documents fetched", data)


@router.get("/admin/verification/pending")
def pending_documents(user=Depends(get_current_user), db: Session = Depends(get_db)):
    items = (
        db.query(VerificationDocument)
        .filter(VerificationDocument.status == VerificationStatus.pending)
        .order_by(VerificationDocument.created_at.desc())
        .all()
    )
    data = []
    for item in items:
        owner = db.get(User, item.user_id)
        worker_profile = owner.worker_profile if owner and owner.worker_profile else None
        data.append(
            {
                "id": item.id,
                "user_id": item.user_id,
                "user_name": owner.full_name if owner else None,
                "user_email": owner.email if owner else None,
                "user_role": owner.role.value if owner and owner.role else None,
                "aadhaar_number": worker_profile.aadhaar_number if worker_profile else None,
                "document_type": item.document_type.value,
                "document_url": item.document_url,
                "status": item.status.value,
                "remarks": item.remarks,
                "created_at": item.created_at.isoformat() if item.created_at else None,
            }
        )
    return api_response("Pending verification documents fetched", data)


@router.patch("/admin/verification/{document_id}/review")
def review(document_id: str, payload: VerificationReview, user=Depends(get_current_user), db: Session = Depends(get_db)):
    document = db.get(VerificationDocument, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    document = review_document(db, user, document, payload)
    return api_response("Verification document reviewed", {"id": document.id, "status": document.status.value})
