from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.common.enums import DisputeIssueType, DisputeStatus
from app.core.database import Base, TimestampMixin, UUIDMixin


class Dispute(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "disputes"

    booking_id: Mapped[str | None] = mapped_column(ForeignKey("bookings.id"), nullable=True)
    raised_by_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    against_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    issue_type: Mapped[DisputeIssueType] = mapped_column(Enum(DisputeIssueType))
    description: Mapped[str] = mapped_column(Text)
    evidence_urls: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[DisputeStatus] = mapped_column(Enum(DisputeStatus), default=DisputeStatus.open)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
