from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.bookings.models import Booking
from app.bookings.schemas import BookingCreate, BookingStatusUpdate
from app.common.enums import BookingStatus, UserRole
from app.otp.service import BOOKING_START_PURPOSE, create_or_refresh_challenge, get_active_challenge, verify_challenge
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
    previous_status = booking.status
    if payload.status == BookingStatus.in_progress and not booking.service_start_verified:
        raise HTTPException(status_code=400, detail="Verify service start with OTP before moving to in progress")
    booking.status = payload.status
    if payload.final_amount is not None:
        booking.final_amount = payload.final_amount
    if payload.status == BookingStatus.completed and previous_status != BookingStatus.completed:
        booking.service_started_at = booking.service_started_at or datetime.now(timezone.utc)
    db.commit()
    db.refresh(booking)
    return booking


def send_booking_start_otp(db: Session, booking: Booking, user: User):
    is_assigned_worker = bool(user.worker_profile and booking.worker_id == user.worker_profile.id)
    if not is_assigned_worker and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only the assigned worker can mark arrival")
    if booking.status != BookingStatus.accepted:
        raise HTTPException(status_code=400, detail="Only accepted bookings can generate an on-site start code")
    employer = db.get(User, booking.employer_user_id)
    if not employer or not employer.phone_number:
        raise HTTPException(status_code=400, detail="The customer does not have a phone number on file")
    return create_or_refresh_challenge(
        db,
        user=employer,
        booking=booking,
        destination=employer.phone_number,
        purpose=BOOKING_START_PURPOSE,
        channel="phone",
        provider_override="internal",
    )


def verify_booking_start_otp(db: Session, booking: Booking, user: User, code: str) -> Booking:
    is_assigned_worker = bool(user.worker_profile and booking.worker_id == user.worker_profile.id)
    if not is_assigned_worker and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only the assigned worker can start the service")
    employer = db.get(User, booking.employer_user_id)
    if not employer or not employer.phone_number:
        raise HTTPException(status_code=400, detail="The customer does not have a phone number on file")
    challenge = verify_challenge(
        db,
        user=employer,
        booking=booking,
        destination=employer.phone_number,
        code=code,
        purpose=BOOKING_START_PURPOSE,
        channel="phone",
    )
    booking.status = BookingStatus.in_progress
    booking.service_start_verified = True
    booking.service_start_verified_at = challenge.verified_at
    booking.service_started_at = challenge.verified_at
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


def get_booking_start_otp(db: Session, booking: Booking, user: User) -> dict:
    if booking.employer_user_id != user.id and user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Only the booking owner can view the on-site start code")
    if booking.status != BookingStatus.accepted:
        raise HTTPException(status_code=400, detail="This booking is not ready for an on-site start code")
    if not user.phone_number:
        raise HTTPException(status_code=400, detail="Phone number missing")
    challenge = get_active_challenge(
        db,
        user_id=user.id,
        booking_id=booking.id,
        destination=user.phone_number,
        purpose=BOOKING_START_PURPOSE,
    )
    if not challenge:
        raise HTTPException(status_code=404, detail="No active on-site start code is available yet")
    return {
        "code": challenge.verification_code,
        "expires_at": challenge.expires_at.isoformat() if challenge.expires_at else None,
    }
