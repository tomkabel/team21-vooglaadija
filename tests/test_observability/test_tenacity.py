"""Tests for tenacity retry logic."""

import asyncio

import pytest
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

tenacity = pytest.importorskip("tenacity", reason="tenacity not installed")


class TransientError(Exception):
    """Error that should trigger a retry."""


class PermanentError(Exception):
    """Error that should NOT trigger a retry."""


class TestTenacityRetry:
    """Test tenacity retry logic."""

    def test_retry_on_transient_error(self):
        """Test that transient errors trigger retry."""
        attempts = []

        @retry(
            retry=retry_if_exception_type(TransientError),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.1, min=0.1, max=0.5),
            reraise=True,
        )
        def flaky_function():
            attempts.append(1)
            if len(attempts) < 3:
                raise TransientError("Temporary failure")
            return "success"

        result = flaky_function()
        assert result == "success"
        assert len(attempts) == 3

    def test_no_retry_on_permanent_error(self):
        """Test that permanent errors don't trigger retry."""
        attempts = []

        @retry(
            retry=retry_if_exception_type(TransientError),
            stop=stop_after_attempt(3),
            reraise=True,
        )
        def permanent_failure():
            attempts.append(1)
            raise PermanentError("Permanent failure")

        with pytest.raises(PermanentError):
            permanent_failure()

        assert len(attempts) == 1


class TestTenacityAsyncRetry:
    """Test tenacity retry logic with async functions."""

    @pytest.mark.asyncio
    async def test_async_retry_on_transient_error(self):
        """Test async function with retry on transient error."""
        attempts = []

        @retry(
            retry=retry_if_exception_type(TransientError),
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=0.1, min=0.1, max=0.5),
            reraise=True,
        )
        async def async_flaky_function():
            attempts.append(1)
            await asyncio.sleep(0.01)  # Small delay
            if len(attempts) < 3:
                raise TransientError("Temporary failure")
            return "success"

        result = await async_flaky_function()
        assert result == "success"
        assert len(attempts) == 3

    @pytest.mark.asyncio
    async def test_async_no_retry_on_permanent_error(self):
        """Test async function with permanent error (no retry)."""
        attempts = []

        @retry(
            retry=retry_if_exception_type(TransientError),
            stop=stop_after_attempt(3),
            reraise=True,
        )
        async def async_permanent_failure():
            attempts.append(1)
            await asyncio.sleep(0.01)
            raise PermanentError("Permanent failure")

        with pytest.raises(PermanentError):
            await async_permanent_failure()

        assert len(attempts) == 1


class TestTenacityWaitStrategies:
    """Test tenacity wait strategies."""

    def test_wait_exponential(self):
        """Test exponential backoff wait strategy."""
        wait_times = []

        original_wait = wait_exponential(multiplier=0.1, min=0.1, max=0.5)

        class FakeRetryState:
            def __init__(self, attempt_number):
                self.attempt_number = attempt_number

        for i in range(1, 6):
            wait = original_wait(FakeRetryState(i))
            wait_times.append(wait)

        # Each wait should be 2^(attempt-1) * multiplier, capped at max
        assert wait_times[0] == 0.1  # min is 0.1
        assert wait_times[1] == 0.2  # 2 * 0.1
        assert wait_times[2] == 0.4  # 4 * 0.1
        assert wait_times[3] == 0.5  # max is 0.5
        assert wait_times[4] == 0.5  # capped at max
