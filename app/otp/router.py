from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.utils import api_response
from app.core.config import settings
from app.core.dependencies import get_current_user, get_db
from app.otp.schemas import OTPStartRequest, OTPVerifyRequest
from app.otp.service import SIGNUP_PURPOSE, create_or_refresh_challenge, verify_challenge

router = APIRouter(prefix="/auth/otp", tags=["otp"])


@router.post("/send")
def send_signup_otp(payload: OTPStartRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    challenge = create_or_refresh_challenge(db, user=user, booking=None, phone_number=payload.phone_number, purpose=SIGNUP_PURPOSE)
    return api_response(
        "Verification code sent",
        {
            "phone_number": challenge.phone_number,
            "purpose": challenge.purpose,
            "expires_in_seconds": settings.otp_ttl_seconds,
            "test_code": challenge.verification_code if challenge.provider == "mock" else None,
        },
    )


@router.post("/verify")
def verify_signup_otp(payload: OTPVerifyRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    challenge = verify_challenge(
        db,
        user=user,
        booking=None,
        phone_number=payload.phone_number,
        code=payload.code,
        purpose=SIGNUP_PURPOSE,
    )
    user.phone_number = challenge.phone_number
    user.is_phone_verified = True
    user.phone_verified_at = challenge.verified_at
    db.add(user)
    db.commit()
    db.refresh(user)
    return api_response(
        "Phone number verified",
        {
            "phone_number": user.phone_number,
            "is_phone_verified": user.is_phone_verified,
            "phone_verified_at": user.phone_verified_at.isoformat() if user.phone_verified_at else None,
        },
    )
