from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.contractor.models import SavedWorker
from app.contractor.schemas import SavedWorkerCreate
from app.profiles.models import WorkerProfile
from app.users.models import User


def ensure_contractor(user: User):
    if user.role not in {UserRole.contractor, UserRole.admin}:
        raise HTTPException(status_code=403, detail="Contractor access required")


def save_worker(db: Session, user: User, payload: SavedWorkerCreate):
    ensure_contractor(user)
    worker = db.get(WorkerProfile, payload.worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    item = SavedWorker(contractor_user_id=user.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
