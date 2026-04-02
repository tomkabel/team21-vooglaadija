import asyncio
import os

# CRITICAL: Set environment variables BEFORE any other imports
os.environ["TESTING"] = "1"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-not-for-production-use-32chars"

# Determine database URL based on environment
# In CI integration tests, use PostgreSQL service; otherwise use SQLite per-worker
_use_postgres = os.environ.get("CI_INTEGRATION", "").strip().lower() in ("1", "true")

if _use_postgres:
    _test_db_url = "postgresql+asyncpg://test_user:test_pass@localhost:5432/test_db"
else:
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


@pytest.fixture(scope="session", autouse=True)
async def setup_database_session() -> AsyncGenerator[None, None]:
    """Create tables once per session. Tables persist until session end."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Tables are dropped at session end - safe because all tests are done
    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    except Exception:
        pass  # Ignore errors during cleanup


@pytest.fixture(scope="function", autouse=True)
async def setup_database(setup_database_session: None) -> AsyncGenerator[None, None]:
    """Provide test isolation by cleaning data between tests.

    Uses transaction rollback pattern: each test runs in a transaction
    that is rolled back at teardown, ensuring clean state.
    """
    async with test_engine.connect() as conn:
        trans = await conn.begin()
        try:
            yield
        finally:
            await trans.rollback()
    # Tables are dropped at session end - safe because all tests are done
    try:
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    except Exception:
        pass  # Ignore errors during cleanup


@pytest.fixture(scope="function", autouse=True)
async def setup_database(setup_database_session: None) -> AsyncGenerator[None, None]:
    """Provide test isolation by cleaning data between tests.

    Uses transaction rollback pattern: each test runs in a transaction
    that is rolled back at teardown, ensuring clean state.
    """
    async with test_engine.connect() as conn:
        trans = await conn.begin()
        try:
            yield
        finally:
            await trans.rollback()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for tests."""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
def sample_url() -> str:
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


async def create_test_user_and_login(
    client,
    email: str = "downloads@example.com",
    password: str = "securepassword123",
) -> dict:
    """Helper to register and login a test user, returning auth headers."""
    register_resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert register_resp.status_code in (200, 201), (
        f"Registration failed: {register_resp.status_code} - {register_resp.text}"
    )

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert login_resp.status_code == 200, (
        f"Login failed: {login_resp.status_code} - {login_resp.text}"
    )
    login_data = login_resp.json()
    assert "access_token" in login_data, f"access_token not in login response: {login_resp.text}"
    token = login_data["access_token"]
    return {"Authorization": f"Bearer {token}"}
