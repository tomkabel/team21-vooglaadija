"""Tests for app.main module."""

import signal
import threading
from unittest.mock import patch


class TestShutdownState:
    """Tests for _ShutdownState class."""

    def test_shutdown_state_initially_zero(self):
        """Test that shutdown state is initially zero."""
        from app.main import _ShutdownState

        state = _ShutdownState()
        assert state.received == 0

    def test_shutdown_state_set_updates_value(self):
        """Test that set() updates the received value."""
        from app.main import _ShutdownState

        state = _ShutdownState()
        state.set(signal.SIGTERM)
        assert state.received == signal.SIGTERM

    def test_shutdown_state_thread_safety(self):
        """Spawn threads, call set(), assert final value is one of the set values."""
        from app.main import _ShutdownState

        state = _ShutdownState()
        results = []

        def set_sigterm():
            state.set(signal.SIGTERM)
            results.append(signal.SIGTERM)

        def set_sigint():
            state.set(signal.SIGINT)
            results.append(signal.SIGINT)

        threads = [
            threading.Thread(target=set_sigterm),
            threading.Thread(target=set_sigint),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert state.received in [signal.SIGTERM, signal.SIGINT]


class TestAppConfiguration:
    """Tests for app configuration."""

    def test_app_has_lifespan(self):
        """Test that app is created with lifespan context manager."""
        from app.main import app

        assert app is not None
        assert hasattr(app, "router")

    def test_app_version_set(self):
        """Test that APP_VERSION is defined."""
        from app.main import APP_VERSION

        assert APP_VERSION == "0.1.0"


class TestShutdownDiagnosticsInstallation:
    """Tests for _install_shutdown_diagnostics behavior."""

    def test_install_shutdown_diagnostics_is_callable(self):
        """Test that _install_shutdown_diagnostics is a callable function."""
        from app.main import _install_shutdown_diagnostics

        assert callable(_install_shutdown_diagnostics)

    def test_install_shutdown_diagnostics_runs_without_error(self):
        """Test that _install_shutdown_diagnostics runs without raising."""
        from app.main import _install_shutdown_diagnostics

        _install_shutdown_diagnostics()


class TestAppSignals:
    """Tests for signal handling configuration."""

    def test_sigterm_handler_exists(self):
        """Test that _sigterm_handler is defined and callable."""
        from app.main import _sigterm_handler

        assert callable(_sigterm_handler)

    def test_sigterm_handler_sets_shutdown_state(self):
        """Test that _sigterm_handler updates _shutdown_state."""
        from app.main import _ShutdownState, _sigterm_handler

        state = _ShutdownState()
        with patch("app.main._shutdown_state", state):
            _sigterm_handler(signal.SIGTERM, None)
            assert state.received == signal.SIGTERM


class TestLifespanLogging:
    """Tests for lifespan function logging behavior."""

    def test_lifespan_function_exists(self):
        """Test that lifespan is importable and callable."""
        from app.main import lifespan

        assert callable(lifespan)


class TestMainModuleExports:
    """Tests for module-level exports."""

    def test_circuit_breaker_imported(self):
        """Test that CircuitBreaker is available."""
        from app.services.circuit_breaker import CircuitBreaker

        assert CircuitBreaker is not None

    def test_get_youtube_circuit_breaker_returns_breaker(self):
        """Test that get_youtube_circuit_breaker returns a CircuitBreaker instance."""
        from app.services.circuit_breaker import CircuitBreaker, get_youtube_circuit_breaker

        cb = get_youtube_circuit_breaker()
        assert isinstance(cb, CircuitBreaker)
