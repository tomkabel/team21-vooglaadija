"""Tests for the rate limiter middleware."""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.middleware.rate_limit import RateLimiter


def _make_mock_redis():
    """Create a mock Redis client with sync pipeline and async execute."""
    redis = MagicMock()
    pipe = MagicMock()
    pipe.zremrangebyscore = MagicMock()
    pipe.zcard = MagicMock()
    pipe.zadd = MagicMock()
    pipe.expire = MagicMock()
    pipe.execute = AsyncMock(return_value=[None, 0, None, None])
    redis.pipeline = MagicMock(return_value=pipe)
    redis.zrange = AsyncMock(return_value=[])
    return redis


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_allows_requests_under_limit(self):
        mock_redis = _make_mock_redis()
        limiter = RateLimiter(redis_client=mock_redis, max_requests=5, window_seconds=60)
        mock_redis.pipeline.return_value.execute = AsyncMock(return_value=[None, 3, None, None])
        result = await limiter.is_allowed("test-key")
        assert result is True

    @pytest.mark.asyncio
    async def test_rejects_requests_over_limit(self):
        mock_redis = _make_mock_redis()
        limiter = RateLimiter(redis_client=mock_redis, max_requests=5, window_seconds=60)
        mock_redis.pipeline.return_value.execute = AsyncMock(return_value=[None, 5, None, None])
        result = await limiter.is_allowed("test-key")
        assert result is False

    @pytest.mark.asyncio
    async def test_allows_on_redis_failure(self):
        mock_redis = _make_mock_redis()
        limiter = RateLimiter(redis_client=mock_redis, max_requests=5, window_seconds=60)
        mock_redis.pipeline.return_value.execute = AsyncMock(return_value=None)
        result = await limiter.is_allowed("test-key")
        assert result is True  # Fail-open

    @pytest.mark.asyncio
    async def test_get_retry_after(self):
        mock_redis = _make_mock_redis()
        limiter = RateLimiter(redis_client=mock_redis, max_requests=5, window_seconds=60)
        now = time.time()
        oldest_timestamp = now - 30
        mock_redis.zrange = AsyncMock(return_value=[(b"key", oldest_timestamp)])
        retry_after = await limiter.get_retry_after("test-key")
        assert 29 <= retry_after <= 31

    @pytest.mark.asyncio
    async def test_get_retry_after_returns_zero_when_empty(self):
        mock_redis = _make_mock_redis()
        limiter = RateLimiter(redis_client=mock_redis, max_requests=5, window_seconds=60)
        mock_redis.zrange = AsyncMock(return_value=[])
        retry_after = await limiter.get_retry_after("test-key")
        assert retry_after == 0
