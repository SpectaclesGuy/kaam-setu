from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.common.utils import api_response
from app.core.dependencies import get_current_user, get_db
from app.operator.service import ensure_operator_scope
from app.profiles.models import WorkerAvailability, WorkerProfile
from app.profiles.schemas import WorkerAvailabilityCreate, WorkerProfileSetup
from app.users.models import User

router = APIRouter(prefix="/operator", tags=["operator"])


@router.post("/workers")
def create_worker_for_operator(payload: WorkerProfileSetup, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role not in {UserRole.operator, UserRole.admin}:
        raise HTTPException(status_code=403, detail="Operator access required")
    shadow_user = User(email=f"worker-{payload.phone_number}@kaamsetu.local", full_name=payload.full_name, role=UserRole.worker)
    db.add(shadow_user)
    db.flush()
    worker = WorkerProfile(
        user_id=shadow_user.id,
        phone_number=payload.phone_number,
        gender=payload.gender,
        profile_photo_url=payload.profile_photo_url,
        location_text=payload.primary_location,
        latitude=payload.latitude,
        longitude=payload.longitude,
        service_radius_km=payload.service_radius_km,
        experience_years=payload.experience_years,
        daily_rate=payload.daily_rate,
        hourly_rate=payload.hourly_rate,
        bio=payload.bio,
        available_today=payload.available_today,
        emergency_available=payload.emergency_available,
    )
    db.add(worker)
    db.commit()
    db.refresh(worker)
    return api_response("Worker onboarded by operator", {"id": worker.id})


@router.get("/workers")
def operator_workers(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == UserRole.admin:
        items = db.query(WorkerProfile).all()
    elif user.role == UserRole.operator and user.operator_profile:
        items = db.query(WorkerProfile).all()
        items = [item for item in items if user.operator_profile.assigned_area.lower() in item.location_text.lower()]
    else:
        raise HTTPException(status_code=403, detail="Operator access required")
    return api_response("Operator workers fetched", [item.id for item in items])


@router.patch("/workers/{worker_id}")
def update_operator_worker(worker_id: str, payload: WorkerProfileSetup, user=Depends(get_current_user), db: Session = Depends(get_db)):
    worker = db.get(WorkerProfile, worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    ensure_operator_scope(user, worker)
    worker.phone_number = payload.phone_number
    worker.location_text = payload.primary_location
    worker.latitude = payload.latitude
    worker.longitude = payload.longitude
    worker.daily_rate = payload.daily_rate
    db.commit()
    return api_response("Operator worker updated", {"id": worker.id})


@router.post("/workers/{worker_id}/documents")
def upload_operator_document(worker_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    worker = db.get(WorkerProfile, worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    ensure_operator_scope(user, worker)
    return api_response("Operator document endpoint ready", {"worker_id": worker.id})


@router.patch("/workers/{worker_id}/availability")
def update_operator_availability(
    worker_id: str, payload: WorkerAvailabilityCreate, user=Depends(get_current_user), db: Session = Depends(get_db)
):
    worker = db.get(WorkerProfile, worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    ensure_operator_scope(user, worker)
    availability = WorkerAvailability(worker_id=worker.id, **payload.model_dump())
    db.add(availability)
    db.commit()
    db.refresh(availability)
    return api_response("Operator worker availability updated", {"id": availability.id})
