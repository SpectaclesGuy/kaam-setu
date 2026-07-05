from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.common.utils import api_response, haversine_distance_km
from app.core.dependencies import get_current_user, get_db
from app.profiles.schemas import WorkerAvailabilityCreate
from app.profiles.service import add_worker_availability, update_worker_availability
from app.workers.service import get_worker_or_404, get_worker_reviews, list_categories, search_workers

router = APIRouter(tags=["workers"])


@router.get("/categories")
def categories(db: Session = Depends(get_db)):
    data = [{"id": item.id, "name": item.name, "slug": item.slug, "icon_url": item.icon_url} for item in list_categories(db)]
    return api_response("Categories fetched", data)


@router.get("/workers/search")
def worker_search(
    lat: float | None = None,
    lng: float | None = None,
    radius_km: float = Query(default=10, ge=1, le=100),
    category: str | None = None,
    skill_keyword: str | None = None,
    available_today: bool | None = None,
    verified: bool | None = True,
    min_rating: float | None = Query(default=None, ge=0, le=5),
    emergency_available: bool | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
):
    return api_response(
        "Workers fetched",
        search_workers(
            db,
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            category=category,
            skill_keyword=skill_keyword,
            available_today=available_today,
            verified=verified,
            min_rating=min_rating,
            emergency_available=emergency_available,
            min_price=min_price,
            max_price=max_price,
        ),
    )


@router.get("/workers/nearby")
def nearby_workers(
    lat: float,
    lng: float,
    radius_km: float = Query(default=10, ge=1, le=100),
    category: str | None = None,
    available_today: bool | None = None,
    verified: bool | None = True,
    min_rating: float | None = Query(default=None, ge=0, le=5),
    db: Session = Depends(get_db),
):
    return api_response(
        "Nearby workers fetched",
        search_workers(
            db,
            lat=lat,
            lng=lng,
            radius_km=radius_km,
            category=category,
            available_today=available_today,
            verified=verified,
            min_rating=min_rating,
        ),
    )


@router.get("/workers/map-markers")
def map_markers(lat: float, lng: float, radius_km: float = 10, category: str | None = None, db: Session = Depends(get_db)):
    workers = search_workers(db, lat=lat, lng=lng, radius_km=radius_km, category=category)
    markers = [
        {
            "worker_id": worker["worker_id"],
            "name": worker["full_name"],
            "lat": worker["latitude"],
            "lng": worker["longitude"],
            "distance_km": worker["distance_km"],
        }
        for worker in workers
    ]
    return api_response("Map markers fetched", markers)


@router.get("/workers/{worker_id}")
def get_worker(worker_id: str, db: Session = Depends(get_db)):
    worker = get_worker_or_404(db, worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return api_response(
        "Worker fetched",
        {
            "id": worker.id,
            "user_id": worker.user_id,
            "full_name": worker.user.full_name,
            "skills": [skill.skill_name for skill in worker.skills],
            "languages": [language.language for language in worker.languages],
            "location_text": worker.location_text,
            "latitude": worker.latitude,
            "longitude": worker.longitude,
            "service_radius_km": worker.service_radius_km,
            "average_rating": worker.average_rating,
            "total_reviews": worker.total_reviews,
            "verification_status": worker.verification_status.value,
            "available_today": worker.available_today,
            "daily_rate": float(worker.daily_rate),
            "bio": worker.bio,
            "profile_photo_url": worker.profile_photo_url,
        },
    )


@router.get("/workers/{worker_id}/reviews")
def worker_reviews(worker_id: str, db: Session = Depends(get_db)):
    reviews = get_worker_reviews(db, worker_id)
    data = [
        {
            "id": review.id,
            "booking_id": review.booking_id,
            "reviewer_user_id": review.reviewer_user_id,
            "reviewee_user_id": review.reviewee_user_id,
            "rating": review.rating,
            "comment": review.comment,
            "created_at": review.created_at.isoformat() if review.created_at else None,
        }
        for review in reviews
    ]
    return api_response("Worker reviews fetched", data)


@router.get("/workers/{worker_id}/distance")
def worker_distance(worker_id: str, lat: float, lng: float, db: Session = Depends(get_db)):
    worker = get_worker_or_404(db, worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    return api_response(
        "Distance calculated",
        {"distance_km": haversine_distance_km(lat, lng, worker.latitude, worker.longitude)},
    )


@router.get("/workers/{worker_id}/availability")
def worker_availability(worker_id: str, db: Session = Depends(get_db)):
    worker = get_worker_or_404(db, worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="Worker not found")
    data = [
        {"id": item.id, "date": item.date, "status": item.status, "emergency_available": item.emergency_available}
        for item in worker.availability
    ]
    return api_response("Worker availability fetched", data)


@router.post("/workers/me/availability")
def create_my_availability(
    payload: WorkerAvailabilityCreate, user=Depends(get_current_user), db: Session = Depends(get_db)
):
    if user.role != UserRole.worker or not user.worker_profile:
        raise HTTPException(status_code=403, detail="Worker access required")
    availability = add_worker_availability(db, user.worker_profile, payload)
    return api_response("Availability added", {"id": availability.id})


@router.patch("/workers/me/availability/{availability_id}")
def patch_my_availability(
    availability_id: str, payload: WorkerAvailabilityCreate, user=Depends(get_current_user), db: Session = Depends(get_db)
):
    if user.role != UserRole.worker or not user.worker_profile:
        raise HTTPException(status_code=403, detail="Worker access required")
    availability = update_worker_availability(db, user.worker_profile, availability_id, payload)
    if not availability:
        raise HTTPException(status_code=404, detail="Availability not found")
    return api_response("Availability updated", {"id": availability.id})


@router.post("/workers/me/emergency-availability")
def toggle_emergency_availability(
    enabled: bool = True, user=Depends(get_current_user), db: Session = Depends(get_db)
):
    if user.role != UserRole.worker or not user.worker_profile:
        raise HTTPException(status_code=403, detail="Worker access required")
    user.worker_profile.emergency_available = enabled
    db.commit()
    return api_response("Emergency availability updated", {"enabled": enabled})
