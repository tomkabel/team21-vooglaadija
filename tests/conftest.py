import asyncio
import os
import sys

# CRITICAL: Set environment variables BEFORE any other imports
os.environ["TESTING"] = "1"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-not-for-production-use-32chars"

# Force reconfigure the database URL before any app imports
# This ensures the app uses SQLite instead of PostgreSQL
import app.config

app.config.settings.database_url = "sqlite+aiosqlite:///test.db"

from collections.abc import AsyncGenerator, Generator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Now import app - it will use the SQLite URL we set above
from app.main import app as fastapi_app
import app.models  # noqa: F401

from app.database import Base, get_db
from app.api.dependencies import DbSession

TEST_DATABASE_URL = "sqlite+aiosqlite:///test.db"


test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=NullPool,
)

# Use the same engine for TestingSessionLocal
TestingSessionLocal = sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# Set up dependency override at session scope - applies to all tests
def override_get_db():
    async def inner():
        async with TestingSessionLocal() as session:
            yield session

    return inner


# Set the overrides on the FastAPI app instance
fastapi_app.dependency_overrides[get_db] = override_get_db()


@pytest.fixture(scope="function", autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """Create tables before each test and drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def sample_url() -> str:
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@pytest.fixture
def sample_urls() -> list[str]:
    return [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=jNQXAC9IVRw",
        "https://youtu.be/dQw4w9WgXcQ",
        "https://www.youtube.com/shorts/dQw4w9WgXcQ",
    ]


@pytest.fixture
def invalid_urls() -> list[str]:
    return [
        "https://www.google.com",
        "https://vimeo.com/123456",
        "not-a-url",
        "",
        "ftp://youtube.com/video",
    ]


@pytest.fixture
def sample_user_data() -> dict[str, str]:
    return {
        "email": "test@example.com",
        "password": "securepassword123",
    }


@pytest.fixture
async def auth_headers(db_session: AsyncSession) -> dict[str, str]:
    from app.auth import create_access_token
    from app.models.user import User
    from app.services.auth_service import hash_password

    user = User(
        id="test-user-id",
        email="test@example.com",
        password_hash=hash_password("password123"),
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()

    token = create_access_token("test-user-id")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_download_data() -> dict[str, str]:
    return {
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    }
