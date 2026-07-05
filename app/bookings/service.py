from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.bookings.models import Booking
from app.bookings.schemas import BookingCreate, BookingStatusUpdate
from app.common.enums import BookingStatus, UserRole
from app.profiles.models import WorkerProfile
from app.users.models import User


def create_booking(db: Session, user: User, payload: BookingCreate) -> Booking:
    worker = db.get(WorkerProfile, payload.worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    if worker.user_id == user.id:
        raise HTTPException(status_code=400, detail="Workers cannot book themselves")
    if user.role not in {UserRole.employer, UserRole.contractor, UserRole.admin}:
        raise HTTPException(status_code=403, detail="Booking not allowed for this role")
    booking = Booking(employer_user_id=user.id, **payload.model_dump())
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def update_booking_status(db: Session, booking: Booking, payload: BookingStatusUpdate) -> Booking:
    booking.status = payload.status
    if payload.final_amount is not None:
        booking.final_amount = payload.final_amount
    db.commit()
    db.refresh(booking)
    return booking
