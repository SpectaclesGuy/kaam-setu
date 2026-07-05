from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.profiles.models import WorkerProfile
from app.users.models import User


def ensure_operator_scope(user: User, worker: WorkerProfile):
    if user.role == UserRole.admin:
        return
    if user.role != UserRole.operator or not user.operator_profile:
        raise HTTPException(status_code=403, detail="Operator access required")
    if user.operator_profile.assigned_area.lower() not in worker.location_text.lower():
        raise HTTPException(status_code=403, detail="Worker is outside assigned operator area")
