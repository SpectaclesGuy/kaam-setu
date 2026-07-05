import httpx
from jose import jwt
from sqlalchemy.orm import Session

from app.auth.schemas import GoogleCallbackPayload
from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.users.models import User


def upsert_google_user(db: Session, payload: GoogleCallbackPayload) -> User:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        user = User(
            google_id=payload.google_id,
            email=payload.email,
            full_name=payload.full_name,
            profile_picture_url=payload.profile_picture_url,
        )
        db.add(user)
    else:
        user.google_id = payload.google_id
        user.full_name = payload.full_name
        user.profile_picture_url = payload.profile_picture_url
    db.commit()
    db.refresh(user)
    return user


def build_auth_payload(user: User) -> dict[str, str]:
    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id),
        "token_type": "bearer",
    }


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])


async def exchange_google_code(code: str) -> GoogleCallbackPayload:
    async with httpx.AsyncClient(timeout=15.0) as client:
        token_response = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.effective_google_redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
        )
        token_response.raise_for_status()
        token_payload = token_response.json()
        access_token = token_payload.get("access_token")
        if not access_token:
            raise ValueError("Google token response did not include an access token")

        userinfo_response = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        userinfo_response.raise_for_status()
        userinfo = userinfo_response.json()
        return GoogleCallbackPayload(
            google_id=userinfo["id"],
            email=userinfo["email"],
            full_name=userinfo.get("name") or userinfo["email"],
            profile_picture_url=userinfo.get("picture"),
        )
