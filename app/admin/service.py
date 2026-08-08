from sqlalchemy import func
from sqlalchemy.orm import Session

from app.bookings.models import Booking
from app.common.enums import BookingStatus, UserRole, WorkRequestStatus
from app.contact_logs import ContactLog
from app.contractor.models import SavedWorker
from app.disputes.models import Dispute
from app.notifications.models import Notification
from app.otp.models import OTPChallenge
from app.profiles.models import Category, EmployerProfile, WorkerProfile
from app.profiles.models import ContractorProfile, OperatorProfile, WorkerAvailability, WorkerLanguage, WorkerSkill
from app.reviews.models import Review
from app.runtime_settings.service import get_runtime_settings, set_runtime_settings
from app.users.models import User
from app.verification.models import VerificationDocument
from app.work_requests.models import WorkRequest, WorkRequestApplication


def dashboard_metrics(db: Session) -> dict:
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_workers = db.query(func.count(WorkerProfile.id)).scalar() or 0
    total_employers = db.query(func.count(EmployerProfile.id)).scalar() or 0
    active_jobs = db.query(func.count(WorkRequest.id)).filter(WorkRequest.status == WorkRequestStatus.open).scalar() or 0
    completed_bookings = (
        db.query(func.count(Booking.id)).filter(Booking.status == BookingStatus.completed).scalar() or 0
    )
    pending_verification = (
        db.query(func.count(VerificationDocument.id))
        .filter(VerificationDocument.status == "pending")
        .scalar()
        or 0
    )
    disputes_count = db.query(func.count(Dispute.id)).scalar() or 0
    workers_by_category = {}
    jobs_by_category = {}
    top_locations_by_demand = (
        db.query(WorkRequest.location_text, func.count(WorkRequest.id))
        .group_by(WorkRequest.location_text)
        .order_by(func.count(WorkRequest.id).desc())
        .limit(5)
        .all()
    )
    return {
        "total_users": total_users,
        "total_workers": total_workers,
        "total_employers": total_employers,
        "active_jobs": active_jobs,
        "completed_bookings": completed_bookings,
        "pending_verification_count": pending_verification,
        "disputes_count": disputes_count,
        "workers_by_category": workers_by_category,
        "jobs_by_category": jobs_by_category,
        "top_locations_by_demand": [{"location": row[0], "count": row[1]} for row in top_locations_by_demand],
        "supply_demand_category_gap": [],
    }


def seed_categories(db: Session, names: list[str]):
    existing = {item.name for item in db.query(Category).all()}
    for name in names:
        if name not in existing:
            db.add(Category(name=name, slug=name.lower().replace(" ", "-")))
    db.commit()


def serialize_admin_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value if user.role else None,
        "is_active": user.is_active,
        "is_verified_user": user.is_verified_user,
        "is_phone_verified": user.is_phone_verified,
        "phone_number": user.phone_number,
        "profile_completed": user.profile_completed,
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
    }


def list_admin_users(db: Session) -> list[dict]:
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [serialize_admin_user(user) for user in users]


def update_admin_user(
    db: Session,
    user: User,
    *,
    role: UserRole | None,
    role_provided: bool,
    is_active: bool | None,
) -> dict:
    if role_provided:
        user.role = role
        if role == UserRole.admin:
            user.profile_completed = True
    if is_active is not None:
        user.is_active = is_active
    db.add(user)
    db.commit()
    db.refresh(user)
    return serialize_admin_user(user)


def list_admin_runtime_settings(db: Session) -> dict[str, bool]:
    return get_runtime_settings(db)


def update_admin_runtime_settings(
    db: Session,
    *,
    profile_setup_require_email_verification: bool,
    profile_setup_require_phone_verification: bool,
    work_request_require_phone_verification: bool,
) -> dict[str, bool]:
    return set_runtime_settings(
        db,
        profile_setup_require_email_verification=profile_setup_require_email_verification,
        profile_setup_require_phone_verification=profile_setup_require_phone_verification,
        work_request_require_phone_verification=work_request_require_phone_verification,
    )


def delete_admin_user(db: Session, user: User) -> None:
    worker_profile = db.query(WorkerProfile).filter(WorkerProfile.user_id == user.id).first()
    worker_profile_id = worker_profile.id if worker_profile else None

    request_ids = [
        item_id for (item_id,) in db.query(WorkRequest.id).filter(WorkRequest.posted_by_user_id == user.id).all()
    ]
    booking_ids = {
        item_id
        for (item_id,) in db.query(Booking.id).filter(Booking.employer_user_id == user.id).all()
    }
    if worker_profile_id:
        booking_ids.update(
            item_id for (item_id,) in db.query(Booking.id).filter(Booking.worker_id == worker_profile_id).all()
        )

    if request_ids:
        booking_ids.update(
            item_id for (item_id,) in db.query(Booking.id).filter(Booking.work_request_id.in_(request_ids)).all()
        )

    if booking_ids:
        db.query(Review).filter(Review.booking_id.in_(booking_ids)).delete(synchronize_session=False)
        db.query(Dispute).filter(Dispute.booking_id.in_(booking_ids)).delete(synchronize_session=False)
        db.query(OTPChallenge).filter(OTPChallenge.booking_id.in_(booking_ids)).delete(synchronize_session=False)

    db.query(Review).filter(
        (Review.reviewer_user_id == user.id) | (Review.reviewee_user_id == user.id)
    ).delete(synchronize_session=False)
    db.query(Dispute).filter(
        (Dispute.raised_by_user_id == user.id) | (Dispute.against_user_id == user.id)
    ).delete(synchronize_session=False)
    db.query(Notification).filter(Notification.user_id == user.id).delete(synchronize_session=False)
    db.query(OTPChallenge).filter(OTPChallenge.user_id == user.id).delete(synchronize_session=False)
    db.query(VerificationDocument).filter(VerificationDocument.user_id == user.id).delete(synchronize_session=False)
    db.query(VerificationDocument).filter(VerificationDocument.reviewed_by == user.id).update(
        {
            VerificationDocument.reviewed_by: None,
            VerificationDocument.remarks: "Reviewer account removed by admin.",
        },
        synchronize_session=False,
    )
    db.query(ContactLog).filter(ContactLog.employer_user_id == user.id).delete(synchronize_session=False)
    db.query(SavedWorker).filter(SavedWorker.contractor_user_id == user.id).delete(synchronize_session=False)

    if worker_profile_id:
        db.query(ContactLog).filter(ContactLog.worker_id == worker_profile_id).delete(synchronize_session=False)
        db.query(SavedWorker).filter(SavedWorker.worker_id == worker_profile_id).delete(synchronize_session=False)
        db.query(WorkRequestApplication).filter(WorkRequestApplication.worker_id == worker_profile_id).delete(
            synchronize_session=False
        )
        db.query(Booking).filter(Booking.worker_id == worker_profile_id).delete(synchronize_session=False)
        db.query(WorkerAvailability).filter(WorkerAvailability.worker_id == worker_profile_id).delete(
            synchronize_session=False
        )
        db.query(WorkerLanguage).filter(WorkerLanguage.worker_id == worker_profile_id).delete(
            synchronize_session=False
        )
        db.query(WorkerSkill).filter(WorkerSkill.worker_id == worker_profile_id).delete(synchronize_session=False)
        db.query(WorkerProfile).filter(WorkerProfile.id == worker_profile_id).delete(synchronize_session=False)

    if request_ids:
        db.query(WorkRequestApplication).filter(WorkRequestApplication.work_request_id.in_(request_ids)).delete(
            synchronize_session=False
        )
        db.query(Booking).filter(Booking.work_request_id.in_(request_ids)).delete(synchronize_session=False)
        db.query(WorkRequest).filter(WorkRequest.id.in_(request_ids)).delete(synchronize_session=False)

    db.query(Booking).filter(Booking.employer_user_id == user.id).delete(synchronize_session=False)
    db.query(EmployerProfile).filter(EmployerProfile.user_id == user.id).delete(synchronize_session=False)
    db.query(ContractorProfile).filter(ContractorProfile.user_id == user.id).delete(synchronize_session=False)
    db.query(OperatorProfile).filter(OperatorProfile.user_id == user.id).delete(synchronize_session=False)
    db.query(User).filter(User.id == user.id).delete(synchronize_session=False)
    db.commit()
