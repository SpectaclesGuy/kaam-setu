from pydantic import BaseModel

from app.common.enums import UserRole


class AdminUserUpdate(BaseModel):
    role: UserRole | None = None
    is_active: bool | None = None


class AdminSettingsUpdate(BaseModel):
    profile_setup_require_email_verification: bool
    profile_setup_require_phone_verification: bool
