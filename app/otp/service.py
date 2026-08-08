from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from secrets import randbelow
import smtplib
import ssl

import httpx
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.bookings.models import Booking
from app.core.config import settings
from app.otp.models import OTPChallenge
from app.users.models import User


SIGNUP_EMAIL_PURPOSE = "signup_email"
SIGNUP_PHONE_PURPOSE = "signup_phone"
BOOKING_START_PURPOSE = "booking_start_phone"


def normalize_phone_number(destination: str) -> str:
    normalized = "".join(char for char in destination.strip() if char.isdigit() or char == "+")
    if not normalized.startswith("+"):
        raise HTTPException(status_code=400, detail="Phone number must include country code, for example +919999999999")
    return normalized


def normalize_email_address(destination: str) -> str:
    normalized = destination.strip().lower()
    if "@" not in normalized:
        raise HTTPException(status_code=400, detail="A valid email address is required")
    return normalized


def generate_mock_code() -> str:
    return "".join(str(randbelow(10)) for _ in range(settings.otp_code_length))


def get_active_challenge(
    db: Session, *, user_id: str | None, booking_id: str | None, destination: str, purpose: str
) -> OTPChallenge | None:
    now = datetime.now(timezone.utc)
    return (
        db.query(OTPChallenge)
        .filter(
            OTPChallenge.user_id == user_id,
            OTPChallenge.booking_id == booking_id,
            OTPChallenge.phone_number == destination,
            OTPChallenge.purpose == purpose,
            OTPChallenge.is_used.is_(False),
            OTPChallenge.expires_at > now,
        )
        .order_by(OTPChallenge.created_at.desc())
        .first()
    )


def send_via_smtp_email(destination: str, code: str, purpose: str) -> str:
    if not settings.smtp_username or not settings.smtp_password:
        raise HTTPException(status_code=500, detail="SMTP credentials are not configured")
    sender = settings.smtp_from_email or settings.smtp_username
    message = EmailMessage()
    message["From"] = f"{settings.smtp_from_name} <{sender}>"
    message["To"] = destination
    message["Subject"] = "Your KaramSetu verification code"
    purpose_text = "verify your KaramSetu account" if purpose == SIGNUP_EMAIL_PURPOSE else "verify this action"
    message.set_content(
        f"Your KaramSetu verification code is {code}. Use it within {max(settings.otp_ttl_seconds // 60, 1)} minutes to {purpose_text}."
    )

    try:
        smtp_client = smtplib.SMTP_SSL if settings.smtp_use_ssl else smtplib.SMTP
        with smtp_client(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            if not settings.smtp_use_ssl:
                server.ehlo()
                if settings.smtp_use_tls:
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
            server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
    except smtplib.SMTPAuthenticationError as exc:
        raise HTTPException(
            status_code=502,
            detail="SMTP authentication failed. Check the Gmail address and app password configured for KaramSetu.",
        ) from exc
    except smtplib.SMTPConnectError as exc:
        raise HTTPException(
            status_code=502,
            detail="KaramSetu could not connect to the SMTP server. Check the SMTP host, port, and TLS settings.",
        ) from exc
    except smtplib.SMTPException as exc:
        raise HTTPException(status_code=502, detail=f"SMTP delivery failed: {exc}") from exc
    except OSError as exc:
        raise HTTPException(
            status_code=502,
            detail="KaramSetu could not reach the SMTP server. Check outbound network access and SMTP settings.",
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Email delivery failed unexpectedly: {exc}") from exc
    return destination


def send_via_msg91(destination: str) -> str:
    if not settings.msg91_auth_key or not settings.msg91_template_id:
        raise HTTPException(status_code=500, detail="MSG91 credentials are not configured")
    response = httpx.post(
        "https://control.msg91.com/api/v5/otp",
        params={
            "template_id": settings.msg91_template_id,
            "mobile": destination.lstrip("+"),
            "authkey": settings.msg91_auth_key,
        },
        headers={"Content-Type": "application/json"},
        json={},
        timeout=20.0,
    )
    response.raise_for_status()
    return destination


def verify_via_msg91(destination: str, code: str) -> bool:
    if not settings.msg91_auth_key:
        raise HTTPException(status_code=500, detail="MSG91 credentials are not configured")
    response = httpx.get(
        "https://control.msg91.com/api/v5/otp/verify",
        params={"otp": code, "mobile": destination.lstrip("+")},
        headers={"authkey": settings.msg91_auth_key},
        timeout=20.0,
    )
    response.raise_for_status()
    payload = response.json()
    message = str(payload.get("message", "")).lower()
    result_type = str(payload.get("type", "")).lower()
    return "verified" in message or result_type == "success"


def create_or_refresh_challenge(
    db: Session,
    *,
    user: User | None,
    booking: Booking | None,
    destination: str,
    purpose: str,
    channel: str,
    provider_override: str | None = None,
) -> OTPChallenge:
    destination = normalize_email_address(destination) if channel == "email" else normalize_phone_number(destination)
    now = datetime.now(timezone.utc)
    existing = get_active_challenge(
        db,
        user_id=user.id if user else None,
        booking_id=booking.id if booking else None,
        destination=destination,
        purpose=purpose,
    )
    if existing and (now - existing.last_sent_at) < timedelta(seconds=settings.otp_resend_cooldown_seconds):
        raise HTTPException(status_code=429, detail="Please wait before requesting another code")

    expires_at = now + timedelta(seconds=settings.otp_ttl_seconds)
    provider = (provider_override or (settings.email_otp_provider if channel == "email" else settings.phone_otp_provider)).lower().strip()
    generated_code = settings.otp_test_bypass_code if provider in {"mock", "internal"} else None
    provider_reference = None
    if provider == "internal":
        generated_code = settings.otp_test_bypass_code or generate_mock_code()
        provider_reference = "internal"
    elif channel == "email" and provider == "smtp":
        generated_code = generate_mock_code()
        provider_reference = send_via_smtp_email(destination, generated_code, purpose)
    elif channel == "phone" and provider == "msg91":
        provider_reference = send_via_msg91(destination)
    else:
        provider = "mock"
        generated_code = settings.otp_test_bypass_code or generate_mock_code()
        provider_reference = "mock"

    challenge = existing or OTPChallenge(
        user_id=user.id if user else None,
        booking_id=booking.id if booking else None,
        phone_number=destination,
        purpose=purpose,
    )
    challenge.provider = provider
    challenge.provider_reference = provider_reference
    challenge.verification_code = generated_code
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
    destination: str,
    code: str,
    purpose: str,
    channel: str,
) -> OTPChallenge:
    destination = normalize_email_address(destination) if channel == "email" else normalize_phone_number(destination)
    challenge = get_active_challenge(
        db,
        user_id=user.id if user else None,
        booking_id=booking.id if booking else None,
        destination=destination,
        purpose=purpose,
    )
    if not challenge:
        raise HTTPException(status_code=404, detail="No active verification was found for this phone number")

    challenge.attempts += 1
    if challenge.attempts > 5:
        db.add(challenge)
        db.commit()
        raise HTTPException(status_code=429, detail="Too many verification attempts")

    if channel == "phone" and challenge.provider == "msg91":
        approved = verify_via_msg91(destination, code)
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
