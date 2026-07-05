from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.bookings.models import Booking
from app.bookings.schemas import BookingCreate, BookingStatusUpdate
from app.bookings.service import create_booking, update_booking_status
from app.common.enums import BookingStatus, UserRole
from app.common.utils import api_response
from app.core.dependencies import get_current_user, get_db

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("")
def create_booking_endpoint(payload: BookingCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    booking = create_booking(db, user, payload)
    return api_response("Booking created", {"id": booking.id, "status": booking.status.value})


@router.get("/my")
def my_bookings(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == UserRole.worker and user.worker_profile:
        items = db.query(Booking).filter(Booking.worker_id == user.worker_profile.id).all()
    else:
        items = db.query(Booking).filter(Booking.employer_user_id == user.id).all()
    return api_response("Bookings fetched", [item.id for item in items])


@router.get("/{booking_id}")
def get_booking(booking_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if user.role != UserRole.admin and booking.employer_user_id != user.id and (
        not user.worker_profile or booking.worker_id != user.worker_profile.id
    ):
        raise HTTPException(status_code=403, detail="Cannot access this booking")
    return api_response("Booking fetched", {"id": booking.id, "status": booking.status.value})


@router.patch("/{booking_id}/status")
def patch_booking_status(
    booking_id: str, payload: BookingStatusUpdate, user=Depends(get_current_user), db: Session = Depends(get_db)
):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if user.role != UserRole.admin and booking.employer_user_id != user.id and (
        not user.worker_profile or booking.worker_id != user.worker_profile.id
    ):
        raise HTTPException(status_code=403, detail="Cannot modify this booking")
    booking = update_booking_status(db, booking, payload)
    return api_response("Booking status updated", {"id": booking.id, "status": booking.status.value})


@router.post("/{booking_id}/complete")
def complete_booking(booking_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return patch_booking_status(booking_id, BookingStatusUpdate(status=BookingStatus.completed), user, db)


@router.post("/{booking_id}/cancel")
def cancel_booking(booking_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return patch_booking_status(booking_id, BookingStatusUpdate(status=BookingStatus.cancelled), user, db)
