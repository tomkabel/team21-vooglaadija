from unittest.mock import MagicMock

from app.config import settings

# Mock redis in test environment
try:
    import os

    if os.environ.get("TESTING"):
        redis_client = MagicMock()
    else:
        import redis

        redis_client = redis.from_url(settings.redis_url, decode_responses=True)
except Exception:
    redis_client = MagicMock()


def enqueue_job(job_id: str) -> None:
    """Enqueue a download job for processing."""
    redis_client.lpush("download_queue", job_id)
