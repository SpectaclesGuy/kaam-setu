from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import UserRole
from app.core.database import Base, TimestampMixin, UUIDMixin


class User(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "users"

    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255))
    profile_picture_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    role: Mapped[UserRole | None] = mapped_column(Enum(UserRole), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_verified_user: Mapped[bool] = mapped_column(Boolean, default=False)
    profile_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    worker_profile = relationship("WorkerProfile", back_populates="user", uselist=False)
    employer_profile = relationship("EmployerProfile", back_populates="user", uselist=False)
    contractor_profile = relationship("ContractorProfile", back_populates="user", uselist=False)
    operator_profile = relationship("OperatorProfile", back_populates="user", uselist=False)
