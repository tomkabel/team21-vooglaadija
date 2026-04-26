"""Tests for retry service with exponential backoff and jitter.

These tests verify the retry calculation follows AWS Well-Architected Framework
and Google SRE best practices for exponential backoff with full jitter.
"""

from datetime import UTC, datetime

import pytest

from app.services.retry_service import (
    RETRY_BASE_SECONDS,
    RETRY_CAP_SECONDS,
    JitterRetryCalculator,
    calculate_retry_with_jitter,
    default_calculator,
    get_retry_delay_seconds,
)


class TestCalculateRetryWithJitter:
    """Tests for the calculate_retry_with_jitter function."""

    def test_returns_datetime_in_future(self):
        """Test that next retry is in the future."""
        before = datetime.now(UTC)
        result = calculate_retry_with_jitter(0)
        after = datetime.now(UTC)

        assert result > before
        assert result > after

    def test_returns_utc_timezone(self):
        """Test that result is in UTC timezone."""
        result = calculate_retry_with_jitter(0)
        assert result.tzinfo is UTC

    def test_retry_count_zero_delay_within_bounds(self):
        """Test delay for first retry (retry_count=0).

        For retry_count=0:
        - cap_delay = min(600, 60 * 2^0) = min(600, 60) = 60
        - delay = random.uniform(0, 60) = 0-60 seconds
        """
        results = []
        for _ in range(50):
            result = calculate_retry_with_jitter(0)
            diff = (result - datetime.now(UTC)).total_seconds()
            results.append(diff)

        min_diff = min(results)
        max_diff = max(results)

        assert 0 <= min_diff <= 61
        assert 0 <= max_diff <= 61

    def test_retry_count_one_exponential_doubling(self):
        """Test that delay doubles with retry_count=1.

        For retry_count=1:
        - cap_delay = min(600, 60 * 2^1) = min(600, 120) = 120
        - delay = random.uniform(0, 120) = 0-120 seconds
        """
        results = []
        for _ in range(50):
            result = calculate_retry_with_jitter(1)
            diff = (result - datetime.now(UTC)).total_seconds()
            results.append(diff)

        min_diff = min(results)
        max_diff = max(results)

        assert 0 <= min_diff <= 121
        assert 0 <= max_diff <= 121

    def test_retry_count_hits_cap(self):
        """Test that delay caps at RETRY_CAP_SECONDS.

        For high retry_count (e.g., 10):
        - cap_delay = min(600, 60 * 2^10) = min(600, 61440) = 600
        - delay = random.uniform(0, 600) = 0-600 seconds
        """
        results = []
        for _ in range(50):
            result = calculate_retry_with_jitter(10)
            diff = (result - datetime.now(UTC)).total_seconds()
            results.append(diff)

        max_diff = max(results)

        assert max_diff <= 601

    @pytest.mark.unit
    def test_thundering_herd_prevention(self):
        """Test that many jobs retry at different times, not all at once.

        This is the core purpose of jitter - without it, all failing jobs
        would retry at the exact same instant (thundering herd problem).
        """
        retry_times = []
        for _ in range(100):
            retry_time = calculate_retry_with_jitter(0)
            retry_times.append(retry_time)

        min_time = min(retry_times)
        max_time = max(retry_times)
        spread_seconds = (max_time - min_time).total_seconds()

        assert spread_seconds >= 1, (
            f"Spread of {spread_seconds}s suggests jitter may not be working. "
            "All 100 retry times should NOT be identical."
        )

        buckets = {}
        for rt in retry_times:
            bucket = rt.replace(microsecond=0)
            buckets[bucket] = buckets.get(bucket, 0) + 1

        max_in_single_bucket = max(buckets.values())
        assert max_in_single_bucket < 50, (
            f"{max_in_single_bucket}% of retries fell in same second. "
            "Jitter should distribute retries across multiple seconds."
        )


class TestGetRetryDelaySeconds:
    """Tests for the get_retry_delay_seconds helper function."""

    def test_returns_float(self):
        """Test that function returns a float (the delay in seconds)."""
        result = get_retry_delay_seconds(0)
        assert isinstance(result, float)

    def test_delay_within_bounds_for_retry_count_zero(self):
        """Test that delay is within bounds for retry_count=0."""
        for _ in range(100):
            delay = get_retry_delay_seconds(0)
            assert 0 <= delay <= 60

    def test_delay_within_bounds_for_retry_count_one(self):
        """Test that delay is within bounds for retry_count=1."""
        for _ in range(100):
            delay = get_retry_delay_seconds(1)
            assert 0 <= delay <= 120

    def test_delay_within_bounds_for_high_retry_count(self):
        """Test that delay caps at RETRY_CAP_SECONDS for high retry_count."""
        for _ in range(100):
            delay = get_retry_delay_seconds(10)
            assert 0 <= delay <= 600


class TestJitterRetryCalculator:
    """Tests for the JitterRetryCalculator class."""

    def test_calculate_next_retry_returns_datetime(self):
        """Test that calculate_next_retry returns a datetime."""
        calc = JitterRetryCalculator()
        result = calc.calculate_next_retry(0)
        assert isinstance(result, datetime)

    def test_calculate_next_retry_is_in_future(self):
        """Test that calculated retry is in the future."""
        calc = JitterRetryCalculator()
        before = datetime.now(UTC)
        result = calc.calculate_next_retry(0)
        after = datetime.now(UTC)

        assert result > before
        assert result > after


class TestDefaultCalculator:
    """Tests for the module-level default_calculator instance."""

    def test_is_jitter_retry_calculator(self):
        """Test that default_calculator is a JitterRetryCalculator."""
        assert isinstance(default_calculator, JitterRetryCalculator)

    def test_calculate_next_retry_works(self):
        """Test that default_calculator.calculate_next_retry works."""
        result = default_calculator.calculate_next_retry(0)
        assert isinstance(result, datetime)
        assert result > datetime.now(UTC)


class TestRetryConfiguration:
    """Tests for retry configuration constants."""

    def test_retry_base_reasonable(self):
        """Test that RETRY_BASE_SECONDS is a reasonable value."""
        assert 30 <= RETRY_BASE_SECONDS <= 300

    def test_retry_cap_reasonable(self):
        """Test that RETRY_CAP_SECONDS is a reasonable value."""
        assert 300 <= RETRY_CAP_SECONDS <= 1800

    def test_base_less_than_cap(self):
        """Test that base is less than cap (required for proper backoff)."""
        assert RETRY_BASE_SECONDS < RETRY_CAP_SECONDS
