from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base, TimestampMixin, UUIDMixin


class SavedWorker(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "saved_workers"

    contractor_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    worker_id: Mapped[str] = mapped_column(ForeignKey("worker_profiles.id"), index=True)
    group_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
