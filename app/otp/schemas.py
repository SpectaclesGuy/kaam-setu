from pydantic import BaseModel, Field


class OTPStartRequest(BaseModel):
    phone_number: str = Field(min_length=8, max_length=20)


class OTPVerifyRequest(BaseModel):
    phone_number: str = Field(min_length=8, max_length=20)
    code: str = Field(min_length=4, max_length=10)
