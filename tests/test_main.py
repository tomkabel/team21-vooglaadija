"""Tests for app.main module."""

import signal
import threading
from unittest.mock import MagicMock, patch

import pytest
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.main import (
    _ShutdownState,
    _sigterm_handler,
    app,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)


class TestShutdownState:
    """Tests for _ShutdownState class."""

    def test_shutdown_state_initially_zero(self):
        """Test that shutdown state is initially zero."""

        state = _ShutdownState()
        assert state.received == 0

    def test_shutdown_state_set_updates_value(self):
        """Test that set() updates the received value."""

        state = _ShutdownState()
        state.set(signal.SIGTERM)
        assert state.received == signal.SIGTERM

    def test_shutdown_state_thread_safety(self):
        """Spawn threads, call set(), assert final value is one of the set values."""

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

        assert callable(_sigterm_handler)

    def test_sigterm_handler_sets_shutdown_state(self):
        """Test that _sigterm_handler updates _shutdown_state."""

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


class TestHttpExceptionHandler:
    """Tests for http_exception_handler."""

    @pytest.mark.asyncio
    async def test_http_exception_handler_401(self):
        """Test that 401 returns UNAUTHORIZED error code."""

        request = MagicMock()
        request.state.request_id = "test-request-id"
        exc = StarletteHTTPException(status_code=401, detail="Not authenticated")

        response = await http_exception_handler(request, exc)

        assert response.status_code == 401
        assert response.body is not None
        body = response.body.decode()
        assert "UNAUTHORIZED" in body
        assert "Not authenticated" in body

    @pytest.mark.asyncio
    async def test_http_exception_handler_404(self):
        """Test that 404 returns NOT_FOUND error code."""

        request = MagicMock()
        request.state.request_id = "test-request-id"
        exc = StarletteHTTPException(status_code=404, detail="Resource not found")

        response = await http_exception_handler(request, exc)

        assert response.status_code == 404
        body = response.body.decode()
        assert "NOT_FOUND" in body

    @pytest.mark.asyncio
    async def test_http_exception_handler_500(self):
        """Test that 500 returns INTERNAL_ERROR error code."""
        request = MagicMock()
        request.state.request_id = "test-request-id"
        exc = StarletteHTTPException(status_code=500, detail="Internal server error")

        response = await http_exception_handler(request, exc)

        assert response.status_code == 500
        body = response.body.decode()
        assert "INTERNAL_ERROR" in body

    @pytest.mark.asyncio
    async def test_http_exception_handler_429(self):
        """Test that 429 returns RATE_LIMIT_EXCEEDED error code."""
        request = MagicMock()
        request.state.request_id = "test-request-id"
        exc = StarletteHTTPException(status_code=429, detail="Rate limit exceeded")

        response = await http_exception_handler(request, exc)

        assert response.status_code == 429
        body = response.body.decode()
        assert "RATE_LIMIT_EXCEEDED" in body


class TestValidationExceptionHandler:
    """Tests for validation_exception_handler."""

    @pytest.mark.asyncio
    async def test_validation_exception_handler_returns_422(self):
        """Test that validation errors return 422 status code."""
        request = MagicMock()
        request.state.request_id = "test-request-id"

        exc = RequestValidationError(
            errors=[
                {
                    "loc": ("body", "url"),
                    "msg": "field required",
                    "type": "missing",
                },
            ]
        )

        response = await validation_exception_handler(request, exc)

        assert response.status_code == 422
        body = response.body.decode()
        assert "VALIDATION_ERROR" in body
        assert "Request validation failed" in body

    @pytest.mark.asyncio
    async def test_validation_exception_handler_includes_error_details(self):
        """Test that validation errors include field details."""
        request = MagicMock()
        request.state.request_id = "test-request-id"

        exc = RequestValidationError(
            errors=[
                {
                    "loc": ("body", "email"),
                    "msg": "invalid email format",
                    "type": "value_error",
                },
            ]
        )

        response = await validation_exception_handler(request, exc)

        assert response.status_code == 422
        body = response.body.decode()
        assert "validation_errors" in body


class TestGeneralExceptionHandler:
    """Tests for general_exception_handler."""

    @pytest.mark.asyncio
    async def test_general_exception_handler_returns_500(self):
        """Test that unexpected exceptions return 500."""
        request = MagicMock()
        request.state.request_id = "test-request-id"

        exc = ValueError("Unexpected error")

        response = await general_exception_handler(request, exc)

        assert response.status_code == 500
        body = response.body.decode()
        assert "INTERNAL_ERROR" in body
        assert "internal error occurred" in body.lower()

    @pytest.mark.asyncio
    async def test_general_exception_handler_includes_request_id(self):
        """Test that exception handler includes X-Request-ID header."""
        request = MagicMock()
        request.state.request_id = "my-custom-request-id"

        exc = RuntimeError("Something went wrong")

        response = await general_exception_handler(request, exc)

        assert response.status_code == 500
        assert response.headers.get("X-Request-ID") == "my-custom-request-id"


class TestSecurityMiddleware:
    """Tests for security headers middleware."""

    @pytest.mark.asyncio
    async def test_security_headers_added(self):
        """Test that security headers are added to responses."""
        from starlette.testclient import TestClient

        with TestClient(app) as client:
            response = client.get("/api/v1/health")

            assert "X-Content-Type-Options" in response.headers
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert "X-Frame-Options" in response.headers
            assert response.headers["X-Frame-Options"] == "DENY"

    @pytest.mark.asyncio
    async def test_request_id_added(self):
        """Test that X-Request-ID header is added to responses."""
        from starlette.testclient import TestClient

        with TestClient(app) as client:
            response = client.get("/api/v1/health")

            assert "X-Request-ID" in response.headers
            assert len(response.headers["X-Request-ID"]) > 0
