from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.bookings.models import Booking
from app.common.enums import BookingStatus
from app.profiles.models import EmployerProfile, WorkerProfile
from app.reviews.models import Review
from app.reviews.schemas import ReviewCreate
from app.users.models import User


def create_review(db: Session, user: User, payload: ReviewCreate) -> Review:
    booking = db.get(Booking, payload.booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != BookingStatus.completed:
        raise HTTPException(status_code=400, detail="Only completed bookings can be reviewed")
    if user.id == payload.reviewee_user_id:
        raise HTTPException(status_code=400, detail="A user cannot review themselves")
    valid_reviewer = booking.employer_user_id == user.id or (
        user.worker_profile and booking.worker_id == user.worker_profile.id
    )
    if not valid_reviewer:
        raise HTTPException(status_code=403, detail="Review not allowed")
    reviewee = db.get(User, payload.reviewee_user_id)
    if not reviewee:
        raise HTTPException(status_code=404, detail="Reviewee not found")
    review = Review(**payload.model_dump(), reviewer_user_id=user.id)
    db.add(review)
    db.commit()
    db.refresh(review)
    update_rating_aggregate(db, reviewee)
    return review


def update_rating_aggregate(db: Session, reviewee: User):
    reviews = db.query(Review).filter(Review.reviewee_user_id == reviewee.id).all()
    avg_rating = round(sum(review.rating for review in reviews) / len(reviews), 2) if reviews else 0
    if reviewee.worker_profile:
        reviewee.worker_profile.average_rating = avg_rating
        reviewee.worker_profile.total_reviews = len(reviews)
    elif reviewee.employer_profile:
        reviewee.employer_profile.average_rating = avg_rating
        reviewee.employer_profile.total_reviews = len(reviews)
    db.commit()
