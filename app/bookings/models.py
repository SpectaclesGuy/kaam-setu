from sqlalchemy import Enum, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import BookingStatus
from app.core.database import Base, TimestampMixin, UUIDMixin


class Booking(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "bookings"

    work_request_id: Mapped[str | None] = mapped_column(ForeignKey("work_requests.id"), nullable=True)
    employer_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    worker_id: Mapped[str] = mapped_column(ForeignKey("worker_profiles.id"), index=True)
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus), default=BookingStatus.requested)
    scheduled_date: Mapped[str] = mapped_column(String(20))
    scheduled_time: Mapped[str | None] = mapped_column(String(20), nullable=True)
    final_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
