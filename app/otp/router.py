from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.common.utils import api_response
from app.core.config import settings
from app.core.dependencies import get_current_user, get_db
from app.otp.schemas import OTPStartRequest, OTPVerifyRequest
from app.otp.service import SIGNUP_EMAIL_PURPOSE, SIGNUP_PHONE_PURPOSE, create_or_refresh_challenge, verify_challenge

router = APIRouter(prefix="/auth/otp", tags=["otp"])


@router.post("/send")
def send_signup_otp(payload: OTPStartRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.channel == "email":
        destination = (payload.email or user.email).strip().lower()
        if destination != user.email.strip().lower():
            raise HTTPException(status_code=400, detail="OTP can only be sent to your signed-in email")
        challenge = create_or_refresh_challenge(
            db,
            user=user,
            booking=None,
            destination=destination,
            purpose=SIGNUP_EMAIL_PURPOSE,
            channel="email",
        )
        return api_response(
            "Verification code sent",
            {
                "channel": "email",
                "email": challenge.phone_number,
                "expires_in_seconds": settings.otp_ttl_seconds,
                "test_code": challenge.verification_code if challenge.provider == "mock" else None,
            },
        )

    if not payload.phone_number:
        raise HTTPException(status_code=400, detail="Phone number is required")
    destination = payload.phone_number.strip()
    challenge = create_or_refresh_challenge(
        db,
        user=user,
        booking=None,
        destination=destination,
        purpose=SIGNUP_PHONE_PURPOSE,
        channel="phone",
    )
    return api_response(
        "Verification code sent",
        {
            "channel": "phone",
            "phone_number": challenge.phone_number,
            "expires_in_seconds": settings.otp_ttl_seconds,
            "test_code": challenge.verification_code if challenge.provider == "mock" else None,
        },
    )


@router.post("/verify")
def verify_signup_otp(payload: OTPVerifyRequest, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if payload.channel == "email":
        destination = (payload.email or user.email).strip().lower()
        if destination != user.email.strip().lower():
            raise HTTPException(status_code=400, detail="OTP can only be verified for your signed-in email")
        challenge = verify_challenge(
            db,
            user=user,
            booking=None,
            destination=destination,
            code=payload.code,
            purpose=SIGNUP_EMAIL_PURPOSE,
            channel="email",
        )
        user.is_verified_user = True
        db.add(user)
        db.commit()
        db.refresh(user)
        return api_response(
            "Email verified",
            {
                "channel": "email",
                "email": user.email,
                "is_verified_user": user.is_verified_user,
                "verified_at": challenge.verified_at.isoformat() if challenge.verified_at else None,
            },
        )

    if not payload.phone_number:
        raise HTTPException(status_code=400, detail="Phone number is required")
    destination = payload.phone_number.strip()
    challenge = verify_challenge(
        db,
        user=user,
        booking=None,
        destination=destination,
        code=payload.code,
        purpose=SIGNUP_PHONE_PURPOSE,
        channel="phone",
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
            "channel": "phone",
            "phone_number": user.phone_number,
            "is_phone_verified": user.is_phone_verified,
            "phone_verified_at": user.phone_verified_at.isoformat() if user.phone_verified_at else None,
        },
    )
