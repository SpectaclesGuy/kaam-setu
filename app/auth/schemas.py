from pydantic import BaseModel, EmailStr

from app.users.schemas import UserRead


class GoogleCallbackPayload(BaseModel):
    google_id: str
    email: EmailStr
    full_name: str
    profile_picture_url: str | None = None


class TokenRefreshRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserRead
