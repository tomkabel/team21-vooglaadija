"""Tests for the PubSub service."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.pubsub_service import (
    CHANNEL_PREFIX,
    PubSubService,
    close_pubsub_service,
    get_pubsub_service,
)


class TestPubSubService:
    """Tests for PubSubService class."""

    @pytest.fixture
    def service(self):
        """Create a fresh PubSubService instance for each test."""
        service = PubSubService(redis_url="redis://localhost:6379")
        yield service
        # Cleanup
        service._client = None

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client."""
        mock_client = MagicMock()
        mock_client.publish = AsyncMock(return_value=1)
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.close = AsyncMock()
        return mock_client

    def test_get_channel_for_user(self, service):
        """Test channel name generation for a user."""
        user_id = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
        channel = service.get_channel_for_user(user_id)

        assert channel == f"{CHANNEL_PREFIX}:{user_id}"
        assert channel == "job_status:550e8400-e29b-41d4-a716-446655440000"

    def test_get_channel_for_user_different_users(self, service):
        """Test that different users get different channels."""
        user_id_1 = uuid.uuid4()
        user_id_2 = uuid.uuid4()

        channel_1 = service.get_channel_for_user(user_id_1)
        channel_2 = service.get_channel_for_user(user_id_2)

        assert channel_1 != channel_2
        assert user_id_1 != user_id_2

    @pytest.mark.asyncio
    async def test_publish_job_status(self, service, mock_redis_client):
        """Test publishing job status to a user's channel."""
        service._client = mock_redis_client

        user_id = uuid.uuid4()
        job_data = {
            "job_id": str(uuid.uuid4()),
            "status": "processing",
            "url": "https://youtube.com/watch?v=test",
            "file_name": None,
            "error": None,
        }

        result = await service.publish_job_status(user_id, job_data)

        assert result == 1
        mock_redis_client.publish.assert_called_once()
        call_args = mock_redis_client.publish.call_args
        assert call_args[0][0] == f"{CHANNEL_PREFIX}:{user_id}"
        published_message = json.loads(call_args[0][1])
        assert published_message["job_id"] == job_data["job_id"]
        assert published_message["status"] == job_data["status"]

    @pytest.mark.asyncio
    async def test_publish_job_status_multiple_subscribers(self, service, mock_redis_client):
        """Test publishing when multiple subscribers are listening."""
        service._client = mock_redis_client
        mock_redis_client.publish.return_value = 3  # 3 subscribers

        user_id = uuid.uuid4()
        job_data = {
            "job_id": str(uuid.uuid4()),
            "status": "completed",
        }

        result = await service.publish_job_status(user_id, job_data)

        assert result == 3

    @pytest.mark.asyncio
    async def test_health_check_success(self, service, mock_redis_client):
        """Test health check when Redis is available."""
        service._client = mock_redis_client

        result = await service.health_check()

        assert result is True
        mock_redis_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_failure(self, service, mock_redis_client):
        """Test health check when Redis is unavailable."""
        service._client = mock_redis_client
        mock_redis_client.ping = AsyncMock(side_effect=ConnectionError("Connection refused"))

        result = await service.health_check()

        assert result is False

    @pytest.mark.asyncio
    async def test_close(self, service, mock_redis_client):
        """Test closing the Redis client."""
        service._client = mock_redis_client

        await service.close()

        assert service._client is None
        mock_redis_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_when_not_initialized(self, service):
        """Test closing when client is not initialized."""
        service._client = None

        # Should not raise
        await service.close()

        assert service._client is None


class TestPubSubServiceSubscribe:
    """Tests for the subscribe method."""

    @pytest.fixture
    def service(self):
        """Create a fresh PubSubService instance for each test."""
        service = PubSubService(redis_url="redis://localhost:6379")
        yield service
        service._client = None

    @pytest.mark.asyncio
    async def test_subscribe_receives_messages(self, service):
        """Test that subscribe yields messages from the channel."""
        user_id = uuid.uuid4()
        job_data = {
            "id": str(uuid.uuid4()),
            "status": "processing",
            "url": "https://youtube.com/watch?v=test",
        }

        mock_messages = [
            {"type": "message", "data": json.dumps(job_data), "channel": f"job_status:{user_id}"},
        ]

        async def mock_listen():
            for msg in mock_messages:
                yield msg

        mock_pubsub = MagicMock()
        mock_pubsub.listen = mock_listen
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()

        mock_client = MagicMock()
        mock_client.pubsub.return_value = mock_pubsub
        service.get_client = AsyncMock(return_value=mock_client)

        messages = []
        async for data in service.subscribe(user_id):
            messages.append(data)
            break  # Only get first message

        assert len(messages) == 1
        assert messages[0]["id"] == job_data["id"]
        assert messages[0]["status"] == job_data["status"]

    @pytest.mark.asyncio
    async def test_subscribe_invalid_json(self, service):
        """Test that subscribe handles invalid JSON gracefully."""
        user_id = uuid.uuid4()

        mock_messages = [
            {"type": "message", "data": "not valid json", "channel": f"job_status:{user_id}"},
        ]

        async def mock_listen():
            for msg in mock_messages:
                yield msg

        mock_pubsub = MagicMock()
        mock_pubsub.listen = mock_listen
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()

        mock_client = MagicMock()
        mock_client.pubsub.return_value = mock_pubsub
        service.get_client = AsyncMock(return_value=mock_client)

        # Invalid JSON should be logged and skipped, not raise
        messages = []
        async for data in service.subscribe(user_id):
            messages.append(data)
            break

        # No valid messages should be yielded because JSON was invalid
        assert len(messages) == 0


class TestGlobalInstance:
    """Tests for global instance management."""

    @pytest.fixture(autouse=True)
    def reset_global(self):
        """Reset global instance before and after each test."""
        import app.services.pubsub_service as module

        module._pubsub_service = None
        yield
        module._pubsub_service = None

    def test_get_pubsub_service_returns_same_instance(self):
        """Test that get_pubsub_service returns the same instance."""
        service1 = get_pubsub_service()
        service2 = get_pubsub_service()

        assert service1 is service2

    def test_get_pubsub_service_creates_instance_if_none(self):
        """Test that get_pubsub_service creates an instance if none exists."""
        service = get_pubsub_service()

        assert service is not None
        assert isinstance(service, PubSubService)

    @pytest.mark.asyncio
    async def test_close_pubsub_service(self):
        """Test closing the global pubsub service."""
        service = get_pubsub_service()
        service._client = MagicMock()
        service._client.close = AsyncMock()

        await close_pubsub_service()

        import app.services.pubsub_service as module

        assert module._pubsub_service is None


class TestChannelPrefix:
    """Tests for channel prefix constant."""

    def test_channel_prefix_format(self):
        """Test that channel prefix follows expected format."""
        assert CHANNEL_PREFIX == "job_status"

    def test_channel_name_format(self):
        """Test full channel name format."""
        user_id = uuid.uuid4()
        expected = f"job_status:{user_id}"
        # This would be the format from get_channel_for_user
        actual = f"{CHANNEL_PREFIX}:{user_id}"
        assert actual == expected
