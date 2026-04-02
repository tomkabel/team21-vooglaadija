"""Rate limiting middleware for FastAPI using async Redis."""

import time

import redis.asyncio as aioredis


class RateLimiter:
    """Redis-based rate limiter using sliding window algorithm."""

    def __init__(
        self,
        redis_client: aioredis.Redis,
        max_requests: int = 5,
        window_seconds: int = 60,
    ):
        self.redis = redis_client
        self.max_requests = max_requests
        self.window = window_seconds

    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed under rate limit.

        Args:
            key: Unique identifier for the rate limit bucket (e.g., IP + endpoint)

        Returns:
            True if request is allowed, False if rate limit exceeded

        """
        now = time.time()
        pipe = self.redis.pipeline()

        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, now - self.window)

        # Count current entries
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(now): now})

        # Set expiry on the key
        pipe.expire(key, self.window)

        try:
            results = await pipe.execute()
        except aioredis.ConnectionError:
            # Fail open on Redis connection errors
            return True

        # Handle case where redis is not available
        if not results or len(results) < 4:
            return True

        _, current_count, _, _ = results

        # Allow if count before adding current request is less than max
        return int(current_count) < self.max_requests

    async def get_retry_after(self, key: str) -> int:
        """Get seconds until rate limit resets.

        Args:
            key: Unique identifier for the rate limit bucket

        Returns:
            Seconds until the oldest request expires

        """
        now = time.time()
        try:
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
        except aioredis.ConnectionError:
            # Fail open on Redis connection errors
            return 0
        if not oldest:
            return 0
        oldest_timestamp = oldest[0][1]
        retry_after = int(oldest_timestamp + self.window - now)
        return max(0, retry_after)
