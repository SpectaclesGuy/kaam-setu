from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.enums import ContactType, UserRole
from app.common.utils import api_response
from app.contact_logs import ContactLog
from app.core.dependencies import get_current_user, get_db
from app.profiles.models import WorkerProfile

router = APIRouter(prefix="/contact-log", tags=["contact_logs"])


def _log_contact(contact_type: ContactType, worker_id: str, user, db: Session):
    if user.role not in {UserRole.employer, UserRole.contractor, UserRole.admin}:
        raise HTTPException(status_code=403, detail="Employer or contractor access required")
    worker = db.get(WorkerProfile, worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    item = ContactLog(employer_user_id=user.id, worker_id=worker_id, contact_type=contact_type.value)
    db.add(item)
    db.commit()
    db.refresh(item)
    return api_response("Contact logged", {"id": item.id, "contact_type": item.contact_type})


@router.post("/call")
def log_call(worker_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return _log_contact(ContactType.call, worker_id, user, db)


@router.post("/whatsapp")
def log_whatsapp(worker_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return _log_contact(ContactType.whatsapp, worker_id, user, db)
