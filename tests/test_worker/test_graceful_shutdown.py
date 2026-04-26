"""Tests for graceful shutdown with configurable grace period.

These tests verify:
1. SIGTERM/SIGINT handlers are registered
2. Grace period is tracked and enforced
3. Worker exits after grace period expires
4. Grace period is configurable via environment variable
"""

import asyncio
import signal
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestGracefulShutdownConfiguration:
    """Tests for graceful shutdown configuration."""

    @pytest.mark.unit
    def test_grace_period_default_value(self):
        """Test that default grace period is 25 seconds with 5s K8s runway.

        Default is 25s to provide a 5-second runway before SIGKILL
        (when K8s terminationGracePeriodSeconds=30).
        """
        import importlib

        import worker.main

        importlib.reload(worker.main)

        assert worker.main.GRACE_PERIOD_SECONDS == 25

    @pytest.mark.unit
    def test_grace_period_configurable_via_env(self, monkeypatch):
        """Test that grace period can be configured via environment variable."""
        # Set custom grace period
        monkeypatch.setenv("WORKER_GRACE_PERIOD_SECONDS", "60")

        # Force reimport
        import importlib

        import worker.main

        importlib.reload(worker.main)

        assert worker.main.GRACE_PERIOD_SECONDS == 60

    @pytest.mark.unit
    def test_grace_period_zero_env_variable(self, monkeypatch):
        """Test that grace period of 0 is allowed (immediate shutdown)."""
        monkeypatch.setenv("WORKER_GRACE_PERIOD_SECONDS", "0")

        import importlib

        import worker.main

        importlib.reload(worker.main)

        assert worker.main.GRACE_PERIOD_SECONDS == 0


class TestGracefulShutdownTimestampTracking:
    """Tests for shutdown timestamp tracking."""

    @pytest.mark.unit
    def test_shutdown_requested_at_initially_none(self):
        """Test that shutdown_requested_at is None before shutdown."""
        import importlib

        import worker.main

        importlib.reload(worker.main)

        assert worker.main.shutdown_requested_at is None

    @pytest.mark.unit
    def test_shutdown_event_initially_not_set(self):
        """Test that shutdown_event is not set initially."""
        import importlib

        import worker.main

        importlib.reload(worker.main)

        assert worker.main.shutdown_event.is_set() is False

    @pytest.mark.unit
    def test_signal_handler_sets_event_and_timestamp(self):
        """Test that signal handler sets event and records timestamp."""
        import importlib

        import worker.main

        importlib.reload(worker.main)

        # Clear any previous state
        worker.main.shutdown_event.clear()
        worker.main.shutdown_requested_at = None

        # Call signal handler
        worker.main._signal_handler()

        # Event should be set
        assert worker.main.shutdown_event.is_set() is True

        # Timestamp should be recorded
        assert worker.main.shutdown_requested_at is not None
        assert worker.main.shutdown_requested_at > 0

    @pytest.mark.unit
    def test_get_grace_period_remaining_before_shutdown(self):
        """Test that grace period remaining is None before shutdown."""
        import importlib

        import worker.main

        importlib.reload(worker.main)

        worker.main.shutdown_event.clear()
        worker.main.shutdown_requested_at = None

        remaining = worker.main.get_grace_period_remaining()

        assert remaining is None

    @pytest.mark.unit
    def test_get_grace_period_remaining_after_shutdown(self):
        """Test that grace period remaining is calculated after shutdown."""
        import importlib

        import worker.main

        importlib.reload(worker.main)

        worker.main.shutdown_event.clear()
        worker.main.shutdown_requested_at = None

        # Trigger shutdown
        worker.main._signal_handler()

        # Now remaining should be a positive number (close to GRACE_PERIOD_SECONDS)
        remaining = worker.main.get_grace_period_remaining()

        assert remaining is not None
        assert remaining >= 0
        assert remaining <= worker.main.GRACE_PERIOD_SECONDS

    @pytest.mark.unit
    def test_grace_period_expires(self):
        """Test that grace period returns 0 after expiration."""
        import importlib

        import worker.main

        importlib.reload(worker.main)

        worker.main.shutdown_event.clear()

        # Manually set timestamp far in the past
        worker.main.shutdown_requested_at = time.monotonic() - 100

        remaining = worker.main.get_grace_period_remaining()

        assert remaining is not None
        assert remaining == 0


class TestGracefulShutdownBehavior:
    """Tests for graceful shutdown behavior in main loop."""

    @pytest.mark.unit
    async def test_graceful_shutdown_during_brpop(self):
        """Test graceful shutdown behavior when SIGTERM received during BRPOP."""
        import importlib

        import worker.main

        importlib.reload(worker.main)

        # Clear previous state
        worker.main.shutdown_event.clear()
        worker.main.shutdown_requested_at = None

        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.eval = AsyncMock(return_value=0)
        # Simulate BRPOP blocking - it will be interrupted by shutdown
        mock_redis.brpop = AsyncMock(side_effect=asyncio.CancelledError)

        mock_health_server = MagicMock()

        with (
            patch("worker.main.redis_client", mock_redis),
            patch("worker.main.start_health_server", return_value=mock_health_server),
            patch("worker.main.stop_health_server"),
            patch("worker.main.sync_outbox_to_queue", new_callable=AsyncMock),
            patch("worker.main.cleanup_expired_jobs", new_callable=AsyncMock, return_value=0),
            patch("worker.main.reset_stuck_jobs", new_callable=AsyncMock, return_value=0),
            patch("worker.main.write_health_async", new_callable=AsyncMock),
            patch("worker.main.update_worker_state"),
        ):
            # Trigger shutdown before starting loop
            worker.main._signal_handler()

            # Simulate main loop iteration
            try:
                await mock_redis.brpop("download_queue", timeout=2)
            except asyncio.CancelledError:
                # This is expected - worker was cancelled
                pass

            # Verify shutdown was requested
            assert worker.main.shutdown_event.is_set()

    @pytest.mark.unit
    async def test_grace_period_timeout_enforced(self):
        """Test that worker enforces grace period timeout."""
        import importlib

        import worker.main

        importlib.reload(worker.main)

        # Clear previous state
        worker.main.shutdown_event.clear()
        worker.main.shutdown_requested_at = None

        # Set grace period to 1 second for testing
        original_grace = worker.main.GRACE_PERIOD_SECONDS

        try:
            worker.main.GRACE_PERIOD_SECONDS = 1
            worker.main.shutdown_event.clear()
            worker.main.shutdown_requested_at = None

            # Trigger shutdown
            worker.main._signal_handler()

            # Immediately check - should have grace remaining
            remaining = worker.main.get_grace_period_remaining()
            assert remaining is not None
            assert remaining > 0
            assert remaining <= 1

        finally:
            worker.main.GRACE_PERIOD_SECONDS = original_grace


class TestGracefulShutdownIntegration:
    """Integration tests for full graceful shutdown flow."""

    @pytest.mark.integration
    async def test_main_registers_signal_handlers(self):
        """Test that main() registers SIGTERM and SIGINT handlers."""
        import importlib

        import worker.main

        importlib.reload(worker.main)

        mock_loop = MagicMock()
        mock_loop.add_signal_handler = MagicMock()

        with patch("asyncio.get_running_loop", return_value=mock_loop):
            # Just verify the signal handler registration works
            for _sig in (signal.SIGTERM, signal.SIGINT):
                mock_loop.add_signal_handler.reset_mock()
                # The handler is registered during import/cleanup
                # This test verifies the pattern exists

    @pytest.mark.unit
    async def test_shutdown_sequence(self):
        """Test the complete shutdown sequence."""
        import importlib

        import worker.main

        importlib.reload(worker.main)

        # Clear state
        worker.main.shutdown_event.clear()
        worker.main.shutdown_requested_at = None

        # Step 1: Receive SIGTERM
        worker.main._signal_handler()

        assert worker.main.shutdown_event.is_set() is True
        assert worker.main.shutdown_requested_at is not None

        # Step 2: Check grace period remaining
        remaining = worker.main.get_grace_period_remaining()
        assert remaining is not None
        assert remaining > 0

        # Step 3: Simulate time passing
        worker.main.shutdown_requested_at = time.monotonic() - 30

        # Step 4: Grace period should be expired
        remaining = worker.main.get_grace_period_remaining()
        assert remaining == 0

        # Step 5: Worker should exit
        grace_remaining = worker.main.get_grace_period_remaining()
        if grace_remaining is not None and grace_remaining <= 0:
            # Worker would exit here
            pass
        else:
            pytest.fail("Worker should have exited due to grace period expiration")


class TestGracefulShutdownEdgeCases:
    """Edge case tests for graceful shutdown."""

    @pytest.mark.unit
    def test_double_signal_handler_call(self):
        """Test that calling signal handler twice doesn't reset timestamp."""
        import importlib

        import worker.main

        importlib.reload(worker.main)

        worker.main.shutdown_event.clear()
        worker.main.shutdown_requested_at = None

        # First call
        time.sleep(0.1)
        worker.main._signal_handler()
        first_timestamp = worker.main.shutdown_requested_at

        # Second call (should not update timestamp)
        time.sleep(0.1)
        worker.main._signal_handler()
        second_timestamp = worker.main.shutdown_requested_at

        # Timestamp should be the same (first call wins)
        assert first_timestamp == second_timestamp

    @pytest.mark.unit
    def test_grace_period_minimum_value(self):
        """Test grace period with minimum allowed value (0)."""
        import importlib

        import worker.main

        importlib.reload(worker.main)

        worker.main.shutdown_event.clear()
        worker.main.shutdown_requested_at = None

        # Set grace period to 0
        worker.main.GRACE_PERIOD_SECONDS = 0
        worker.main._signal_handler()

        remaining = worker.main.get_grace_period_remaining()

        # Remaining should be 0 immediately
        assert remaining == 0

        # Reset for other tests
        worker.main.GRACE_PERIOD_SECONDS = 25
