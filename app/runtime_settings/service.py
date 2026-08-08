from sqlalchemy.orm import Session

from app.core.config import settings
from app.runtime_settings.models import AppSetting

PROFILE_REQUIRE_EMAIL_KEY = "profile_setup_require_email_verification"
PROFILE_REQUIRE_PHONE_KEY = "profile_setup_require_phone_verification"
WORK_REQUEST_REQUIRE_PHONE_KEY = "work_request_require_phone_verification"


def _read_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_runtime_settings(db: Session) -> dict[str, bool]:
    rows = db.query(AppSetting).filter(
        AppSetting.key.in_([PROFILE_REQUIRE_EMAIL_KEY, PROFILE_REQUIRE_PHONE_KEY, WORK_REQUEST_REQUIRE_PHONE_KEY])
    ).all()
    mapped = {row.key: row.value for row in rows}
    return {
        "profile_setup_require_email_verification": _read_bool(
            mapped.get(PROFILE_REQUIRE_EMAIL_KEY), settings.profile_setup_require_email_verification
        ),
        "profile_setup_require_phone_verification": _read_bool(
            mapped.get(PROFILE_REQUIRE_PHONE_KEY), settings.profile_setup_require_phone_verification
        ),
        "work_request_require_phone_verification": _read_bool(
            mapped.get(WORK_REQUEST_REQUIRE_PHONE_KEY), settings.work_request_require_phone_verification
        ),
    }


def set_runtime_settings(
    db: Session,
    *,
    profile_setup_require_email_verification: bool,
    profile_setup_require_phone_verification: bool,
    work_request_require_phone_verification: bool,
) -> dict[str, bool]:
    updates = {
        PROFILE_REQUIRE_EMAIL_KEY: str(profile_setup_require_email_verification).lower(),
        PROFILE_REQUIRE_PHONE_KEY: str(profile_setup_require_phone_verification).lower(),
        WORK_REQUEST_REQUIRE_PHONE_KEY: str(work_request_require_phone_verification).lower(),
    }
    for key, value in updates.items():
        row = db.get(AppSetting, key)
        if not row:
            row = AppSetting(key=key, value=value)
        else:
            row.value = value
        db.add(row)
    db.commit()
    return get_runtime_settings(db)


def get_public_client_config(db: Session) -> dict:
    runtime = get_runtime_settings(db)
    return {
        "maps_provider": "google" if settings.google_maps_api_key else "openstreetmap",
        "google_maps_api_key": settings.google_maps_api_key,
        "cloudinary_cloud_name": settings.cloudinary_cloud_name,
        "cloudinary_upload_preset": settings.cloudinary_upload_preset,
        "cloudinary_folder": settings.cloudinary_folder,
        "profile_setup_require_email_verification": runtime["profile_setup_require_email_verification"],
        "profile_setup_require_phone_verification": runtime["profile_setup_require_phone_verification"],
        "work_request_require_phone_verification": runtime["work_request_require_phone_verification"],
    }
