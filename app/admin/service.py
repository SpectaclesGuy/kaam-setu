from sqlalchemy import func
from sqlalchemy.orm import Session

from app.bookings.models import Booking
from app.common.enums import BookingStatus, UserRole, WorkRequestStatus
from app.disputes.models import Dispute
from app.profiles.models import Category, EmployerProfile, WorkerProfile
from app.users.models import User
from app.verification.models import VerificationDocument
from app.work_requests.models import WorkRequest


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
