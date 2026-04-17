"""Redis queue operations for the download worker.

Uses lazy initialization to avoid import-time side effects.
In test environments, mock objects are created on first access.
"""

import os
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    pass

_redis_client = None


def _get_redis_client():
    """Get or create the Redis client (lazy initialization)."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client

    if os.environ.get("TESTING"):
        from unittest.mock import AsyncMock, MagicMock

        client = MagicMock()
        pipe_mock = MagicMock()
        pipe_mock.execute = AsyncMock(return_value=[None, 0, None, None])
        pipe_mock.zremrangebyscore = MagicMock()
        pipe_mock.zcard = MagicMock()
        pipe_mock.zadd = MagicMock()
        pipe_mock.expire = MagicMock()
        client.pipeline.return_value = pipe_mock
        client.zrange = AsyncMock(return_value=[])
        client.lpush = AsyncMock(return_value=1)
        client.rpop = AsyncMock(return_value=None)
        client.brpop = AsyncMock(return_value=None)
        client.ping = AsyncMock(return_value=True)
        _redis_client = client
    else:
        import redis.asyncio as aioredis

        from app.config import settings

        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)

    return _redis_client


def __getattr__(name: str):
    """Lazy attribute access for backward compatibility."""
    if name == "redis_client":
        return _get_redis_client()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


async def enqueue_job(job_id: UUID | str) -> None:
    """Enqueue a download job for processing.

    Uses the async Redis client to push job IDs to the download queue.
    """
    # Use module-level redis_client so tests can patch it
    import worker.queue as _queue

    client = _queue.redis_client
    await client.lpush("download_queue", str(job_id))
