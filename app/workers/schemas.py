from datetime import datetime

from pydantic import BaseModel


class WorkerSearchResult(BaseModel):
    worker_id: str
    user_id: str
    full_name: str
    skills: list[str]
    latitude: float
    longitude: float
    distance_km: float | None = None
    average_rating: float
    total_reviews: int
    verification_status: str
    available_today: bool
    daily_rate: float
    profile_photo_url: str | None = None


class ReviewRead(BaseModel):
    id: str
    booking_id: str
    reviewer_user_id: str
    reviewee_user_id: str
    rating: int
    comment: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
