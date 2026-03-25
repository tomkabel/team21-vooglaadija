from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://user:pass@localhost:5432/ytprocessor"
    secret_key: str = "change-me"
    redis_url: str = "redis://localhost:6379"
    cors_origins: str = "*"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 7
    file_expire_hours: int = 24
    storage_path: str = "./storage"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    def __init__(self, **kwargs):
        # If TESTING environment variable is set, use SQLite
        import os

        if os.environ.get("TESTING"):
            kwargs["database_url"] = "sqlite+aiosqlite:///:memory:"
        super().__init__(**kwargs)


settings = Settings()
