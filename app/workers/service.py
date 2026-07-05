from sqlalchemy.orm import Session, joinedload

from app.common.enums import VerificationStatus
from app.common.utils import haversine_distance_km
from app.profiles.models import Category, WorkerProfile
from app.reviews.models import Review


def list_categories(db: Session):
    return db.query(Category).filter(Category.is_active.is_(True)).order_by(Category.name.asc()).all()


def search_workers(
    db: Session,
    *,
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float = 10,
    category: str | None = None,
    skill_keyword: str | None = None,
    available_today: bool | None = None,
    verified: bool | None = True,
    min_rating: float | None = None,
    emergency_available: bool | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
):
    query = db.query(WorkerProfile).options(joinedload(WorkerProfile.user), joinedload(WorkerProfile.skills))
    if available_today is not None:
        query = query.filter(WorkerProfile.available_today == available_today)
    if verified:
        query = query.filter(WorkerProfile.verification_status == VerificationStatus.approved)
    if min_rating is not None:
        query = query.filter(WorkerProfile.average_rating >= min_rating)
    if emergency_available is not None:
        query = query.filter(WorkerProfile.emergency_available == emergency_available)
    if min_price is not None:
        query = query.filter(WorkerProfile.daily_rate >= min_price)
    if max_price is not None:
        query = query.filter(WorkerProfile.daily_rate <= max_price)

    workers = []
    for worker in query.all():
        skills = [skill.skill_name for skill in worker.skills]
        if category and category.lower() not in ",".join(skills).lower():
            continue
        if skill_keyword and skill_keyword.lower() not in ",".join(skills).lower():
            continue
        distance = None
        if lat is not None and lng is not None:
            distance = haversine_distance_km(lat, lng, worker.latitude, worker.longitude)
            if distance > min(radius_km, worker.service_radius_km):
                continue
        workers.append(
            {
                "worker_id": worker.id,
                "user_id": worker.user_id,
                "full_name": worker.user.full_name,
                "skills": skills,
                "latitude": worker.latitude,
                "longitude": worker.longitude,
                "distance_km": distance,
                "average_rating": worker.average_rating,
                "total_reviews": worker.total_reviews,
                "verification_status": worker.verification_status.value,
                "available_today": worker.available_today,
                "daily_rate": float(worker.daily_rate),
                "profile_photo_url": worker.profile_photo_url,
            }
        )
    return sorted(workers, key=lambda item: (item["distance_km"] is None, item["distance_km"] or 0))


def get_worker_or_404(db: Session, worker_id: str) -> WorkerProfile | None:
    return (
        db.query(WorkerProfile)
        .options(joinedload(WorkerProfile.user), joinedload(WorkerProfile.skills), joinedload(WorkerProfile.languages))
        .filter(WorkerProfile.id == worker_id)
        .first()
    )


def get_worker_reviews(db: Session, worker_id: str):
    worker = get_worker_or_404(db, worker_id)
    if not worker:
        return []
    return db.query(Review).filter(Review.reviewee_user_id == worker.user_id).order_by(Review.created_at.desc()).all()
