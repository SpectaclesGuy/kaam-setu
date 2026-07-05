from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDMixin


class ContactLog(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "contact_logs"

    employer_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    worker_id: Mapped[str] = mapped_column(ForeignKey("worker_profiles.id"), index=True)
    contact_type: Mapped[str] = mapped_column(String(50))
