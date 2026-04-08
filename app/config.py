import math
import os
import warnings
from pathlib import Path
from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _estimate_entropy(text: str) -> float:
    """Estimate Shannon entropy of a string in bits.

    A truly random hex string has 4 bits per character.
    A truly random alphanumeric string has ~6.5 bits per character.
    We flag anything below 3 bits/char as suspiciously low-entropy.
    """
    if not text:
        return 0.0
    freq: dict[str, int] = {}
    for c in text:
        freq[c] = freq.get(c, 0) + 1
    length = len(text)
    entropy = 0.0
    for count in freq.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


class Settings(BaseSettings):
    database_url: str = ""
    secret_key: str = ""
    redis_url: str = ""
    cors_origins: str = "http://localhost:3000"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    file_expire_hours: int = 24
    storage_path: str = "./storage"
    bcrypt_rounds: int = 12

    # Cookie security — False for local dev (no HTTPS), True for production
    cookie_secure: bool = False

    # Used to construct DATABASE_URL if not set directly
    db_user: str = "postgres"
    db_password: str = ""
    db_name: str = "ytprocessor"
    db_host: str = "localhost"
    db_port: str = "5432"

    # Used to construct REDIS_URL if not set directly
    redis_host: str = "localhost"
    redis_port: str = "6379"
    redis_password: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @model_validator(mode="after")
    def validate_and_construct(self) -> "Settings":
        # TESTING override — skip all validation
        testing_val = os.environ.get("TESTING", "").lower()
        is_testing = testing_val in ("1", "true", "yes", "on")
        if is_testing:
            if not self.database_url:
                self.database_url = "sqlite+aiosqlite:///:memory:"
            return self

        # Construct DATABASE_URL from components if not set directly
        if not self.database_url:
            if not self.db_password:
                raise ValueError(
                    "Either DATABASE_URL or DB_PASSWORD must be set. "
                    "For Docker: set DB_PASSWORD in .env. "
                    "For local dev: set DATABASE_URL in .env."
                )
            encoded_password = quote_plus(self.db_password)
            self.database_url = (
                f"postgresql+asyncpg://{self.db_user}:{encoded_password}"
                f"@{self.db_host}:{self.db_port}/{self.db_name}"
            )

        # Validate SECRET_KEY — reject known weak values
        if not self.secret_key:
            raise ValueError(
                "SECRET_KEY is required. "
                'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
            )

        # Check for low-entropy keys (repetitive patterns, dictionary words, etc.)
        entropy_per_char = _estimate_entropy(self.secret_key)
        if entropy_per_char < 2.9:
            raise ValueError(
                "SECRET_KEY has insufficient entropy "
                f"(~{entropy_per_char:.1f} bits/char, need >= 2.9). "
                'Generate a secure key with: python -c "import secrets; print(secrets.token_hex(32))"'
            )
        if len(self.secret_key) < 32:
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

        # Construct REDIS_URL from components if not set directly
        if not self.redis_url:
            if self.redis_password:
                encoded_password = quote_plus(self.redis_password)
                self.redis_url = f"redis://:{encoded_password}@{self.redis_host}:{self.redis_port}"
            else:
                self.redis_url = f"redis://{self.redis_host}:{self.redis_port}"

        return self


settings = Settings()
