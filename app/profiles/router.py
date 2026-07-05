from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.common.utils import api_response
from app.core.dependencies import get_current_user, get_db
from app.profiles.schemas import RoleSetupRequest, WorkerAvailabilityCreate
from app.profiles.service import add_worker_availability, setup_role_profile

router = APIRouter(prefix="/profile", tags=["profiles"])


@router.post("/setup-role")
def setup_role(payload: RoleSetupRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin setup is protected")
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
