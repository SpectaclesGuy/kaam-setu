from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.common.enums import EmployerType, UserRole


class BaseProfileSchema(BaseModel):
    full_name: str
    phone_number: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class WorkerProfileSetup(BaseProfileSchema):
    gender: str | None = None
    profile_photo_url: str | None = None
    primary_location: str
    service_radius_km: float = Field(default=10, ge=1, le=100)
    skills: list[str]
    categories: list[str] = Field(default_factory=list)
    experience_years: int = Field(default=0, ge=0)
    daily_rate: float = Field(gt=0)
    hourly_rate: float | None = Field(default=None, gt=0)
    languages: list[str] = Field(default_factory=list)
    available_today: bool = False
    emergency_available: bool = False
    bio: str | None = None
    work_gallery_urls: list[str] = Field(default_factory=list)


class EmployerProfileSetup(BaseProfileSchema):
    employer_type: EmployerType
    organization_name: str | None = None
    location: str


class ContractorProfileSetup(BaseProfileSchema):
    company_name: str | None = None
    work_categories: list[str] = Field(default_factory=list)
    frequent_locations: list[str] = Field(default_factory=list)
    bulk_hiring_enabled: bool = False
    location: str


class OperatorProfileSetup(BaseProfileSchema):
    assigned_area: str
    verification_permissions: bool = False


class RoleSetupRequest(BaseModel):
    role: UserRole
    worker_profile: WorkerProfileSetup | None = None
    employer_profile: EmployerProfileSetup | None = None
    contractor_profile: ContractorProfileSetup | None = None
    operator_profile: OperatorProfileSetup | None = None

    @model_validator(mode="after")
    def validate_role_payload(self):
        mapping = {
            UserRole.worker: self.worker_profile,
            UserRole.employer: self.employer_profile,
            UserRole.contractor: self.contractor_profile,
            UserRole.operator: self.operator_profile,
        }
        if self.role == UserRole.admin:
            raise ValueError("Admin role cannot be self-assigned")
        if not mapping.get(self.role):
            raise ValueError("Role-specific profile payload is required")
        return self


class WorkerAvailabilityCreate(BaseModel):
    date: str
    status: Literal["available", "busy", "unavailable"]
    emergency_available: bool = False
    notes: str | None = None
