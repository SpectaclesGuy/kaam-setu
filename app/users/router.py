from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.bookings.models import Booking
from app.common.utils import api_response
from app.contractor.models import SavedWorker
from app.core.dependencies import get_current_user, get_db
from app.notifications.models import Notification
from app.users.schemas import UserRead
from app.verification.models import VerificationDocument
from app.work_requests.models import WorkRequest

router = APIRouter(prefix="/me", tags=["me"])


@router.get("/summary")
def my_summary(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.worker_profile:
        booking_count = db.query(Booking).filter(Booking.worker_id == user.worker_profile.id).count()
    else:
        booking_count = db.query(Booking).filter(Booking.employer_user_id == user.id).count()
    request_count = db.query(WorkRequest).filter(WorkRequest.posted_by_user_id == user.id).count()
    saved_count = db.query(SavedWorker).filter(SavedWorker.contractor_user_id == user.id).count()
    unread_notifications = db.query(Notification).filter(Notification.user_id == user.id, Notification.is_read.is_(False)).count()
    verification_count = db.query(VerificationDocument).filter(VerificationDocument.user_id == user.id).count()
    return api_response(
        "User summary fetched",
        {
            "user": UserRead.model_validate(user).model_dump(),
            "counts": {
                "bookings": booking_count,
                "work_requests": request_count,
                "saved_workers": saved_count,
                "unread_notifications": unread_notifications,
                "verification_documents": verification_count,
            },
        },
    )
