import asyncio
import os

# CRITICAL: Set environment variables BEFORE any other imports
os.environ["TESTING"] = "1"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-not-for-production-use-32chars"

# Determine unique database URL per xdist worker to avoid race conditions
_worker_id = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
_test_db_path = os.path.abspath(f"test_{_worker_id}.db")
_test_db_url = f"sqlite+aiosqlite:///{_test_db_path}"

# Force reconfigure the database URL before any app imports
# This ensures the app uses SQLite instead of PostgreSQL
import app.config  # noqa: E402

app.config.settings.database_url = _test_db_url

from collections.abc import AsyncGenerator, Generator  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402

import app.models  # noqa: E402
from app.database import Base, get_db  # noqa: E402

# Now import app - it will use the SQLite URL we set above
from app.main import app as fastapi_app  # noqa: E402

TEST_DATABASE_URL = _test_db_url


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
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for tests."""
    async with TestingSessionLocal() as session:
        yield session


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
    from app.auth import create_access_token  # noqa: PLC0415
    from app.models.user import User  # noqa: PLC0415
    from app.services.auth_service import hash_password  # noqa: PLC0415

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
