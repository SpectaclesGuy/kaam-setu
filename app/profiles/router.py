from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.common.utils import api_response
from app.core.dependencies import get_current_user, get_db
from app.profiles.schemas import RoleSetupRequest, WorkerAvailabilityCreate, WorkerProfileUpdate
from app.profiles.service import add_worker_availability, setup_role_profile, update_worker_profile

router = APIRouter(prefix="/profile", tags=["profiles"])


@router.post("/setup-role")
def setup_role(payload: RoleSetupRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin setup is protected")
    if not user.is_verified_user:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email verification is required before profile setup")
    if not user.is_phone_verified or not user.phone_number:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Phone verification is required before profile setup",
        )
    profile_phone_number = None
    if payload.worker_profile:
        profile_phone_number = payload.worker_profile.phone_number
    elif payload.employer_profile:
        profile_phone_number = payload.employer_profile.phone_number
    elif payload.contractor_profile:
        profile_phone_number = payload.contractor_profile.phone_number
    elif payload.operator_profile:
        profile_phone_number = payload.operator_profile.phone_number
    if profile_phone_number != user.phone_number:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Use your verified phone number")
    user = setup_role_profile(db, user, payload)
    return api_response("Profile setup completed", {"role": user.role, "profile_completed": user.profile_completed})


@router.post("/workers/me/availability")
def create_availability(
    payload: WorkerAvailabilityCreate, user=Depends(get_current_user), db: Session = Depends(get_db)
):
    if user.role != UserRole.worker or not user.worker_profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Worker access required")
    availability = add_worker_availability(db, user.worker_profile, payload)
    return api_response("Availability added", {"id": availability.id})


@router.get("/me")
def my_profile(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == UserRole.worker and user.worker_profile:
        worker = user.worker_profile
        data = {
            "role": user.role,
            "full_name": user.full_name,
            "email": user.email,
            "phone_number": user.phone_number,
            "is_phone_verified": user.is_phone_verified,
            "profile_completed": user.profile_completed,
            "worker_profile": {
                "id": worker.id,
                "phone_number": worker.phone_number,
                "gender": worker.gender,
                "profile_photo_url": worker.profile_photo_url,
                "location_text": worker.location_text,
                "latitude": worker.latitude,
                "longitude": worker.longitude,
                "service_radius_km": worker.service_radius_km,
                "experience_years": worker.experience_years,
                "daily_rate": float(worker.daily_rate),
                "hourly_rate": float(worker.hourly_rate) if worker.hourly_rate is not None else None,
                "bio": worker.bio,
                "work_gallery_urls": worker.work_gallery_urls.split(",") if worker.work_gallery_urls else [],
                "available_today": worker.available_today,
                "emergency_available": worker.emergency_available,
                "verification_status": worker.verification_status.value,
                "skills": [skill.skill_name for skill in worker.skills],
                "languages": [language.language for language in worker.languages],
            },
        }
        return api_response("My profile fetched", data)
    data = {
        "role": user.role,
        "full_name": user.full_name,
        "email": user.email,
        "phone_number": user.phone_number,
        "is_phone_verified": user.is_phone_verified,
        "profile_completed": user.profile_completed,
    }
    if user.role == UserRole.employer and user.employer_profile:
        profile = user.employer_profile
        data["employer_profile"] = {
            "id": profile.id,
            "phone_number": profile.phone_number,
            "employer_type": profile.employer_type,
            "organization_name": profile.organization_name,
            "location": profile.location_text,
            "latitude": profile.latitude,
            "longitude": profile.longitude,
        }
    elif user.role == UserRole.contractor and user.contractor_profile:
        profile = user.contractor_profile
        data["contractor_profile"] = {
            "id": profile.id,
            "phone_number": profile.phone_number,
            "company_name": profile.company_name,
            "work_categories": profile.work_categories.split(",") if profile.work_categories else [],
            "frequent_locations": profile.frequent_locations.split(",") if profile.frequent_locations else [],
            "bulk_hiring_enabled": profile.bulk_hiring_enabled,
            "location": profile.location_text,
            "latitude": profile.latitude,
            "longitude": profile.longitude,
        }
    elif user.role == UserRole.operator and user.operator_profile:
        profile = user.operator_profile
        data["operator_profile"] = {
            "id": profile.id,
            "phone_number": profile.phone_number,
            "assigned_area": profile.assigned_area,
            "verification_permissions": profile.can_verify_workers,
            "latitude": profile.latitude,
            "longitude": profile.longitude,
        }
    return api_response(
        "My profile fetched",
        data,
    )


@router.patch("/me/worker")
def patch_my_worker_profile(
    payload: WorkerProfileUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)
):
    if user.role != UserRole.worker or not user.worker_profile:
        raise HTTPException(status_code=403, detail="Worker access required")
    user = update_worker_profile(db, user, payload)
    return api_response("Worker profile updated", {"user_id": user.id})
