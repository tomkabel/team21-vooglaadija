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


class TestPubSubServiceGetClient:
    """Tests for PubSubService.get_client() lazy initialization."""

    @pytest.fixture
    def service(self):
        """Create a fresh PubSubService instance for each test."""
        service = PubSubService(redis_url="redis://localhost:6379")
        yield service
        service._client = None

    @pytest.mark.asyncio
    async def test_get_client_creates_client_when_none(self, service):
        """Test that get_client creates a Redis client when none exists."""
        from unittest.mock import patch

        assert service._client is None

        mock_redis = MagicMock()
        with patch("redis.asyncio.from_url", return_value=mock_redis) as mock_from_url:
            client = await service.get_client()

        assert client is mock_redis
        assert service._client is mock_redis
        mock_from_url.assert_called_once_with(
            "redis://localhost:6379",
            decode_responses=True,
            max_connections=20,
        )

    @pytest.mark.asyncio
    async def test_get_client_returns_existing_client(self, service):
        """Test that get_client returns the existing client without creating a new one."""
        from unittest.mock import patch

        mock_redis = MagicMock()
        service._client = mock_redis

        with patch("redis.asyncio.from_url") as mock_from_url:
            client = await service.get_client()

        assert client is mock_redis
        mock_from_url.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_client_uses_settings_redis_url_when_none_provided(self):
        """Test that PubSubService uses settings.redis_url when no URL provided."""
        from unittest.mock import patch

        from app.services.pubsub_service import PubSubService

        with patch("app.services.pubsub_service.settings") as mock_settings:
            mock_settings.redis_url = "redis://settings-host:6379"
            service = PubSubService()  # No redis_url arg

        assert service.redis_url == "redis://settings-host:6379"


class TestPubSubServiceSubscriptionContextManager:
    """Tests for PubSubService.subscription() context manager."""

    @pytest.fixture
    def service(self):
        """Create a fresh PubSubService instance for each test."""
        service = PubSubService(redis_url="redis://localhost:6379")
        yield service
        service._client = None

    @pytest.mark.asyncio
    async def test_subscription_subscribes_and_unsubscribes(self, service):
        """Test that subscription() subscribes on enter and unsubscribes on exit."""
        user_id = uuid.uuid4()
        expected_channel = f"job_status:{user_id}"

        mock_pubsub = MagicMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()

        mock_client = MagicMock()
        mock_client.pubsub.return_value = mock_pubsub
        service._client = mock_client

        async with service.subscription(user_id) as pubsub_instance:
            mock_pubsub.subscribe.assert_called_once_with(expected_channel)
            assert pubsub_instance is mock_pubsub

        mock_pubsub.unsubscribe.assert_called_once_with(expected_channel)
        mock_pubsub.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscription_closes_even_when_unsubscribe_fails(self, service):
        """Test that subscription() calls close() even when unsubscribe fails."""
        user_id = uuid.uuid4()

        mock_pubsub = MagicMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock(side_effect=Exception("Unsubscribe failed"))
        mock_pubsub.close = AsyncMock()

        mock_client = MagicMock()
        mock_client.pubsub.return_value = mock_pubsub
        service._client = mock_client

        # Should not raise despite unsubscribe failing
        async with service.subscription(user_id):
            pass

        mock_pubsub.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_subscription_yields_pubsub_instance(self, service):
        """Test that subscription yields the pubsub client instance."""
        user_id = uuid.uuid4()

        mock_pubsub = MagicMock()
        mock_pubsub.subscribe = AsyncMock()
        mock_pubsub.unsubscribe = AsyncMock()
        mock_pubsub.close = AsyncMock()

        mock_client = MagicMock()
        mock_client.pubsub.return_value = mock_pubsub
        service._client = mock_client

        yielded_pubsub = None
        async with service.subscription(user_id) as ps:
            yielded_pubsub = ps

        assert yielded_pubsub is mock_pubsub


class TestPubSubServiceSubscribeEdgeCases:
    """Edge case tests for PubSubService.subscribe()."""

    @pytest.fixture
    def service(self):
        """Create a fresh PubSubService instance for each test."""
        service = PubSubService(redis_url="redis://localhost:6379")
        yield service
        service._client = None

    @pytest.mark.asyncio
    async def test_subscribe_skips_non_message_type_events(self, service):
        """Test that subscribe() skips events that are not of type 'message'."""
        user_id = uuid.uuid4()

        # 'subscribe' and 'psubscribe' are Redis internal message types
        mock_messages = [
            {"type": "subscribe", "data": 1, "channel": f"job_status:{user_id}"},
            {"type": "psubscribe", "data": 1, "channel": f"job_status:{user_id}"},
            {
                "type": "message",
                "data": json.dumps({"id": str(uuid.uuid4()), "status": "processing"}),
                "channel": f"job_status:{user_id}",
            },
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

        # Only the "message" type should be yielded (not subscribe/psubscribe)
        assert len(messages) == 1

    @pytest.mark.asyncio
    async def test_subscribe_yields_raw_for_non_dict_json(self, service):
        """Test that subscribe() yields raw wrapper for non-dict JSON payloads."""
        user_id = uuid.uuid4()

        # Valid JSON but not a dict (e.g., list or string)
        non_dict_payload = ["item1", "item2"]
        mock_messages = [
            {
                "type": "message",
                "data": json.dumps(non_dict_payload),
                "channel": f"job_status:{user_id}",
            },
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

        # Non-dict JSON should yield a wrapper with {"job_id": None, "_raw": ...}
        assert len(messages) == 1
        assert messages[0]["job_id"] is None
        assert "_raw" in messages[0]
        assert messages[0]["_raw"] == non_dict_payload

    @pytest.mark.asyncio
    async def test_subscribe_yields_dict_message_correctly(self, service):
        """Test that subscribe() yields dict messages as-is."""
        user_id = uuid.uuid4()
        job_id = str(uuid.uuid4())

        job_data = {
            "id": job_id,
            "status": "completed",
            "url": "https://youtube.com/watch?v=abc",
            "file_name": "video.mp4",
        }

        mock_messages = [
            {
                "type": "message",
                "data": json.dumps(job_data),
                "channel": f"job_status:{user_id}",
            },
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

        assert len(messages) == 1
        assert messages[0]["id"] == job_id
        assert messages[0]["status"] == "completed"
        assert messages[0]["file_name"] == "video.mp4"

    @pytest.mark.asyncio
    async def test_subscribe_multiple_valid_messages(self, service):
        """Test that subscribe() yields all valid messages in sequence."""
        user_id = uuid.uuid4()
        job_id = str(uuid.uuid4())

        messages_data = [
            {"id": job_id, "status": "pending"},
            {"id": job_id, "status": "processing"},
            {"id": job_id, "status": "completed"},
        ]

        mock_messages = [
            {
                "type": "message",
                "data": json.dumps(d),
                "channel": f"job_status:{user_id}",
            }
            for d in messages_data
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

        received = []
        async for data in service.subscribe(user_id):
            received.append(data)

        assert len(received) == 3
        assert received[0]["status"] == "pending"
        assert received[1]["status"] == "processing"
        assert received[2]["status"] == "completed"


class TestClosePubSubServiceEdgeCases:
    """Additional edge case tests for close_pubsub_service."""

    @pytest.fixture(autouse=True)
    def reset_global(self):
        """Reset global instance before and after each test."""
        import app.services.pubsub_service as module

        module._pubsub_service = None
        yield
        module._pubsub_service = None

    @pytest.mark.asyncio
    async def test_close_pubsub_service_when_none(self):
        """Test that close_pubsub_service does not raise when service is None."""
        import app.services.pubsub_service as module

        assert module._pubsub_service is None

        # Should not raise
        await close_pubsub_service()

        assert module._pubsub_service is None

    @pytest.mark.asyncio
    async def test_close_pubsub_service_sets_global_to_none(self):
        """Test that close_pubsub_service sets the global to None after closing."""
        import app.services.pubsub_service as module

        # Create a service with a mock client
        service = get_pubsub_service()
        mock_client = MagicMock()
        mock_client.close = AsyncMock()
        service._client = mock_client

        assert module._pubsub_service is not None

        await close_pubsub_service()

        assert module._pubsub_service is None
        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_pubsub_service_idempotent(self):
        """Test that close_pubsub_service can be called multiple times safely."""
        get_pubsub_service()

        # First call
        await close_pubsub_service()
        # Second call should not raise
        await close_pubsub_service()


class TestPublishJobStatusSerializes:
    """Tests for publish_job_status serialization behavior."""

    @pytest.fixture
    def service(self):
        """Create a fresh PubSubService instance for each test."""
        service = PubSubService(redis_url="redis://localhost:6379")
        yield service
        service._client = None

    @pytest.mark.asyncio
    async def test_publish_job_status_serializes_non_string_values(self, service):
        """Test that publish_job_status serializes non-string values using default=str."""
        import uuid as _uuid

        mock_redis_client = MagicMock()
        mock_redis_client.publish = AsyncMock(return_value=0)
        service._client = mock_redis_client

        user_id = _uuid.uuid4()
        job_id = _uuid.uuid4()
        # Include a UUID (not JSON-serializable by default)
        job_data = {"id": job_id, "status": "pending"}

        result = await service.publish_job_status(user_id, job_data)

        assert result == 0
        call_args = mock_redis_client.publish.call_args
        # Should have serialized to valid JSON without raising
        published = json.loads(call_args[0][1])
        assert published["id"] == str(job_id)

    @pytest.mark.asyncio
    async def test_publish_job_status_returns_subscriber_count(self, service):
        """Test that publish_job_status returns 0 when no subscribers."""
        mock_redis_client = MagicMock()
        mock_redis_client.publish = AsyncMock(return_value=0)
        service._client = mock_redis_client

        user_id = uuid.uuid4()
        result = await service.publish_job_status(user_id, {"status": "pending"})

        assert result == 0
