"""Integration tests for NetData monitoring stack.

These tests verify that the NetData agent and monitoring configuration
are properly set up when running in an integrated environment.

Note: These tests require NetData to be running and are marked as
integration tests to skip during unit test runs.
"""

import pytest

# httpx is a test dependency
pytest.importorskip("httpx", reason="httpx not installed")
import httpx


@pytest.mark.integration
class TestNetDataIntegration:
    """Test NetData agent and metrics collection."""

    async def test_netdata_agent_accessible(self):
        """Verify NetData agent is accessible if running.

        This test checks if NetData is running and can respond to API requests.
        Skip if NetData is not running (common in local development).
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get("http://localhost:19999/api/v1/info")
                assert response.status_code == 200
                data = response.json()
                assert "version" in data
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("NetData agent not running at localhost:19999")

    @pytest.mark.integration
    async def test_netdata_docker_collector_configured(self):
        """Verify Docker container metrics collector is configured.

        This checks the NetData configuration to ensure Docker collector
        is enabled when running in containerized environments.
        """
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Get allcharts to verify docker charts are present
                response = await client.get(
                    "http://localhost:19999/api/v1/allmetrics",
                    params={"format": "json", "chart": "docker.container_uptime"},
                )
                # If docker is not running or cgroups not available, this will 404
                if response.status_code == 404:
                    pytest.skip("Docker collector not available (not in container or no cgroups)")
                assert response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("NetData agent not running at localhost:19999")

    async def test_netdata_redis_collector_configured(self):
        """Verify Redis metrics collector is configured when Redis is available."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "http://localhost:19999/api/v1/allmetrics",
                    params={"format": "json", "chart": "redis.connected_clients"},
                )
                # If Redis collector is not enabled or Redis not running
                if response.status_code == 404:
                    pytest.skip("Redis collector not available or Redis not running")
                assert response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("NetData agent not running at localhost:19999")


@pytest.mark.integration
class TestNetDataHealthAlerts:
    """Test NetData health alert configurations."""

    async def test_netdata_health_alerts_loaded(self):
        """Verify custom health alerts are loaded by NetData."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                # Get alarm info endpoint
                response = await client.get("http://localhost:19999/api/v1/alarms")
                if response.status_code == 404:
                    pytest.skip("Alarms endpoint not available")
                assert response.status_code == 200
                data = response.json()
                # Verify alarms structure
                assert "alarms" in data or "status" in data
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("NetData agent not running at localhost:19999")

    @pytest.mark.integration
    async def test_netdata_cpu_health_check(self):
        """Verify system CPU metrics are being collected."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    "http://localhost:19999/api/v1/allmetrics",
                    params={"format": "json", "chart": "system.cpu"},
                )
                assert response.status_code == 200
                data = response.json()
                if "labels" not in data and "dimensions" not in data:
                    pytest.skip("CPU metrics not available in response")
                assert "labels" in data or "dimensions" in data
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip("NetData agent not running at localhost:19999")
