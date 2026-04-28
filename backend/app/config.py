"""Application settings loaded from environment variables and backend/.env."""

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


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

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

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


settings = Settings()
