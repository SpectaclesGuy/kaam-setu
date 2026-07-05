from sqlalchemy.orm import Session

from app.common.enums import UserRole
from app.profiles.models import (
    ContractorProfile,
    EmployerProfile,
    OperatorProfile,
    WorkerAvailability,
    WorkerLanguage,
    WorkerProfile,
    WorkerSkill,
)
from app.profiles.schemas import RoleSetupRequest, WorkerAvailabilityCreate
from app.users.models import User


def setup_role_profile(db: Session, user: User, payload: RoleSetupRequest) -> User:
    user.role = payload.role
    if payload.role == UserRole.worker and payload.worker_profile:
        profile_data = payload.worker_profile
        worker = user.worker_profile or WorkerProfile(user_id=user.id)
        worker.phone_number = profile_data.phone_number
        worker.gender = profile_data.gender
        worker.profile_photo_url = profile_data.profile_photo_url
        worker.location_text = profile_data.primary_location
        worker.latitude = profile_data.latitude
        worker.longitude = profile_data.longitude
        worker.service_radius_km = profile_data.service_radius_km
        worker.experience_years = profile_data.experience_years
        worker.daily_rate = profile_data.daily_rate
        worker.hourly_rate = profile_data.hourly_rate
        worker.bio = profile_data.bio
        worker.available_today = profile_data.available_today
        worker.emergency_available = profile_data.emergency_available
        worker.skills = [WorkerSkill(skill_name=skill) for skill in profile_data.skills]
        worker.languages = [WorkerLanguage(language=language) for language in profile_data.languages]
        db.add(worker)
        user.full_name = profile_data.full_name
        user.profile_picture_url = profile_data.profile_photo_url
    elif payload.role == UserRole.employer and payload.employer_profile:
        profile_data = payload.employer_profile
        employer = user.employer_profile or EmployerProfile(user_id=user.id)
        employer.phone_number = profile_data.phone_number
        employer.employer_type = profile_data.employer_type.value
        employer.organization_name = profile_data.organization_name
        employer.location_text = profile_data.location
        employer.latitude = profile_data.latitude
        employer.longitude = profile_data.longitude
        db.add(employer)
        user.full_name = profile_data.full_name
    elif payload.role == UserRole.contractor and payload.contractor_profile:
        profile_data = payload.contractor_profile
        contractor = user.contractor_profile or ContractorProfile(user_id=user.id)
        contractor.phone_number = profile_data.phone_number
        contractor.company_name = profile_data.company_name
        contractor.latitude = profile_data.latitude
        contractor.longitude = profile_data.longitude
        contractor.location_text = profile_data.location
        contractor.bulk_hiring_enabled = profile_data.bulk_hiring_enabled
        contractor.work_categories = ",".join(profile_data.work_categories)
        contractor.frequent_locations = ",".join(profile_data.frequent_locations)
        db.add(contractor)
        user.full_name = profile_data.full_name
    elif payload.role == UserRole.operator and payload.operator_profile:
        profile_data = payload.operator_profile
        operator = user.operator_profile or OperatorProfile(user_id=user.id)
        operator.phone_number = profile_data.phone_number
        operator.assigned_area = profile_data.assigned_area
        operator.latitude = profile_data.latitude
        operator.longitude = profile_data.longitude
        operator.can_verify_workers = profile_data.verification_permissions
        db.add(operator)
        user.full_name = profile_data.full_name
    user.profile_completed = True
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def add_worker_availability(db: Session, worker: WorkerProfile, payload: WorkerAvailabilityCreate) -> WorkerAvailability:
    availability = WorkerAvailability(worker_id=worker.id, **payload.model_dump())
    db.add(availability)
    db.commit()
    db.refresh(availability)
    return availability


def update_worker_availability(
    db: Session, worker: WorkerProfile, availability_id: str, payload: WorkerAvailabilityCreate
) -> WorkerAvailability | None:
    availability = (
        db.query(WorkerAvailability)
        .filter(WorkerAvailability.id == availability_id, WorkerAvailability.worker_id == worker.id)
        .first()
    )
    if not availability:
        return None
    for key, value in payload.model_dump().items():
        setattr(availability, key, value)
    db.commit()
    db.refresh(availability)
    return availability
