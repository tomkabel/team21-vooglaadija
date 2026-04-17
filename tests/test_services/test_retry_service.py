"""Tests for retry service with exponential backoff and jitter.

These tests verify the retry calculation follows AWS Well-Architected Framework
and Google SRE best practices for exponential backoff with full jitter.
"""

import random
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from app.services.retry_service import (
    RETRY_BASE_SECONDS,
    RETRY_CAP_SECONDS,
    RETRY_JITTER_SECONDS,
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

    def test_retry_count_zero_minimum_delay(self):
        """Test minimum delay for first retry (retry_count=0).

        For retry_count=0:
        - exp_delay = min(600, 60 * 2^0) = min(600, 60) = 60
        - jitter = 0 (when mocked)
        - total = 60 + 0 = 60 seconds minimum
        """
        with patch("app.services.retry_service.random.randint", return_value=0):
            result = calculate_retry_with_jitter(0)
            expected_min = datetime.now(UTC) + timedelta(seconds=60)

        # With jitter=0, next_retry should be approximately 60 seconds in future
        # Allow 1 second tolerance for test execution time
        diff = (result - expected_min).total_seconds()
        assert -1 <= diff <= 1

    def test_retry_count_zero_maximum_delay(self):
        """Test maximum delay for first retry (retry_count=0).

        For retry_count=0:
        - exp_delay = min(600, 60 * 2^0) = 60
        - jitter = 60 (when mocked)
        - total = 60 + 60 = 120 seconds maximum
        """
        with patch("app.services.retry_service.random.randint", return_value=60):
            result = calculate_retry_with_jitter(0)
            expected_max = datetime.now(UTC) + timedelta(seconds=120)

        # With jitter=60, next_retry should be approximately 120 seconds in future
        diff = (result - expected_max).total_seconds()
        assert -1 <= diff <= 1

    def test_retry_count_one_exponential_doubling(self):
        """Test that delay doubles with retry_count=1.

        For retry_count=1:
        - exp_delay = min(600, 60 * 2^1) = min(600, 120) = 120
        - jitter range: 0-60
        - total range: 120-180 seconds
        """
        with patch("app.services.retry_service.random.randint", return_value=0):
            result = calculate_retry_with_jitter(1)
            expected_min = datetime.now(UTC) + timedelta(seconds=120)

        diff = (result - expected_min).total_seconds()
        assert -1 <= diff <= 1

    def test_retry_count_hits_cap(self):
        """Test that delay caps at RETRY_CAP_SECONDS.

        For high retry_count (e.g., 10):
        - exp_delay = min(600, 60 * 2^10) = min(600, 61440) = 600 (capped)
        - jitter range: 0-60
        - total range: 600-660 seconds
        """
        with patch("app.services.retry_service.random.randint", return_value=0):
            result = calculate_retry_with_jitter(10)
            # Should be capped at 600 seconds (with 0 jitter)
            expected = datetime.now(UTC) + timedelta(seconds=600)

        diff = (result - expected).total_seconds()
        assert -1 <= diff <= 1

    @pytest.mark.unit
    def test_jitter_provides_spread(self):
        """Test that jitter creates distribution spread, not identical values.

        Running with different random values should produce different results.
        """
        results = []
        for jitter_val in [0, 30, 60]:
            with patch("app.services.retry_service.random.randint", return_value=jitter_val):
                result = calculate_retry_with_jitter(0)
                results.append(result)

        # All three should be different due to different jitter values
        assert results[0] != results[1] != results[2]
        # Earlier jitter values should produce earlier retry times
        assert results[0] < results[1] < results[2]

    @pytest.mark.unit
    def test_thundering_herd_prevention(self):
        """Test that many jobs retry at different times, not all at once.

        This is the core purpose of jitter - without it, all failing jobs
        would retry at the exact same instant (thundering herd problem).
        """
        # Simulate 100 jobs all failing at t=0 with retry_count=0
        retry_times = []
        for _ in range(100):
            # Use fixed seed would give same result, so don't patch random
            # This tests the actual behavior
            retry_time = calculate_retry_with_jitter(0)
            retry_times.append(retry_time)

        # Calculate the spread (max - min) in seconds
        min_time = min(retry_times)
        max_time = max(retry_times)
        spread_seconds = (max_time - min_time).total_seconds()

        # With jitter of 0-60 seconds, spread should be significant
        # (statistically almost certain to have spread > 0)
        # We test that spread is at least 1 second to prove randomization works
        assert spread_seconds >= 1, (
            f"Spread of {spread_seconds}s suggests jitter may not be working. "
            "All 100 retry times should NOT be identical."
        )

        # Additionally verify most retries don't cluster at exactly the same moment
        # Group into 1-second buckets
        buckets = {}
        for rt in retry_times:
            bucket = rt.replace(microsecond=0)
            buckets[bucket] = buckets.get(bucket, 0) + 1

        max_in_single_bucket = max(buckets.values())
        # No single second should have more than 50% of retries
        assert max_in_single_bucket < 50, (
            f"{max_in_single_bucket}% of retries fell in same second. "
            "Jitter should distribute retries across multiple seconds."
        )


class TestGetRetryDelaySeconds:
    """Tests for the get_retry_delay_seconds helper function."""

    def test_returns_tuple_of_three_values(self):
        """Test that function returns (exp_delay, jitter, total_delay)."""
        result = get_retry_delay_seconds(0)
        assert isinstance(result, tuple)
        assert len(result) == 3

    def test_exp_delay_follows_exponential_pattern(self):
        """Test that exp_delay doubles with each retry."""
        delays = [get_retry_delay_seconds(i)[0] for i in range(5)]

        # exp_delay should double each time until hitting cap
        assert delays[0] == 60  # 60 * 2^0 = 60
        assert delays[1] == 120  # 60 * 2^1 = 120
        assert delays[2] == 240  # 60 * 2^2 = 240
        assert delays[3] == 480  # 60 * 2^3 = 480
        assert delays[4] == 600  # min(600, 960) = 600 (capped)

    def test_jitter_within_bounds(self):
        """Test that jitter is always within 0 to RETRY_JITTER_SECONDS."""
        for _ in range(100):
            _, jitter, _ = get_retry_delay_seconds(0)
            assert 0 <= jitter <= RETRY_JITTER_SECONDS


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
        # Base should be between 30 seconds and 5 minutes
        assert 30 <= RETRY_BASE_SECONDS <= 300

    def test_retry_cap_reasonable(self):
        """Test that RETRY_CAP_SECONDS is a reasonable value."""
        # Cap should be between 5 minutes and 30 minutes
        assert 300 <= RETRY_CAP_SECONDS <= 1800

    def test_retry_jitter_reasonable(self):
        """Test that RETRY_JITTER_SECONDS is a reasonable value."""
        # Jitter should be between 1 second and base value
        assert 1 <= RETRY_JITTER_SECONDS <= RETRY_BASE_SECONDS

    def test_base_less_than_cap(self):
        """Test that base is less than cap (required for proper backoff)."""
        assert RETRY_BASE_SECONDS < RETRY_CAP_SECONDS
