from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.utils import api_response
from app.core.dependencies import get_current_user, get_db
from app.notifications.models import Notification

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def list_notifications(user=Depends(get_current_user), db: Session = Depends(get_db)):
    items = db.query(Notification).filter(Notification.user_id == user.id).all()
    return api_response("Notifications fetched", [item.id for item in items])


@router.patch("/{notification_id}/read")
def read_notification(notification_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.get(Notification, notification_id)
    if not item or item.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    item.is_read = True
    db.commit()
    return api_response("Notification marked as read", {"id": item.id})
