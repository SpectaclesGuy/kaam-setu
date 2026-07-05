from pydantic import BaseModel, Field

from app.common.enums import BookingStatus


class BookingCreate(BaseModel):
    work_request_id: str | None = None
    worker_id: str
    scheduled_date: str
    scheduled_time: str | None = None
    notes: str | None = None


class BookingStatusUpdate(BaseModel):
    status: BookingStatus
    final_amount: float | None = Field(default=None, ge=0)
