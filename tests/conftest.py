import asyncio
import fcntl
import json
import os
import shutil
import sys
import tempfile
import time
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path

os.environ["TESTING"] = "1"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only-not-for-production-use-32chars"
os.environ["BCRYPT_ROUNDS"] = "4"  # min rounds for test speed (prod default: 12)

import pytest
from sqlalchemy import create_engine, delete, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer

from core import models as core_models

_REGISTERED_MODEL_EXPORTS = core_models.__all__

_worker_id = os.environ.get("PYTEST_XDIST_WORKER", "gw0")

# pytest-xdist runs each worker in its own process, and this module is
# imported once per worker. Without coordination that means one PostgreSQL
# container per worker. Instead, workers of the *same* pytest invocation
# (sharing PYTEST_XDIST_TESTRUNUID) race for a file lock: the winner starts
# the single shared container and records its connection info; everyone
# else just reads that info. Each worker still gets its own database inside
# the shared container (see _worker_db_name below) for test isolation.
_run_id = os.environ.get("PYTEST_XDIST_TESTRUNUID", "solo")
_coord_dir = Path(tempfile.gettempdir()) / f"vooglaadija-pg-testcontainer-{_run_id}"
_coord_dir.mkdir(parents=True, exist_ok=True)
_workers_dir = _coord_dir / "workers"
_workers_dir.mkdir(parents=True, exist_ok=True)
_info_path = _coord_dir / "info.json"
_lock_path = _coord_dir / "lock"

(_workers_dir / _worker_id).touch()

postgres_container: PostgresContainer | None = None
_is_container_leader = False

with open(_lock_path, "w") as _lock_file:
    fcntl.flock(_lock_file, fcntl.LOCK_EX)
    try:
        if _info_path.exists():
            _container_info = json.loads(_info_path.read_text())
        else:
            postgres_container = PostgresContainer("postgres:17-alpine")
            postgres_container.start()
            _is_container_leader = True
            _container_info = {
                "host": postgres_container.get_container_host_ip(),
                "port": postgres_container.get_exposed_port(5432),
                "user": postgres_container.username,
                "password": postgres_container.password,
                "dbname": postgres_container.dbname,
            }
            # This is Testcontainers' own random, throwaway password for an
            # ephemeral local Postgres container that lives only for this
            # test run — not a real secret. It's written here purely so
            # sibling pytest-xdist worker processes can read the connection
            # info; 0o600 (created atomically, owner-only) keeps it from
            # other local users. lgtm[py/clear-text-storage-sensitive-data]
            fd = os.open(_info_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as _info_file:
                _info_file.write(json.dumps(_container_info))
    finally:
        fcntl.flock(_lock_file, fcntl.LOCK_UN)

_container_host = _container_info["host"]
_container_port = str(_container_info["port"])
_container_user = _container_info["user"]
_container_password = _container_info["password"]
_container_dbname = _container_info["dbname"]

_worker_db_name = f"test_{_worker_id}"

_sync_url = (
    f"postgresql+psycopg://{_container_user}:{_container_password}"
    f"@{_container_host}:{_container_port}/{_container_dbname}"
)
_sync_engine = create_engine(_sync_url, isolation_level="AUTOCOMMIT")
with _sync_engine.connect() as conn:
    conn.execute(text(f'DROP DATABASE IF EXISTS "{_worker_db_name}"'))
    conn.execute(text(f'CREATE DATABASE "{_worker_db_name}"'))
_sync_engine.dispose()

os.environ["DB_HOST"] = _container_host
os.environ["DB_PORT"] = _container_port
os.environ["DB_USER"] = _container_user
os.environ["DB_PASSWORD"] = _container_password
os.environ["DB_NAME"] = _worker_db_name

import core.config  # noqa: E402

_worker_database_url = (
    f"postgresql+asyncpg://{_container_user}:{_container_password}"
    f"@{_container_host}:{_container_port}/{_worker_db_name}"
)
core.config.settings.database_url = _worker_database_url
# pytest-asyncio tears down its event loop between test functions by default.
# core.database's production engine singleton pools connections; a pooled
# asyncpg connection opened on one test's loop breaks the next time it's
# checked out under a different test's loop ("TCPTransport closed ... the
# handler is closed"). This tells core/database.py to use NullPool instead.
core.config.settings.db_disable_pooling = True

from app.main import app as fastapi_app  # noqa: E402
from core.database import Base, get_db  # noqa: E402

TEST_DATABASE_URL = _worker_database_url

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    # pytest-asyncio tears down its event loop between test functions by
    # default; a pooled asyncpg connection opened on one loop raises
    # "TCPTransport closed ... the handler is closed" the next time it's
    # checked out under a different loop. NullPool opens a fresh connection
    # per checkout instead of reusing one across event loop boundaries.
    poolclass=NullPool,
)

TestingSessionLocal = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


def override_get_db():
    async def inner():
        async with TestingSessionLocal() as session:
            yield session

    return inner


fastapi_app.dependency_overrides[get_db] = override_get_db()


@pytest.fixture(scope="session", autouse=True)
async def _session_cleanup():
    yield
    await test_engine.dispose()
    (_workers_dir / _worker_id).unlink(missing_ok=True)

    if not _is_container_leader:
        return

    # The leader owns the only live PostgresContainer handle (and the
    # Testcontainers "Ryuk" reaper connection that keeps it alive). Wait for
    # every other worker to deregister before stopping the shared container,
    # so a fast-finishing leader doesn't pull the container out from under
    # workers that are still running. Bounded so a stuck worker can't hang
    # teardown forever.
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        try:
            remaining = any(_workers_dir.iterdir())
        except FileNotFoundError:
            remaining = False
        if not remaining:
            break
        await asyncio.sleep(1)

    assert postgres_container is not None  # leader always starts one
    postgres_container.stop()
    shutil.rmtree(_coord_dir, ignore_errors=True)


@pytest.fixture(scope="session", autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """Create tables once per xdist worker, drop at end.

    Per-test isolation is provided by the autouse ``_cleanup_test_tables`` fixture,
    which deletes all rows before each test. Combined with the shared Postgres
    container and NullPool connections, schema isolation per test is unnecessary
    and costs real time across a large suite.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(autouse=True)
def _reset_shutdown_event():
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
async def db_session() -> AsyncSession:
    async with TestingSessionLocal() as session:
        yield session


async def seed_user(session: AsyncSession, user_id: uuid.UUID | None = None):
    """Insert a minimal ``User`` row and return it.

    Real PostgreSQL (via Testcontainers) enforces the FK from
    ``download_jobs.user_id`` / ``failed_jobs.user_id`` to ``users.id`` that
    the previous SQLite test database never checked. Fixtures/tests that
    fabricate a bare ``user_id`` UUID for a DownloadJob/FailedJob/Outbox row
    must call this (or ``seed_download_job``) first instead of relying on an
    unpersisted UUID satisfying the constraint.
    """
    from core.models.user import User

    resolved_id = user_id or uuid.uuid4()
    user = User(id=resolved_id, email=f"{resolved_id}@test.example", password_hash="test-hash")
    session.add(user)
    await session.flush()
    return user


async def seed_download_job(
    session: AsyncSession,
    job_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    **overrides,
):
    """Insert a ``User`` (if needed) and a ``DownloadJob`` row, and return the job.

    ``overrides`` are passed through to ``DownloadJob(...)`` (e.g. ``status``,
    ``url``, ``error_category``) on top of sane defaults.
    """
    from core.models.download_job import DownloadJob

    user = await seed_user(session, user_id)
    job = DownloadJob(
        id=job_id or uuid.uuid4(),
        user_id=user.id,
        url=overrides.pop("url", "https://www.youtube.com/watch?v=seeded"),
        status=overrides.pop("status", "pending"),
        **overrides,
    )
    session.add(job)
    await session.flush()
    return job


@pytest.fixture
def sample_url() -> str:
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


async def create_test_user_and_login(
    client,
    email: str = "downloads@example.com",
    password: str = "securepassword123",
    _lock=None,
) -> str:
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
