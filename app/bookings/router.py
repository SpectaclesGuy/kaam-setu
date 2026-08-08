from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.bookings.models import Booking
from app.bookings.schemas import BookingCreate, BookingStartOTPVerify, BookingStatusUpdate
from app.bookings.service import (
    create_booking,
    get_booking_start_otp,
    send_booking_start_otp,
    update_booking_status,
    verify_booking_start_otp,
)
from app.common.enums import BookingStatus, UserRole
from app.common.utils import api_response
from app.core.dependencies import get_current_user, get_db

router = APIRouter(prefix="/bookings", tags=["bookings"])


def serialize_booking(booking: Booking, db: Session):
    worker = db.get(__import__("app.profiles.models", fromlist=["WorkerProfile"]).WorkerProfile, booking.worker_id)
    employer = db.get(__import__("app.users.models", fromlist=["User"]).User, booking.employer_user_id)
    return {
        "id": booking.id,
        "work_request_id": booking.work_request_id,
        "employer_user_id": booking.employer_user_id,
        "worker_id": booking.worker_id,
        "status": booking.status.value,
        "scheduled_date": booking.scheduled_date,
        "scheduled_time": booking.scheduled_time,
        "final_amount": float(booking.final_amount) if booking.final_amount is not None else None,
        "notes": booking.notes,
        "service_started_at": booking.service_started_at.isoformat() if booking.service_started_at else None,
        "service_start_verified": booking.service_start_verified,
        "service_start_verified_at": booking.service_start_verified_at.isoformat() if booking.service_start_verified_at else None,
        "created_at": booking.created_at.isoformat() if booking.created_at else None,
        "updated_at": booking.updated_at.isoformat() if booking.updated_at else None,
        "worker_name": worker.user.full_name if worker and worker.user else None,
        "worker_user_id": worker.user_id if worker else None,
        "employer_name": employer.full_name if employer else None,
    }


@router.post("")
def create_booking_endpoint(payload: BookingCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    booking = create_booking(db, user, payload)
    return api_response("Booking created", serialize_booking(booking, db))


@router.get("/my")
def my_bookings(user=Depends(get_current_user), db: Session = Depends(get_db)):
    if user.role == UserRole.worker and user.worker_profile:
        items = db.query(Booking).filter(Booking.worker_id == user.worker_profile.id).all()
    else:
        items = db.query(Booking).filter(Booking.employer_user_id == user.id).all()
    return api_response("Bookings fetched", [serialize_booking(item, db) for item in items])


@router.get("/{booking_id}")
def get_booking(booking_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if user.role != UserRole.admin and booking.employer_user_id != user.id and (
        not user.worker_profile or booking.worker_id != user.worker_profile.id
    ):
        raise HTTPException(status_code=403, detail="Cannot access this booking")
    return api_response("Booking fetched", serialize_booking(booking, db))


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
    if user.worker_profile and booking.worker_id == user.worker_profile.id and payload.status not in {
        BookingStatus.accepted,
        BookingStatus.rejected,
        BookingStatus.in_progress,
        BookingStatus.completed,
        BookingStatus.cancelled,
    }:
        raise HTTPException(status_code=400, detail="Worker cannot set this booking status")
    booking = update_booking_status(db, booking, payload)
    return api_response("Booking status updated", serialize_booking(booking, db))


@router.post("/{booking_id}/complete")
def complete_booking(booking_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return patch_booking_status(booking_id, BookingStatusUpdate(status=BookingStatus.completed), user, db)


@router.post("/{booking_id}/cancel")
def cancel_booking(booking_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    return patch_booking_status(booking_id, BookingStatusUpdate(status=BookingStatus.cancelled), user, db)


@router.post("/{booking_id}/start/send-otp")
def start_booking_send_otp(booking_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    challenge = send_booking_start_otp(db, booking, user)
    return api_response(
        "On-site start code generated",
        {
            "booking_id": booking.id,
            "customer_phone_number": challenge.phone_number,
            "expires_at": challenge.expires_at.isoformat() if challenge.expires_at else None,
        },
    )


@router.get("/{booking_id}/start/code")
def get_start_booking_code(booking_id: str, user=Depends(get_current_user), db: Session = Depends(get_db)):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return api_response("On-site start code fetched", get_booking_start_otp(db, booking, user))


@router.post("/{booking_id}/start/verify-otp")
def start_booking_verify_otp(
    booking_id: str,
    payload: BookingStartOTPVerify,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = db.get(Booking, booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking = verify_booking_start_otp(db, booking, user, payload.code)
    return api_response("Service started", serialize_booking(booking, db))
