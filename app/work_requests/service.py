from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.common.enums import ApplicationStatus, UserRole, WorkRequestStatus
from app.profiles.models import WorkerProfile
from app.users.models import User
from app.work_requests.models import WorkRequest, WorkRequestApplication
from app.work_requests.schemas import WorkRequestCreate, WorkRequestUpdate


def create_work_request(db: Session, user: User, payload: WorkRequestCreate) -> WorkRequest:
    if user.role not in {UserRole.employer, UserRole.contractor, UserRole.admin}:
        raise HTTPException(status_code=403, detail="Only employers or contractors can post work requests")
    work_request = WorkRequest(posted_by_user_id=user.id, **payload.model_dump())
    db.add(work_request)
    db.commit()
    db.refresh(work_request)
    return work_request


def list_work_requests(db: Session, user: User | None = None):
    query = db.query(WorkRequest)
    if not user or user.role not in {UserRole.admin, UserRole.operator}:
        query = query.filter(WorkRequest.status != WorkRequestStatus.cancelled)
    return query.order_by(WorkRequest.created_at.desc()).all()


def apply_to_work_request(db: Session, work_request: WorkRequest, worker: WorkerProfile, message: str | None):
    application = WorkRequestApplication(work_request_id=work_request.id, worker_id=worker.id, message=message)
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def assign_worker_to_request(db: Session, work_request: WorkRequest, worker_id: str):
    worker = db.get(WorkerProfile, worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    work_request.status = WorkRequestStatus.assigned
    application = (
        db.query(WorkRequestApplication)
        .filter(WorkRequestApplication.work_request_id == work_request.id, WorkRequestApplication.worker_id == worker_id)
        .first()
    )
    if application:
        application.status = ApplicationStatus.accepted
    db.commit()
    db.refresh(work_request)
    return work_request


def update_work_request(db: Session, work_request: WorkRequest, payload: WorkRequestUpdate):
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(work_request, key, value)
    db.commit()
    db.refresh(work_request)
    return work_request
