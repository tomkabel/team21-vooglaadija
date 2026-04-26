"""
Circuit Breaker pattern for external API calls.

Based on 2026 industry best practices for resilience engineering.
Prevents thundering herd problem when external services (like YouTube) are down.

States:
- CLOSED: Normal operation, requests pass through
- OPEN: Circuit is tripped, requests fail immediately
- HALF_OPEN: Testing if service recovered, limited requests pass through

Transitions:
- CLOSED → OPEN: After failure_threshold consecutive failures
- OPEN → HALF_OPEN: After reset_timeout elapsed
- HALF_OPEN → CLOSED: After success_threshold consecutive successes
- HALF_OPEN → OPEN: After failure in half-open state
"""

import asyncio
import os
import time
from enum import Enum
from typing import Any

from app.logging_config import get_logger

logger = get_logger(__name__)


class CircuitState(Enum):
    """Circuit breaker states."""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit tripped, failing fast
    HALF_OPEN = "half_open"  # Testing recovery


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open and request cannot proceed."""

    def __init__(self, service_name: str, reset_timeout: float):
        self.service_name = service_name
        self.reset_timeout = reset_timeout
        super().__init__(
            f"Circuit breaker is OPEN for {service_name}. "
            f"Service will be retried after {reset_timeout}s cooldown."
        )


class CircuitBreaker:
    """
    Circuit breaker implementation for external service calls.

    Tracks failures and opens the circuit when threshold is exceeded,
    preventing cascading failures and thundering herd problems.
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        success_threshold: int = 3,
        reset_timeout: float = 30.0,
        half_open_max_calls: int = 3,
    ):
        """
        Initialize circuit breaker.

        Args:
            name: Service name for logging
            failure_threshold: Consecutive failures before opening circuit
            success_threshold: Consecutive successes to close circuit from half-open
            reset_timeout: Seconds before attempting recovery (open → half-open)
            half_open_max_calls: Max concurrent calls in half-open state
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.reset_timeout = reset_timeout
        self.half_open_max_calls = half_open_max_calls

        # State tracking
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float | None = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()

    @property
    def state(self) -> CircuitState:
        """Get current circuit state, checking for timeout transition.

        Note: This property only checks for transitions but does NOT modify state.
        Use _check_and_transition() or can_execute() for state mutations.
        """
        if self._state == CircuitState.OPEN and self._last_failure_time is not None:
            # Check if reset timeout has elapsed
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self.reset_timeout:
                return CircuitState.HALF_OPEN
        return self._state

    def _check_and_transition_to_half_open(self) -> CircuitState:
        """Check timeout and transition OPEN→HALF_OPEN under lock.

        Returns the current state after potential transition.
        """
        if self._state == CircuitState.OPEN and self._last_failure_time is not None:
            elapsed = time.monotonic() - self._last_failure_time
            if elapsed >= self.reset_timeout:
                logger.info(
                    "circuit_breaker_reset_timeout_elapsed",
                    service=self.name,
                    elapsed_seconds=elapsed,
                    reset_timeout=self.reset_timeout,
                )
                self._state = CircuitState.HALF_OPEN
                self._last_failure_time = None  # Reset timer
        return self._state

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed (normal operation)."""
        return self.state == CircuitState.CLOSED

    @property
    def is_open(self) -> bool:
        """Check if circuit is open (failing fast)."""
        return self.state == CircuitState.OPEN

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open (testing recovery)."""
        return self.state == CircuitState.HALF_OPEN

    async def can_execute(self) -> bool:
        """Check if request can proceed."""
        async with self._lock:
            # First: check for timeout-based transition OPEN→HALF_OPEN under lock
            current_state = self._check_and_transition_to_half_open()

            if current_state == CircuitState.CLOSED:
                return True

            if current_state == CircuitState.OPEN:
                return False

            # HALF_OPEN: allow limited concurrent calls and reserve a slot
            if current_state == CircuitState.HALF_OPEN:
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False

            return False

    async def record_success(self) -> None:
        """Record a successful call."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                self._half_open_calls = max(0, self._half_open_calls - 1)
                logger.info(
                    "circuit_breaker_success_in_half_open",
                    service=self.name,
                    success_count=self._success_count,
                    success_threshold=self.success_threshold,
                )

                if self._success_count >= self.success_threshold:
                    logger.info(
                        "circuit_breaker_closing",
                        service=self.name,
                        success_count=self._success_count,
                    )
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    self._half_open_calls = 0
            elif self._state == CircuitState.CLOSED:
                # Reset failure count on success
                if self._failure_count > 0:
                    logger.info(
                        "circuit_breaker_failure_count_reset",
                        service=self.name,
                        previous_failures=self._failure_count,
                    )
                self._failure_count = 0

    async def record_failure(self, error: Exception | None = None) -> None:
        """Record a failed call."""
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()

            error_msg = str(error)[:100] if error else "unknown"
            logger.warning(
                "circuit_breaker_failure_recorded",
                service=self.name,
                failure_count=self._failure_count,
                failure_threshold=self.failure_threshold,
                error=error_msg,
                current_state=self._state.value,
            )

            if self._state == CircuitState.HALF_OPEN:
                self._half_open_calls = max(0, self._half_open_calls - 1)
                logger.warning(
                    "circuit_breaker_opening_from_half_open",
                    service=self.name,
                    failure_count=self._failure_count,
                )
                self._state = CircuitState.OPEN
                self._success_count = 0
                self._half_open_calls = 0
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.failure_threshold:
                    logger.warning(
                        "circuit_breaker_opening",
                        service=self.name,
                        failure_count=self._failure_count,
                        failure_threshold=self.failure_threshold,
                    )
                    self._state = CircuitState.OPEN

    async def execute(self, func, *args, **kwargs) -> Any:
        """
        Execute a function with circuit breaker protection.

        Args:
            func: Async function to execute
            *args: Positional arguments for func
            **kwargs: Keyword arguments for func

        Returns:
            Result from func if successful

        Raises:
            CircuitBreakerOpenError: If circuit is open
            Exception: Re-raises any exception from func
        """
        if not await self.can_execute():
            raise CircuitBreakerOpenError(self.name, self.reset_timeout)

        try:
            result = await func(*args, **kwargs)
            await self.record_success()
            return result

        except Exception as e:
            await self.record_failure(e)
            raise

    def get_stats(self) -> dict[str, Any]:
        """Get circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "failure_threshold": self.failure_threshold,
            "success_threshold": self.success_threshold,
            "reset_timeout": self.reset_timeout,
            "last_failure_time": self._last_failure_time,
        }


# Global circuit breaker for YouTube API
_youtube_circuit_breaker: CircuitBreaker | None = None


def get_youtube_circuit_breaker() -> CircuitBreaker:
    """Get or create the YouTube API circuit breaker."""
    global _youtube_circuit_breaker  # noqa: PLW0603 - singleton pattern requires module-level state
    if _youtube_circuit_breaker is None:
        _youtube_circuit_breaker = CircuitBreaker(
            name="youtube_api",
            failure_threshold=int(os.environ.get("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5")),
            success_threshold=int(os.environ.get("CIRCUIT_BREAKER_SUCCESS_THRESHOLD", "3")),
            reset_timeout=float(os.environ.get("CIRCUIT_BREAKER_RESET_TIMEOUT", "30.0")),
            half_open_max_calls=int(os.environ.get("CIRCUIT_BREAKER_HALF_OPEN_MAX_CALLS", "3")),
        )
    return _youtube_circuit_breaker


async def extract_media_with_circuit_breaker(url: str, storage_path: str) -> tuple[str, str]:
    """
    Extract media URL with circuit breaker protection.

    Wraps extract_media_url with circuit breaker to prevent
    hammering YouTube during outages.
    """
    cb = get_youtube_circuit_breaker()

    logger.debug(
        "circuit_breaker_executing_youtube_extraction",
        circuit_state=cb.state.value,
        url=url[:50],
    )

    result: tuple[str, str] = await cb.execute(
        _extract_media_url_internal,
        url,
        storage_path,
    )
    return result


async def _extract_media_url_internal(url: str, storage_path: str) -> tuple[str, str]:
    """Internal extraction without circuit breaker (called by circuit breaker)."""
    from app.services.yt_dlp_service import extract_media_url

    return await extract_media_url(url, storage_path)


def get_circuit_breaker_stats() -> dict[str, Any]:
    """Get stats for the YouTube circuit breaker."""
    return get_youtube_circuit_breaker().get_stats()
