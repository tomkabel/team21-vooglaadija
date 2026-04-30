"""Redis Pub/Sub service for job status broadcasting.

This module provides a Redis-based pub/sub mechanism for real-time
job status updates, replacing the polling-based SSE implementation.
"""

import json
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import redis.asyncio as aioredis

from app.config import settings
from app.logging_config import get_logger

logger = get_logger(__name__)

CHANNEL_PREFIX = "job_status"


class PubSubService:
    """Redis Pub/Sub service for job status broadcasting.

    This service provides:
    - publish_job_status(): Publishes job status updates to user-specific channels
    - subscribe(): Async generator that yields job status updates from Redis pub/sub

    Channel Pattern: job_status:{user_id}
    Message Format: JSON with job_id, status, url, file_name, error, created_at, updated_at
    """

    def __init__(self, redis_url: str | None = None):
        """Initialize the PubSubService.

        Args:
            redis_url: Redis connection URL. Defaults to settings.redis_url.
        """
        self.redis_url = redis_url or settings.redis_url
        self._client: aioredis.Redis | None = None

    async def get_client(self) -> aioredis.Redis:
        """Get or create Redis client with connection pooling.

        Returns:
            Redis client instance.
        """
        if self._client is None:
            self._client = aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                max_connections=20,
            )
        return self._client

    async def close(self) -> None:
        """Close the Redis client connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None

    def get_channel_for_user(self, user_id: uuid.UUID) -> str:
        """Get the pub/sub channel name for a user.

        Args:
            user_id: The user's UUID.

        Returns:
            Channel name in format 'job_status:{user_id}'.
        """
        return f"{CHANNEL_PREFIX}:{user_id}"

    async def publish_job_status(self, user_id: uuid.UUID, job_data: dict) -> int:
        """Publish a job status update to a user's channel.

        Args:
            user_id: The user's UUID to publish to.
            job_data: Dictionary containing job information (job_id, status, url, etc.)

        Returns:
            Number of subscribers that received the message.
        """
        client = await self.get_client()
        channel = self.get_channel_for_user(user_id)
        message = json.dumps(job_data, default=str)
        result = await client.publish(channel, message)

        logger.debug(
            "pubsub_message_published",
            channel=channel,
            job_id=job_data.get("id"),
            status=job_data.get("status"),
            subscribers=result,
        )

        return result

    @asynccontextmanager
    async def subscription(
        self, user_id: uuid.UUID
    ) -> AsyncGenerator[aioredis.client.PubSub, None]:
        """Create a subscription context for a user's channel.

        Args:
            user_id: The user's UUID to subscribe to.

        Yields:
            PubSub client instance.
        """
        client = await self.get_client()
        channel = self.get_channel_for_user(user_id)
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)

        logger.debug("pubsub_subscription_started", channel=channel)

        try:
            yield pubsub
        finally:
            try:
                await pubsub.unsubscribe(channel)
            except Exception as e:
                logger.exception("pubsub_unsubscribe_failed", channel=channel, error=str(e))
            await pubsub.close()
            logger.debug("pubsub_subscription_ended", channel=channel)

    async def subscribe(self, user_id: uuid.UUID) -> AsyncGenerator[dict, None]:
        """Subscribe to a user's job status channel.

        This is an async generator that yields job status updates
        as they are published to the user's channel.

        Args:
            user_id: The user's UUID to subscribe to.

        Yields:
            Dictionary containing job information.
        """
        async with self.subscription(user_id) as pubsub:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        if isinstance(data, dict):
                            logger.debug(
                                "pubsub_message_received",
                                channel=message["channel"],
                                job_id=data.get("id"),
                            )
                            yield data
                        else:
                            logger.warning(
                                "pubsub_non_dict_payload",
                                channel=message["channel"],
                                payload_type=type(data).__name__,
                                payload=str(data)[:200],
                            )
                            yield {"job_id": None, "_raw": data}
                    except json.JSONDecodeError as e:
                        logger.error(
                            "pubsub_invalid_json",
                            channel=message["channel"],
                            error=str(e),
                            data=message["data"][:200],
                        )

    async def health_check(self) -> bool:
        """Check if Redis connection is healthy.

        Returns:
            True if Redis is reachable, False otherwise.
        """
        try:
            client = await self.get_client()
            await client.ping()
            return True
        except Exception as e:
            logger.error("pubsub_health_check_failed", error=str(e))
            return False


_pubsub_service: PubSubService | None = None


def get_pubsub_service() -> PubSubService:
    """Get the global PubSubService instance.

    Returns:
        The global PubSubService instance.
    """
    global _pubsub_service  # noqa: PLW0603
    if _pubsub_service is None:
        _pubsub_service = PubSubService()
    return _pubsub_service


async def close_pubsub_service() -> None:
    """Close the global PubSubService instance."""
    global _pubsub_service  # noqa: PLW0603
    if _pubsub_service is not None:
        await _pubsub_service.close()
        _pubsub_service = None
