import os
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

# CRITICAL: Set environment variables BEFORE any other imports
os.environ["TESTING"] = "1"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-not-for-production-use-32chars"
os.environ["BCRYPT_ROUNDS"] = "4"  # min rounds for test speed (prod default: 12)

# Support running integration tests against real PostgreSQL via docker-compose.test.yml.
# Usage:
#   TEST_DATABASE_URL=postgresql+asyncpg://test_user:test_pass@localhost:5433/test_db \
#     pytest tests/ -v
# If unset, fallback to per-worker SQLite for fast parallel unit tests.
_test_db_url = os.environ.get("TEST_DATABASE_URL")
_using_postgres = _test_db_url is not None

# Unique worker id used to isolate database state when running under
# pytest-xdist (`-n auto`); defaults to a single logical worker otherwise.
_worker_id = os.environ.get("PYTEST_XDIST_WORKER", "gw0")


# asyncpg query parameters that have no libpq/psycopg equivalent. psycopg
# raises on unrecognized connection options, so these must be dropped rather
# than forwarded when building the admin DSN below.
_ASYNCPG_ONLY_PARAMS = frozenset(
    {
        "server_settings",
        "statement_cache_size",
        "max_cached_statement_lifetime",
        "max_cacheable_statement_size",
        "command_timeout",
        "direct_tls",
    }
)

# asyncpg query parameter names that map to a differently-named libpq option.
_ASYNCPG_TO_LIBPQ_PARAM = {
    "ssl": "sslmode",
    "timeout": "connect_timeout",
}


def _build_admin_dsn(base_url: str) -> str:
    """Build a libpq-compatible admin DSN from an asyncpg-style database URL.

    Points at the server's default ``postgres`` maintenance database while
    preserving connection-level parameters (TLS, timeouts, ...) carried in
    ``base_url``'s query string. asyncpg-specific parameter names are
    translated to their libpq/psycopg equivalents; parameters with no libpq
    equivalent are dropped instead of forwarded verbatim.
    """
    parts = urlsplit(base_url)
    translated_params = [
        (_ASYNCPG_TO_LIBPQ_PARAM.get(key, key), value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if _ASYNCPG_TO_LIBPQ_PARAM.get(key, key) not in _ASYNCPG_ONLY_PARAMS
    ]
    query = urlencode(translated_params)
    return urlunsplit((parts.scheme.split("+")[0], parts.netloc, "/postgres", query, ""))


def _ensure_postgres_database_exists(base_url: str, db_name: str) -> None:
    """Create ``db_name`` on the Postgres server from ``base_url`` if missing.

    Runs synchronously via psycopg, before any async engine or event loop
    exists. Connects to the server's default ``postgres`` maintenance
    database, since ``CREATE DATABASE`` cannot run inside a transaction
    against the database being created (and psycopg defaults to
    transactional execution, hence ``autocommit=True`` here).
    """
    import psycopg
    from psycopg import sql

    admin_dsn = _build_admin_dsn(base_url)
    with psycopg.connect(admin_dsn, autocommit=True) as conn:
        exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_name,)).fetchone()
        if not exists:
            try:
                conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(db_name)))
            except psycopg.errors.DuplicateDatabase:
                # Another process created it between our check and CREATE
                # (e.g. concurrent xdist worker startup) - safe to ignore.
                pass


if not _using_postgres:
    # Determine unique database URL per xdist worker to avoid race conditions
    _test_db_path = os.path.abspath(f"test_{_worker_id}.db")
    _test_db_url = f"sqlite+aiosqlite:///{_test_db_path}"

    # Remove stale per-worker database from previous runs.
    # create_all skips existing tables so a stale file with an older schema
    # won't be updated to match the current model definitions.
    try:
        os.remove(_test_db_path)
    except OSError:
        pass
else:
    # Isolate PostgreSQL state per xdist worker. `setup_database` (below)
    # creates/drops ALL tables once per worker session - if every worker
    # pointed at the same database, one worker could drop tables out from
    # under another worker's in-flight query. Mirror the per-worker SQLite
    # pattern above: suffix the database name with the worker id and create
    # it on first use if it doesn't already exist.
    _base_test_db_url = _test_db_url
    _worker_db_name = f"{urlsplit(_base_test_db_url).path.lstrip('/')}_{_worker_id}"
    _ensure_postgres_database_exists(_base_test_db_url, _worker_db_name)
    _base_parts = urlsplit(_base_test_db_url)
    _test_db_url = urlunsplit(_base_parts._replace(path=f"/{_worker_db_name}"))

# Force reconfigure the database URL before any app imports.
# This ensures the app uses the URL selected above (SQLite or PostgreSQL).
import core.config  # noqa: E402

core.config.settings.database_url = _test_db_url

from collections.abc import AsyncGenerator  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy import delete  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool  # noqa: E402

from core import models as core_models  # noqa: E402
from core.database import Base, get_db  # noqa: E402

_REGISTERED_MODEL_EXPORTS = core_models.__all__

# Now import app - it will use the database URL we set above
from app.main import app as fastapi_app  # noqa: E402

TEST_DATABASE_URL = _test_db_url

_engine_kwargs: dict = {"poolclass": NullPool}
if not _using_postgres:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    **_engine_kwargs,
)

# Use async_sessionmaker for proper async session support
TestingSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


# Set up dependency override at session scope - applies to all tests
def override_get_db():
    async def inner():
        async with TestingSessionLocal() as session:
            yield session

    return inner


# Set the overrides on the FastAPI app instance
fastapi_app.dependency_overrides[get_db] = override_get_db()


@pytest.fixture(scope="session", autouse=True)
async def _session_cleanup() -> AsyncGenerator[None, None]:
    """Dispose the test engine after all tests in the worker finish."""
    yield
    await test_engine.dispose()


@pytest.fixture(scope="session", autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """Create tables once per xdist worker, drop at end.

    Per-test isolation is provided by the autouse ``_cleanup_test_tables`` fixture,
    which deletes all rows before each test. Combined with per-worker DB files and
    NullPool connections, schema isolation per test is unnecessary and costs ~270s
    for 972 tests (0.28s DDL x 2 ops x 972 tests).
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def _reset_shutdown_event():
    """Reset global worker shutdown state before each test.

    Some tests set shutdown_event or shutdown_requested_at to trigger shutdown behavior,
    which persists across tests in the same xdist worker process.
    """
    try:
        from worker.state import shutdown_event

        shutdown_event.clear()
    except Exception:
        pass

    worker_main = sys.modules.get("worker.main")
    if worker_main is not None:
        worker_main.shutdown_requested_at = None


@pytest.fixture(autouse=True)
def _disable_token_blacklist_lookup(monkeypatch: pytest.MonkeyPatch) -> None:
    """Avoid Redis-backed blacklist checks for ordinary authenticated test requests."""

    async def _not_blacklisted(_token_jti: str) -> bool:
        return False

    async def _reserve_ok(_token_jti: str, ttl_seconds: int = 0) -> bool:
        return True

    monkeypatch.setattr("app.api.dependencies.is_token_blacklisted", _not_blacklisted)
    monkeypatch.setattr("app.services.token_blacklist.reserve_token_jti", _reserve_ok)


@pytest.fixture(autouse=True)
async def _cleanup_test_tables() -> AsyncGenerator[None, None]:
    """Delete all table rows before each test to ensure test isolation.

    With session-scoped table creation, truncating/deleting rows between tests
    guarantees a clean database slate (no PK, unique, FK, or count leaks).
    """
    from core.models import DownloadJob, FailedJob, Outbox, User

    async with TestingSessionLocal() as session:
        await session.execute(delete(Outbox))
        await session.execute(delete(FailedJob))
        await session.execute(delete(DownloadJob))
        await session.execute(delete(User))
        await session.commit()
    yield


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
    _lock=None,
) -> str:
    """Register and login a test user using a unique email per call.

    Uses a UUID prefix on the email to avoid isolation issues with
    parallel xdist workers. Returns the access token string.

    The optional _lock parameter is unused (kept for API compatibility).
    """
    import uuid

    unique_email = f"{uuid.uuid4().hex[:8]}@{email.split('@')[1]}"
    await client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": password},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": unique_email, "password": password},
    )
    return response.json()["access_token"]
