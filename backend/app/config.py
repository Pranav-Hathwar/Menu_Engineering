"""Application settings loaded from environment variables and backend/.env."""

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Substrings that betray a placeholder/example secret left in by mistake.
_WEAK_SECRET_MARKERS = (
    "replace",
    "change-this",
    "changeme",
    "your-secret",
    "placeholder",
    "example",
)


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    APP_NAME: str = "MenuMind Pro"
    DEBUG: bool = False
    AUTO_CREATE_TABLES: bool = True
    MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024
    LOGIN_MAX_ATTEMPTS: int = 5
    LOGIN_LOCKOUT_SECONDS: int = 300
    # Comma-separated list of allowed browser origins for CORS.
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @field_validator("DEBUG", "AUTO_CREATE_TABLES", mode="before")
    @classmethod
    def parse_boolish(cls, value):
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"1", "true", "yes", "on", "dev", "debug"}:
                return True
            if normalized in {"0", "false", "no", "off", "prod", "production", "release"}:
                return False
        return value

    @model_validator(mode="after")
    def _reject_weak_secret_in_prod(self):
        """Fail fast rather than deploy with a guessable JWT secret.

        Only enforced when DEBUG is off so local dev stays frictionless.
        """
        if not self.DEBUG:
            low = (self.SECRET_KEY or "").lower()
            if len(self.SECRET_KEY or "") < 32 or any(marker in low for marker in _WEAK_SECRET_MARKERS):
                raise ValueError(
                    "SECRET_KEY looks weak or is a placeholder. With DEBUG off, set a strong "
                    "random SECRET_KEY of at least 32 characters (e.g. `python -c \"import secrets; "
                    "print(secrets.token_urlsafe(48))\"`)."
                )
        return self


settings = Settings()
