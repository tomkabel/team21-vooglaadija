import os
import warnings
from pathlib import Path
from typing import Any

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = ""
    secret_key: str = ""
    redis_url: str = "redis://localhost:6379"
    cors_origins: str = "http://localhost:3000"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    file_expire_hours: int = 24
    storage_path: str = "./storage"
    bcrypt_rounds: int = 12

    # Used to construct DATABASE_URL if not set directly
    db_user: str = "postgres"
    db_password: str = ""
    db_name: str = "ytprocessor"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_and_construct(self) -> "Settings":
        # TESTING override — skip all validation
        testing_env = os.environ.get("TESTING", "").strip().lower()
        if testing_env in ("1", "true", "yes", "y", "on"):
            if not self.database_url.strip():
                self.database_url = "sqlite+aiosqlite:///:memory:"
            return self

        # Construct DATABASE_URL from components if not set directly
        if not self.database_url.strip():
            if not self.db_password.strip():
                raise ValueError(
                    "Either DATABASE_URL or DB_PASSWORD must be set. "
                    "For Docker: set DB_PASSWORD in .env. "
                    "For local dev: set DATABASE_URL in .env."
                )
            from sqlalchemy.engine import URL as SA_URL

            db_url = SA_URL.create(
                drivername="postgresql+asyncpg",
                username=self.db_user,
                password=self.db_password,
                host="localhost",
                port=5432,
                database=self.db_name,
            )
            self.database_url = db_url.render_as_string(hide_password=False)

        # Validate SECRET_KEY
        if not self.secret_key.strip():
            raise ValueError(
                "SECRET_KEY is required. "
                'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
            )

        secret_key_stripped = self.secret_key.strip()
        weak_defaults = (
            "change-me",
            "change-this-secret-key",
            "change-this-secret-key-for-testing-only-min-32-chars",
            "change-this-secret-key-for-local-dev-only-not-secure-32chars",
        )
        if secret_key_stripped in weak_defaults:
            raise ValueError(
                "SECRET_KEY must be changed from default value. "
                'Generate a secure key with: python -c "import secrets; print(secrets.token_hex(32))"'
            )
        if len(secret_key_stripped) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters for security")

        # Warn on wildcard CORS
        if self.cors_origins == "*":
            warnings.warn(
                "CORS_ORIGINS is set to '*', allowing all origins. "
                "This is insecure for production.",
                stacklevel=2,
            )

        # Resolve storage path to absolute
        self.storage_path = str(Path(self.storage_path).resolve())

        return self


# Lazy initialization: Settings instance is created on first access, not at import time
class _SettingsHolder:
    """Singleton holder for Settings instance."""

    _instance: Settings | None = None

    @classmethod
    def get(cls) -> Settings:
        if cls._instance is None:
            cls._instance = Settings()
        return cls._instance

    @classmethod
    def reload(cls) -> Settings:
        """Force reload settings (useful for testing)."""
        cls._instance = Settings()
        return cls._instance


def get_settings() -> Settings:
    """Get the singleton Settings instance, creating it on first call.

    This enables lazy initialization so that importing config doesn't fail
    when environment variables are missing.
    """
    return _SettingsHolder.get()


def reload_settings() -> Settings:
    """Force reload settings (useful for testing)."""
    return _SettingsHolder.reload()


class _SettingsProxy:
    """Lazy proxy for settings that initializes on first attribute access.

    This allows `from app.config import settings` to work without triggering
    validation at import time. Validation occurs only when settings attributes
    are actually accessed.
    """

    def __init__(self) -> None:
        self._instance: Settings | None = None

    def _get_instance(self) -> Settings:
        if self._instance is None:
            self._instance = Settings()
        return self._instance

    def __getattr__(self, name: str) -> Any:
        return getattr(self._get_instance(), name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            setattr(self._get_instance(), name, value)


# For backward compatibility: import settings from app.config works seamlessly
settings = _SettingsProxy()
