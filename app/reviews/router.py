from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.utils import api_response
from app.core.dependencies import get_current_user, get_db
from app.reviews.models import Review
from app.reviews.schemas import ReviewCreate
from app.reviews.service import create_review

router = APIRouter(prefix="/reviews", tags=["reviews"])


def serialize_review(item: Review):
    return {
        "id": item.id,
        "booking_id": item.booking_id,
        "reviewer_user_id": item.reviewer_user_id,
        "reviewee_user_id": item.reviewee_user_id,
        "rating": item.rating,
        "comment": item.comment,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.post("")
def create_review_endpoint(payload: ReviewCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    review = create_review(db, user, payload)
    return api_response("Review created", serialize_review(review))


@router.get("/worker/{worker_id}")
def reviews_for_worker(worker_id: str, db: Session = Depends(get_db)):
    items = db.query(Review).all()
    return api_response("Worker reviews fetched", [serialize_review(item) for item in items])


@router.get("/user/{user_id}")
def reviews_for_user(user_id: str, db: Session = Depends(get_db)):
    items = db.query(Review).filter(Review.reviewee_user_id == user_id).all()
    return api_response("User reviews fetched", [serialize_review(item) for item in items])
