"""Retry service with exponential backoff and jitter.

Implements the "Exponential Backoff with Full Jitter" strategy as recommended
by AWS Well-Architected Framework and Google SRE practices (2026).

Formula: delay = random.uniform(0, min(cap, base * 2^attempt))

This prevents the "thundering herd" problem where all failing jobs retry
at the exact same instant, overwhelming both the system and external APIs.
"""

import random
from datetime import UTC, datetime, timedelta
from typing import Protocol

# Retry configuration constants
RETRY_BASE_SECONDS = 60  # Initial base delay (60 seconds)
RETRY_CAP_SECONDS = 600  # Maximum delay cap (10 minutes)


class RetryCalculator(Protocol):
    """Protocol for retry calculation strategies."""

    def calculate_next_retry(self, retry_count: int) -> datetime:
        """Calculate the next retry datetime for a given retry count."""
        ...


def calculate_retry_with_jitter(retry_count: int) -> datetime:
    """Calculate next retry time using exponential backoff with full jitter.

    Implements the "Exponential Backoff with Full Jitter" algorithm:
    - delay = random.uniform(0, min(cap, base * 2^attempt))

    This is the recommended approach per:
    - AWS Well-Architected Framework (2026)
    - Google SRE Book, Chapter 6 (Handling Overload)
    - Netflix Tech Blog "HASTINGS Presents: Exponential Backoff"

    Args:
        retry_count: The current retry attempt (0-indexed, so first retry is retry_count=0)

    Returns:
        datetime in UTC when the next retry should occur

    Example:
        >>> # First retry (retry_count=0):
        >>> #   cap_delay = min(600, 60 * 2^0) = min(600, 60) = 60
        >>> #   delay = random.uniform(0, 60) = 0-60 seconds
        >>>
        >>> # Second retry (retry_count=1):
        >>> #   cap_delay = min(600, 60 * 2^1) = min(600, 120) = 120
        >>> #   delay = random.uniform(0, 120) = 0-120 seconds
    """
    cap_delay = min(RETRY_CAP_SECONDS, RETRY_BASE_SECONDS * (2**retry_count))
    delay = random.uniform(0, cap_delay)
    return datetime.now(UTC) + timedelta(seconds=delay)


def get_retry_delay_seconds(retry_count: int) -> float:
    """Get the random delay for debugging/logging purposes.

    Returns:
        The delay in seconds (float) for the given retry count
    """
    cap_delay = min(RETRY_CAP_SECONDS, RETRY_BASE_SECONDS * (2**retry_count))
    return random.uniform(0, cap_delay)


class JitterRetryCalculator:
    """Retry calculator that always uses exponential backoff with jitter."""

    def calculate_next_retry(self, retry_count: int) -> datetime:
        """Calculate next retry with exponential backoff and jitter."""
        return calculate_retry_with_jitter(retry_count)


# Default instance for convenience
default_calculator = JitterRetryCalculator()
