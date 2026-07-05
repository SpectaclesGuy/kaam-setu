from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.schemas import AuthResponse, GoogleCallbackPayload, TokenRefreshRequest
from app.auth.service import build_auth_payload, decode_token, upsert_google_user
from app.common.utils import api_response
from app.core.config import settings
from app.core.dependencies import get_current_user, get_db
from app.users.schemas import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/google/login")
def google_login():
    redirect = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={settings.google_client_id}"
        f"&redirect_uri={settings.google_redirect_uri}"
        "&response_type=code&scope=openid%20email%20profile"
    )
    return api_response("Google OAuth URL generated", {"authorization_url": redirect})


@router.get("/google/callback")
def google_callback(
    google_id: str = Query(...),
    email: str = Query(...),
    full_name: str = Query(...),
    profile_picture_url: str | None = Query(default=None),
    redirect: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    user = upsert_google_user(
        db,
        GoogleCallbackPayload(
            google_id=google_id,
            email=email,
            full_name=full_name,
            profile_picture_url=profile_picture_url,
        ),
    )
    payload = {**build_auth_payload(user), "user": UserRead.model_validate(user).model_dump()}
    if redirect:
        return RedirectResponse(
            url=f"{settings.frontend_url}?token={payload['access_token']}&profile_completed={user.profile_completed}"
        )
    return api_response("Authentication successful", payload)


@router.post("/logout")
def logout():
    return api_response("Logged out")


@router.get("/me")
def me(user=Depends(get_current_user)):
    return api_response("Authenticated user fetched", UserRead.model_validate(user).model_dump())


@router.post("/refresh")
def refresh_tokens(payload: TokenRefreshRequest):
    decoded = decode_token(payload.refresh_token)
    if decoded.get("type") != "refresh":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid refresh token")
    return api_response(
        "Tokens refreshed",
        {
            "access_token": build_auth_payload(type("TempUser", (), {"id": decoded["sub"]})())["access_token"],
            "refresh_token": payload.refresh_token,
            "token_type": "bearer",
        },
    )
