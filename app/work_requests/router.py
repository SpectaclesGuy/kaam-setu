from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.common.utils import api_response, haversine_distance_km
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


def serialize_work_request(item: WorkRequest):
    return {
        "id": item.id,
        "posted_by_user_id": item.posted_by_user_id,
        "category_id": item.category_id,
        "category_label": item.category_label,
        "title": item.title,
        "description": item.description,
        "location_text": item.location_text,
        "latitude": item.latitude,
        "longitude": item.longitude,
        "date_required": item.date_required,
        "time_required": item.time_required,
        "urgency": item.urgency.value,
        "budget_min": float(item.budget_min) if item.budget_min is not None else None,
        "budget_max": float(item.budget_max) if item.budget_max is not None else None,
        "workers_needed": item.workers_needed,
        "status": item.status.value,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "updated_at": item.updated_at.isoformat() if item.updated_at else None,
    }


@router.post("")
def create_request(payload: WorkRequestCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = create_work_request(db, user, payload)
    return api_response("Work request created", {"id": item.id})


@router.get("")
def list_requests(scope: str = Query(default="all"), user=Depends(get_current_user), db: Session = Depends(get_db)):
    items = list_work_requests(db, user)
    if scope == "mine":
        items = [item for item in items if item.posted_by_user_id == user.id]
    return api_response("Work requests fetched", [serialize_work_request(item) for item in items])


@router.get("/nearby-worker")
def nearby_for_worker(
    radius_km: float = Query(default=20, ge=1, le=100),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role != UserRole.worker or not user.worker_profile:
        raise HTTPException(status_code=403, detail="Worker access required")
    items = list_work_requests(db, user)
    results = []
    for item in items:
        if item.status != "open" and getattr(item.status, "value", item.status) != "open":
            continue
        distance = haversine_distance_km(
            user.worker_profile.latitude,
            user.worker_profile.longitude,
            item.latitude,
            item.longitude,
        )
        if distance > radius_km:
            continue
        serialized = serialize_work_request(item)
        serialized["distance_km"] = round(distance, 2)
        serialized["worker_latitude"] = user.worker_profile.latitude
        serialized["worker_longitude"] = user.worker_profile.longitude
        serialized["worker_location_text"] = user.worker_profile.location_text
        results.append(serialized)
    results.sort(key=lambda item: item["distance_km"])
    return api_response("Nearby work requests fetched", results)


@router.get("/{request_id}")
def get_request(request_id: str, db: Session = Depends(get_db)):
    item = db.get(WorkRequest, request_id)
    if not item:
        raise HTTPException(status_code=404, detail="Work request not found")
    return api_response("Work request fetched", serialize_work_request(item))


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
    return api_response("Work request updated", serialize_work_request(item))


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
