import warnings

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/ytprocessor"
    secret_key: str = "change-me"
    redis_url: str = "redis://localhost:6379"
    cors_origins: str = "http://localhost:3000"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    file_expire_hours: int = 24
    storage_path: str = "./storage"
    bcrypt_rounds: int = 12

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        """Validate that SECRET_KEY is not the default value."""
        if v == "change-me":
            raise ValueError(
                "SECRET_KEY must be changed from default value. "
                'Generate a secure key with: python -c "import secrets; print(secrets.token_hex(32))"'
            )
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters for security")
        return v

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: str) -> str:
        """Warn if CORS allows all origins."""
        if v == "*":
            warnings.warn(
                "CORS_ORIGINS is set to '*', allowing all origins. "
                "This is insecure for production.",
                stacklevel=2,
            )
        return v

    def __init__(self, **kwargs):
        # If TESTING environment variable is set, use SQLite
        import os

        if os.environ.get("TESTING"):
            kwargs["database_url"] = "sqlite+aiosqlite:///:memory:"
        super().__init__(**kwargs)


settings = Settings()
