import redis

from app.config import settings

redis_client = redis.from_url(settings.redis_url, decode_responses=True)


def enqueue_job(job_id: str) -> None:
    """Enqueue a download job for processing."""
    redis_client.lpush("download_queue", job_id)
