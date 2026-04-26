"""Tests for Sentry error tracking integration."""

import os

import pytest

# sentry_sdk is an optional dependency
sentry_sdk = pytest.importorskip("sentry_sdk", reason="sentry-sdk not installed")


@pytest.fixture(autouse=True)
def disable_sentry():
    """Disable Sentry during tests by clearing DSN."""
    original_dsn = os.environ.get("SENTRY_DSN")
    os.environ["SENTRY_DSN"] = ""  # Empty DSN prevents Sentry from initializing
    yield
    if original_dsn is not None:
        os.environ["SENTRY_DSN"] = original_dsn
    elif "SENTRY_DSN" in os.environ:
        del os.environ["SENTRY_DSN"]


@pytest.mark.integration
class TestSentryIntegration:
    """Test Sentry SDK integration with the application."""

    def test_sentry_sdk_importable(self):
        """Test that sentry_sdk can be imported."""
        assert sentry_sdk is not None

    def test_sentry_init_does_not_raise(self):
        """Test that Sentry initialization with empty DSN doesn't raise."""
        # Should not raise even with invalid/empty DSN
        sentry_sdk.init(dsn=None)

    def test_sentry_capture_exception(self):
        """Test that Sentry can capture exceptions."""
        sentry_sdk.init(dsn=None)

        # Should not raise
        try:
            raise ValueError("Test error")
        except ValueError:
            sentry_sdk.capture_exception()


@pytest.mark.integration
class TestSentryFastAPIIntegration:
    """Test Sentry integration with FastAPI."""

    def test_sentry_fastapi_integration_importable(self):
        """Test that FastAPI integration can be imported."""
        pytest.importorskip(
            "sentry_sdk.integrations.fastapi", reason="FastAPI integration not installed"
        )
        from sentry_sdk.integrations.fastapi import FastApiIntegration

        assert FastApiIntegration is not None

    def test_sentry_sqlalchemy_integration_importable(self):
        """Test that SQLAlchemy integration can be imported."""
        pytest.importorskip("sqlalchemy", reason="SQLAlchemy not installed")
        pytest.importorskip(
            "sentry_sdk.integrations.sqlalchemy", reason="SQLAlchemy integration not installed"
        )
        from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

        assert SqlalchemyIntegration is not None

    def test_sentry_redis_integration_importable(self):
        """Test that Redis integration can be imported."""
        pytest.importorskip(
            "sentry_sdk.integrations.redis", reason="Redis integration not installed"
        )
        from sentry_sdk.integrations.redis import RedisIntegration

        assert RedisIntegration is not None
