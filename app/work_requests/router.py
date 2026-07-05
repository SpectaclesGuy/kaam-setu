from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.common.utils import api_response
from app.core.dependencies import get_current_user, get_db
from app.work_requests.schemas import ApplyToRequest, AssignWorkerRequest, WorkRequestCreate, WorkRequestUpdate
from app.work_requests.service import (
    apply_to_work_request,
    assign_worker_to_request,
    create_work_request,
    list_work_requests,
    update_work_request,
)
from app.work_requests.models import WorkRequest

router = APIRouter(prefix="/work-requests", tags=["work_requests"])


@router.post("")
def create_request(payload: WorkRequestCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = create_work_request(db, user, payload)
    return api_response("Work request created", {"id": item.id})


@router.get("")
def list_requests(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return api_response("Work requests fetched", [item.id for item in list_work_requests(db, user)])


@router.get("/{request_id}")
def get_request(request_id: str, db: Session = Depends(get_db)):
    item = db.get(WorkRequest, request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Work request not found")
    return api_response("Work request fetched", {"id": item.id, "title": item.title, "status": item.status.value})


@router.patch("/{request_id}")
def patch_request(
    request_id: str, payload: WorkRequestUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)
):
    item = db.get(WorkRequest, request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Work request not found")
    if item.posted_by_user_id != user.id and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Cannot update this work request")
    item = update_work_request(db, item, payload)
    return api_response("Work request updated", {"id": item.id, "status": item.status.value})


@router.delete("/{request_id}")
def delete_request(request_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.get(WorkRequest, request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Work request not found")
    if item.posted_by_user_id != user.id and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Cannot delete this work request")
    db.delete(item)
    db.commit()
    return api_response("Work request deleted")


@router.post("/{request_id}/apply")
def apply_request(
    request_id: str, payload: ApplyToRequest, user=Depends(get_current_user), db: Session = Depends(get_db)
):
    if user.role != UserRole.worker or not user.worker_profile:
        raise HTTPException(status_code=403, detail="Worker access required")
    item = db.get(WorkRequest, request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Work request not found")
    application = apply_to_work_request(db, item, user.worker_profile, payload.message)
    return api_response("Application submitted", {"id": application.id})


@router.post("/{request_id}/assign-worker")
def assign_worker(
    request_id: str, payload: AssignWorkerRequest, user=Depends(get_current_user), db: Session = Depends(get_db)
):
    item = db.get(WorkRequest, request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Work request not found")
    if item.posted_by_user_id != user.id and user.role not in {UserRole.admin, UserRole.contractor}:
        raise HTTPException(status_code=403, detail="Cannot assign worker")
    item = assign_worker_to_request(db, item, payload.worker_id)
    return api_response("Worker assigned", {"id": item.id, "status": item.status.value})
