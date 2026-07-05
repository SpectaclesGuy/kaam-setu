from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.utils import api_response
from app.core.dependencies import get_current_user, get_db
from app.disputes.models import Dispute
from app.disputes.schemas import DisputeCreate, DisputeUpdate
from app.disputes.service import create_dispute, update_dispute

router = APIRouter(prefix="/disputes", tags=["disputes"])


@router.post("")
def create_dispute_endpoint(payload: DisputeCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    dispute = create_dispute(db, user, payload)
    return api_response("Dispute created", {"id": dispute.id})


@router.get("/my")
def my_disputes(user=Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(Dispute).filter(Dispute.raised_by_user_id == user.id).all()
    return api_response("Disputes fetched", [item.id for item in items])


@router.get("/admin/disputes")
def admin_disputes(user=Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(Dispute).all()
    return api_response("Admin disputes fetched", [item.id for item in items])


@router.patch("/admin/disputes/{dispute_id}/resolve")
def resolve_dispute(
    dispute_id: str, payload: DisputeUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)
):
    dispute = db.get(Dispute, dispute_id)
    if not dispute:
        raise HTTPException(status_code=404, detail="Dispute not found")
    dispute = update_dispute(db, user, dispute, payload)
    return api_response("Dispute updated", {"id": dispute.id, "status": dispute.status.value})
