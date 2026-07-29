from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.common.enums import UserRole


class UserRead(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    profile_picture_url: str | None
    role: UserRole | None
    phone_number: str | None
    is_phone_verified: bool
    phone_verified_at: datetime | None
    is_active: bool
    is_verified_user: bool
    profile_completed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
