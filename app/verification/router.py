from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.utils import api_response
from app.core.dependencies import get_current_user, get_db
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
    return api_response("Verification documents fetched", [item.id for item in items])


@router.get("/admin/verification/pending")
def pending_documents(user=Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(VerificationDocument).all()
    return api_response("Pending verification documents fetched", [item.id for item in items if item.status.value == "pending"])


@router.patch("/admin/verification/{document_id}/review")
def review(document_id: str, payload: VerificationReview, user=Depends(get_current_user), db: Session = Depends(get_db)):
    document = db.get(VerificationDocument, document_id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    document = review_document(db, user, document, payload)
    return api_response("Verification document reviewed", {"id": document.id, "status": document.status.value})
