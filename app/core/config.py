from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "KaamSetu API"
    app_env: str = "development"
    backend_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:3000"
    database_url: str = "sqlite:///./kaamsetu.db"
    google_client_id: str = "demo-client-id"
    google_client_secret: str = "demo-client-secret"
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"
    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7
    map_geocoder_provider: str = "nominatim"
    nominatim_base_url: str = "https://nominatim.openstreetmap.org"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
