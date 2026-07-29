from functools import lru_cache
import json

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "KaramSetu API"
    app_env: str = "development"
    backend_url: str = "http://localhost:8000"
    frontend_url: str | None = None
    database_url: str = "sqlite:///./kaamsetu.db"
    google_client_id: str = "demo-client-id"
    google_client_secret: str = "demo-client-secret"
    google_redirect_uri: str | None = None
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    map_geocoder_provider: str = "nominatim"
    nominatim_base_url: str = "https://nominatim.openstreetmap.org"
    cors_origins_raw: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    otp_provider: str = "mock"
    otp_code_length: int = 6
    otp_ttl_seconds: int = 300
    otp_resend_cooldown_seconds: int = 60
    otp_test_bypass_code: str = "123456"
    email_otp_provider: str = "mock"
    phone_otp_provider: str = "mock"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str | None = None
    smtp_from_name: str = "KaramSetu"
    smtp_use_tls: bool = True
    msg91_auth_key: str | None = None
    msg91_template_id: str | None = None

    @property
    def effective_google_redirect_uri(self) -> str:
        if self.google_redirect_uri:
            return self.google_redirect_uri
        return f"{self.backend_url.rstrip('/')}/auth/google/callback"

    @property
    def effective_frontend_url(self) -> str:
        return self.frontend_url or self.backend_url

    @property
    def cors_origins(self) -> list[str]:
        stripped = self.cors_origins_raw.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            return json.loads(stripped)
        return [item.strip() for item in stripped.split(",") if item.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
