"""Database engine and session configuration shared by API and worker.

Uses lazy initialization to avoid creating the engine at import time,
which prevents issues with test environment overrides and ensures
the engine is created with the correct configuration.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from core.config import settings
from core.models.base import Base as CoreBase

Base = CoreBase


def _connect_args(database_url: str) -> dict[str, object]:
    """Return dialect-appropriate ``connect_args`` for ``create_async_engine``.

    All PostgreSQL traffic in production is routed through PgBouncer in
    transaction-pooling mode, which does not preserve server-side prepared
    statements across pooled connections. asyncpg's default statement cache
    then goes stale mid-session and raises ``prepared statement ... does not
    exist`` errors. Disabling the cache makes every query use an unnamed
    prepared statement, which is safe under transaction pooling.
    """
    url = make_url(database_url)
    if url.get_backend_name() == "postgresql" and url.get_driver_name() == "asyncpg":
        return {"statement_cache_size": 0}
    return {}


class _EngineFactory:
    """Lazy-initialized engine and session factory wrapper.

    Avoids module-level global state while providing singleton-like behavior.
    """

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None
        self._async_session_factory: async_sessionmaker[AsyncSession] | None = None
        self._replica_engine: AsyncEngine | None = None
        self._replica_session_factory: async_sessionmaker[AsyncSession] | None = None

    def get_engine(self) -> AsyncEngine:
        """
        Provide the configured asynchronous database engine.

        Returns:
            AsyncEngine: The database engine.
        """
        if self._engine is None:
            self._engine = create_async_engine(
                settings.database_url,
                echo=False,
                future=True,
                connect_args=_connect_args(settings.database_url),
                pool_recycle=settings.db_pool_recycle,
                pool_pre_ping=True,
                **self._pool_kwargs(settings.database_url),
            )
        return self._engine

    def get_replica_engine(self) -> AsyncEngine:
        """
        Provide the read-only engine bound to the configured replica.

        Falls back to the primary engine when no replica host is configured.

        Returns:
            AsyncEngine: The read-only database engine.
        """
        if not settings.db_replica_host:
            return self.get_engine()
        if self._replica_engine is None:
            replica_url = settings.database_replica_url
            self._replica_engine = create_async_engine(
                replica_url,
                echo=False,
                future=True,
                connect_args=_connect_args(replica_url),
                pool_recycle=settings.db_pool_recycle,
                pool_pre_ping=True,
                **self._pool_kwargs(replica_url),
            )
        return self._replica_engine

    def _pool_kwargs(self, database_url: str) -> dict[str, object]:
        """Return pool kwargs appropriate for the current dialect and environment.

        tests/conftest.py sets ``settings.db_disable_pooling = True`` on the
        settings singleton because pytest-asyncio tears down its event loop
        between test functions by default: a pooled asyncpg/aiosqlite
        connection this singleton opened on one loop then raises "unable to
        perform operation on <TCPTransport closed=True ...>; the handler is
        closed" the next time a test checks it out under a different loop.
        NullPool sidesteps this by opening a fresh connection per checkout
        instead of reusing one across event-loop boundaries; it accepts no
        pool_size/max_overflow/pool_timeout kwargs, so those are skipped here.
        """
        if settings.db_disable_pooling:
            return {"poolclass": NullPool}
        url = make_url(database_url)
        if url.get_backend_name() == "sqlite":
            return {}
        return {
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "pool_timeout": settings.db_pool_timeout,
        }

    def get_async_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get or create the async session factory (lazy initialization)."""
        if self._async_session_factory is None:
            self._async_session_factory = async_sessionmaker(
                self.get_engine(),
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._async_session_factory

    def get_replica_session_factory(self) -> async_sessionmaker[AsyncSession]:
        """Get or create the read-only session factory bound to the replica."""
        if not settings.db_replica_host:
            return self.get_async_session_factory()
        if self._replica_session_factory is None:
            self._replica_session_factory = async_sessionmaker(
                self.get_replica_engine(),
                class_=AsyncSession,
                expire_on_commit=False,
            )
        return self._replica_session_factory


_factory = _EngineFactory()


def get_engine() -> AsyncEngine:
    """Get or create the async engine (lazy initialization)."""
    return _factory.get_engine()


def get_replica_engine() -> AsyncEngine:
    """Get or create the read-only async engine bound to the replica."""
    return _factory.get_replica_engine()


def get_async_session_factory() -> async_sessionmaker[AsyncSession]:
    """
    Provide the shared asynchronous database session factory.

    Returns:
        async_sessionmaker[AsyncSession]: The session factory used to create asynchronous database sessions.
    """
    return _factory.get_async_session_factory()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session."""
    async with _factory.get_async_session_factory()() as session:
        yield session


async def get_replica_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields a read-only session against the replica.

    Intended for analytical/reporting queries that can tolerate replication
    lag. Falls back to the primary session when no replica is configured.
    Do not use this for writes: the replica connection rejects them.
    """
    async with _factory.get_replica_session_factory()() as session:
        yield session


get_db = get_async_session

__all__ = [
    "Base",
    "get_async_session",
    "get_async_session_factory",
    "get_db",
    "get_engine",
    "get_replica_engine",
    "get_replica_session",
]
