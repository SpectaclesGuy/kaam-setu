from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    booking_id: str
    reviewee_user_id: str
    rating: int = Field(ge=1, le=5)
    comment: str | None = None
