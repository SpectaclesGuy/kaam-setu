from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.schemas import AuthResponse, GoogleCallbackPayload, TokenRefreshRequest
from app.auth.service import build_auth_payload, decode_token, exchange_google_code, upsert_google_user
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
        f"&redirect_uri={settings.effective_google_redirect_uri}"
        "&response_type=code&scope=openid%20email%20profile"
        "&access_type=offline&prompt=consent&state=web"
    )
    return api_response("Google OAuth URL generated", {"authorization_url": redirect})


@router.get("/google/callback")
async def google_callback(
    code: str | None = Query(default=None),
    state: str | None = Query(default=None),
    google_id: str | None = Query(default=None),
    email: str | None = Query(default=None),
    full_name: str | None = Query(default=None),
    profile_picture_url: str | None = Query(default=None),
    redirect: bool | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if code:
        google_payload = await exchange_google_code(code)
    elif google_id and email and full_name:
        google_payload = GoogleCallbackPayload(
            google_id=google_id,
            email=email,
            full_name=full_name,
            profile_picture_url=profile_picture_url,
        )
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Google OAuth callback data")

    user = upsert_google_user(db, google_payload)
    payload = {**build_auth_payload(user), "user": UserRead.model_validate(user).model_dump()}
    should_redirect = redirect if redirect is not None else state == "web" or bool(code)
    if should_redirect:
        destination = "/profile-setup" if not user.profile_completed else "/find-workers"
        return RedirectResponse(
            url=f"{settings.effective_frontend_url.rstrip('/')}{destination}?token={payload['access_token']}&profile_completed={str(user.profile_completed).lower()}"
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
