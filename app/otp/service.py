from datetime import datetime, timedelta, timezone
from secrets import randbelow

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.bookings.models import Booking
from app.core.config import settings
from app.otp.models import OTPChallenge
from app.users.models import User


SIGNUP_PURPOSE = "signup"
BOOKING_START_PURPOSE = "booking_start"


def normalize_phone_number(phone_number: str) -> str:
    normalized = "".join(char for char in phone_number.strip() if char.isdigit() or char == "+")
    if not normalized.startswith("+"):
        raise HTTPException(status_code=400, detail="Phone number must include country code, for example +919999999999")
    return normalized


def generate_mock_code() -> str:
    return "".join(str(randbelow(10)) for _ in range(settings.otp_code_length))


def get_active_challenge(
    db: Session, *, user_id: str | None, booking_id: str | None, phone_number: str, purpose: str
) -> OTPChallenge | None:
    now = datetime.now(timezone.utc)
    return (
        db.query(OTPChallenge)
        .filter(
            OTPChallenge.user_id == user_id,
            OTPChallenge.booking_id == booking_id,
            OTPChallenge.phone_number == phone_number,
            OTPChallenge.purpose == purpose,
            OTPChallenge.is_used.is_(False),
            OTPChallenge.expires_at > now,
        )
        .order_by(OTPChallenge.created_at.desc())
        .first()
    )


def send_via_twilio_verify(phone_number: str) -> str:
    if not settings.twilio_account_sid or not settings.twilio_auth_token or not settings.twilio_verify_service_sid:
        raise HTTPException(status_code=500, detail="Twilio Verify is not configured")
    response = httpx.post(
        f"https://verify.twilio.com/v2/Services/{settings.twilio_verify_service_sid}/Verifications",
        auth=(settings.twilio_account_sid, settings.twilio_auth_token),
        data={"To": phone_number, "Channel": "sms"},
        timeout=20.0,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("sid") or phone_number


def verify_via_twilio(phone_number: str, code: str) -> bool:
    response = httpx.post(
        f"https://verify.twilio.com/v2/Services/{settings.twilio_verify_service_sid}/VerificationCheck",
        auth=(settings.twilio_account_sid, settings.twilio_auth_token),
        data={"To": phone_number, "Code": code},
        timeout=20.0,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("status") == "approved"


def create_or_refresh_challenge(
    db: Session,
    *,
    user: User | None,
    booking: Booking | None,
    phone_number: str,
    purpose: str,
) -> OTPChallenge:
    phone_number = normalize_phone_number(phone_number)
    now = datetime.now(timezone.utc)
    existing = get_active_challenge(
        db,
        user_id=user.id if user else None,
        booking_id=booking.id if booking else None,
        phone_number=phone_number,
        purpose=purpose,
    )
    if existing and (now - existing.last_sent_at) < timedelta(seconds=settings.otp_resend_cooldown_seconds):
        raise HTTPException(status_code=429, detail="Please wait before requesting another code")

    expires_at = now + timedelta(seconds=settings.otp_ttl_seconds)
    provider = settings.otp_provider.lower().strip()
    mock_code = None
    provider_reference = None
    if provider == "twilio_verify":
        provider_reference = send_via_twilio_verify(phone_number)
    else:
        provider = "mock"
        mock_code = settings.otp_test_bypass_code or generate_mock_code()
        provider_reference = "mock"

    challenge = existing or OTPChallenge(
        user_id=user.id if user else None,
        booking_id=booking.id if booking else None,
        phone_number=phone_number,
        purpose=purpose,
    )
    challenge.provider = provider
    challenge.provider_reference = provider_reference
    challenge.verification_code = mock_code
    challenge.expires_at = expires_at
    challenge.last_sent_at = now
    challenge.attempts = 0
    challenge.is_used = False
    challenge.verified_at = None
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge


def verify_challenge(
    db: Session,
    *,
    user: User | None,
    booking: Booking | None,
    phone_number: str,
    code: str,
    purpose: str,
) -> OTPChallenge:
    phone_number = normalize_phone_number(phone_number)
    challenge = get_active_challenge(
        db,
        user_id=user.id if user else None,
        booking_id=booking.id if booking else None,
        phone_number=phone_number,
        purpose=purpose,
    )
    if not challenge:
        raise HTTPException(status_code=404, detail="No active verification was found for this phone number")

    challenge.attempts += 1
    if challenge.attempts > 5:
        db.add(challenge)
        db.commit()
        raise HTTPException(status_code=429, detail="Too many verification attempts")

    if challenge.provider == "twilio_verify":
        approved = verify_via_twilio(phone_number, code)
    else:
        approved = code == challenge.verification_code

    if not approved:
        db.add(challenge)
        db.commit()
        raise HTTPException(status_code=400, detail="Incorrect verification code")

    challenge.is_used = True
    challenge.verified_at = datetime.now(timezone.utc)
    db.add(challenge)
    db.commit()
    db.refresh(challenge)
    return challenge
