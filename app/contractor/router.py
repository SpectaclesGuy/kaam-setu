from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.utils import api_response
from app.contractor.models import SavedWorker
from app.contractor.schemas import BulkRequestCreate, SavedWorkerCreate
from app.contractor.service import ensure_contractor, save_worker
from app.core.dependencies import get_current_user, get_db

router = APIRouter(prefix="/contractor", tags=["contractor"])


@router.post("/bulk-request")
def bulk_request(payload: BulkRequestCreate, user=Depends(get_current_user)):
    ensure_contractor(user)
    return api_response("Bulk request submitted", payload.model_dump())


@router.get("/saved-workers")
def get_saved_workers(user=Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_contractor(user)
    items = db.query(SavedWorker).filter(SavedWorker.contractor_user_id == user.id).all()
    data = []
    for item in items:
        worker = db.get(__import__("app.profiles.models", fromlist=["WorkerProfile"]).WorkerProfile, item.worker_id)
        data.append(
            {
                "id": item.id,
                "worker_id": item.worker_id,
                "group_name": item.group_name,
                "saved_at": item.created_at.isoformat() if item.created_at else None,
                "worker_name": worker.user.full_name if worker and worker.user else None,
                "location_text": worker.location_text if worker else None,
                "daily_rate": float(worker.daily_rate) if worker else None,
            }
        )
    return api_response("Saved workers fetched", data)


@router.post("/saved-workers")
def create_saved_worker(payload: SavedWorkerCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = save_worker(db, user, payload)
    return api_response("Worker saved", {"id": item.id})


@router.delete("/saved-workers/{saved_worker_id}")
def delete_saved_worker(saved_worker_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_contractor(user)
    item = db.get(SavedWorker, saved_worker_id)
    if item and (item.contractor_user_id == user.id or user.role == "admin"):
        db.delete(item)
        db.commit()
    return api_response("Saved worker deleted")


@router.get("/worker-groups")
def worker_groups(user=Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_contractor(user)
    items = db.query(SavedWorker.group_name).filter(SavedWorker.contractor_user_id == user.id).distinct().all()
    return api_response("Worker groups fetched", [item[0] for item in items if item[0]])
