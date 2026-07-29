from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class OTPStartRequest(BaseModel):
    channel: Literal["email", "phone"]
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, min_length=8, max_length=20)


class OTPVerifyRequest(BaseModel):
    channel: Literal["email", "phone"]
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, min_length=8, max_length=20)
    code: str = Field(min_length=4, max_length=10)
