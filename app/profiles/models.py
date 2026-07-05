from sqlalchemy import Boolean, Enum, Float, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import VerificationStatus
from app.core.database import Base, TimestampMixin, UUIDMixin


class WorkerProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "worker_profiles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(20))
    gender: Mapped[str | None] = mapped_column(String(50), nullable=True)
    profile_photo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    location_text: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    service_radius_km: Mapped[float] = mapped_column(Float, default=10)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    daily_rate: Mapped[float] = mapped_column(Numeric(10, 2))
    hourly_rate: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    available_today: Mapped[bool] = mapped_column(Boolean, default=False)
    emergency_available: Mapped[bool] = mapped_column(Boolean, default=False)
    verification_status: Mapped[VerificationStatus] = mapped_column(
        Enum(VerificationStatus), default=VerificationStatus.pending
    )
    average_rating: Mapped[float] = mapped_column(Float, default=0)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)
    completed_jobs: Mapped[int] = mapped_column(Integer, default=0)

    user = relationship("User", back_populates="worker_profile")
    skills = relationship("WorkerSkill", back_populates="worker", cascade="all, delete-orphan")
    languages = relationship("WorkerLanguage", back_populates="worker", cascade="all, delete-orphan")
    availability = relationship("WorkerAvailability", back_populates="worker", cascade="all, delete-orphan")


class EmployerProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "employer_profiles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(20))
    employer_type: Mapped[str] = mapped_column(String(50))
    organization_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    location_text: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    average_rating: Mapped[float] = mapped_column(Float, default=0)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)

    user = relationship("User", back_populates="employer_profile")


class ContractorProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "contractor_profiles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(20))
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    location_text: Mapped[str] = mapped_column(String(255))
    bulk_hiring_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    average_rating: Mapped[float] = mapped_column(Float, default=0)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)
    work_categories: Mapped[str | None] = mapped_column(Text, nullable=True)
    frequent_locations: Mapped[str | None] = mapped_column(Text, nullable=True)

    user = relationship("User", back_populates="contractor_profile")


class OperatorProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "operator_profiles"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(20))
    assigned_area: Mapped[str] = mapped_column(String(255))
    latitude: Mapped[float] = mapped_column(Float)
    longitude: Mapped[float] = mapped_column(Float)
    can_verify_workers: Mapped[bool] = mapped_column(Boolean, default=False)

    user = relationship("User", back_populates="operator_profile")


class Category(UUIDMixin, Base):
    __tablename__ = "categories"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    icon_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class WorkerSkill(UUIDMixin, Base):
    __tablename__ = "worker_skills"

    worker_id: Mapped[str] = mapped_column(ForeignKey("worker_profiles.id"), index=True)
    category_id: Mapped[str | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    skill_name: Mapped[str] = mapped_column(String(100))
    years_experience: Mapped[int | None] = mapped_column(Integer, nullable=True)

    worker = relationship("WorkerProfile", back_populates="skills")


class WorkerLanguage(UUIDMixin, Base):
    __tablename__ = "worker_languages"

    worker_id: Mapped[str] = mapped_column(ForeignKey("worker_profiles.id"), index=True)
    language: Mapped[str] = mapped_column(String(50))

    worker = relationship("WorkerProfile", back_populates="languages")


class WorkerAvailability(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "worker_availability"

    worker_id: Mapped[str] = mapped_column(ForeignKey("worker_profiles.id"), index=True)
    date: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20))
    emergency_available: Mapped[bool] = mapped_column(Boolean, default=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    worker = relationship("WorkerProfile", back_populates="availability")
