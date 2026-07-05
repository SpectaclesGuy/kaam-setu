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
