import os

from app.config import settings

# Mock redis in test environment
if os.environ.get("TESTING"):
    from unittest.mock import AsyncMock, MagicMock

    # Use MagicMock for the client (pipeline is sync), but AsyncMock for async methods
    redis_client = MagicMock()
    pipe_mock = MagicMock()
    pipe_mock.execute = AsyncMock(return_value=[None, 0, None, None])
    pipe_mock.zremrangebyscore = MagicMock()
    pipe_mock.zcard = MagicMock()
    pipe_mock.zadd = MagicMock()
    pipe_mock.expire = MagicMock()
    redis_client.pipeline.return_value = pipe_mock
    redis_client.zrange = AsyncMock(return_value=[])
    redis_client.lpush = AsyncMock()
    redis_client.rpop = MagicMock(return_value=None)
else:
    import redis.asyncio as aioredis

    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)


async def enqueue_job(job_id: str) -> None:
    """Enqueue a download job for processing.

    Uses the async Redis client to push job IDs to the download queue.
    """
    await redis_client.lpush("download_queue", job_id)
