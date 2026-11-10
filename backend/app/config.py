from functools import lru_cache

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Only used when ENVIRONMENT=development and JWT_SECRET is not set.
# The app refuses to start in production with this value (see validator below).
DEV_JWT_SECRET = "local-development-secret-change-before-deployment"


class Settings(BaseSettings):
    environment: str = "development"
    database_url: str = "sqlite:///./farm_records.db"
    jwt_secret: str = DEV_JWT_SECRET
    access_token_minutes: int = 720
    frontend_origin: str = "http://localhost:5173"
    # Optional comma-separated list of additional allowed origins, e.g.
    # FRONTEND_ORIGINS="https://app.example.com,https://admin.example.com"
    frontend_origins: str = ""
    # Auth rate limits (sliding window, per client IP + email).
    login_rate_limit_attempts: int = 10
    register_rate_limit_attempts: int = 5
    auth_rate_limit_window_seconds: int = 60

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @model_validator(mode="after")
    def _reject_insecure_production_secret(self) -> "Settings":
        if self.environment.lower() == "production":
            if self.jwt_secret == DEV_JWT_SECRET or len(self.jwt_secret) < 32:
                raise ValueError(
                    "JWT_SECRET must be set to a random value of at least 32 "
                    "characters when ENVIRONMENT=production. Generate one with: "
                    "python -c \"import secrets; print(secrets.token_urlsafe(48))\""
                )
        return self

    @property
    def cors_origins(self) -> list[str]:
        origins = [self.frontend_origin.strip()]
        for extra in self.frontend_origins.split(","):
            extra = extra.strip()
            if extra and extra not in origins:
                origins.append(extra)
        return origins


@lru_cache
def get_settings() -> Settings:
    return Settings()
