from sqlalchemy import Enum, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import ApplicationStatus, WorkRequestStatus, WorkUrgency
from app.core.database import Base, TimestampMixin, UUIDMixin


class WorkRequest(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "work_requests"

    posted_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    category_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    location_text: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    date_required: Mapped[str] = mapped_column(String(20))
    urgency: Mapped[WorkUrgency] = mapped_column(Enum(WorkUrgency), default=WorkUrgency.normal)
    budget_min: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    budget_max: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    workers_needed: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[WorkRequestStatus] = mapped_column(Enum(WorkRequestStatus), default=WorkRequestStatus.open)


class WorkRequestApplication(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "work_request_applications"

    work_request_id: Mapped[str] = mapped_column(ForeignKey("work_requests.id"), index=True)
    worker_id: Mapped[str] = mapped_column(ForeignKey("worker_profiles.id"), index=True)
    status: Mapped[ApplicationStatus] = mapped_column(Enum(ApplicationStatus), default=ApplicationStatus.pending)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)
