"""
app/config.py

Loads environment variables using pydantic-settings.
All configuration is pulled from the .env file — never hardcoded.
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    APP_NAME: str = "MenuMind AI"
    DEBUG: bool = True

    class Config:
        env_file = ".env"


# Single instance — import this everywhere you need settings
settings = Settings()
