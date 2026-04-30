"""SSE (Server-Sent Events) routes for real-time job status updates.

This module provides SSE endpoints that subscribe to Redis Pub/Sub for
real-time job status updates, with fallback to polling if pub/sub fails.
"""

import asyncio
import json
import uuid
from collections import OrderedDict
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Request
from sqlalchemy import select
from sse_starlette import EventSourceResponse, ServerSentEvent

from app.api.dependencies import CurrentUserFromCookie
from app.database import get_async_session_factory
from app.logging_config import get_logger
from app.models.download_job import DownloadJob
from app.services.pubsub_service import get_pubsub_service

router = APIRouter(prefix="/web", tags=["sse"])

logger = get_logger(__name__)

MAX_SEEN_JOBS = 100
POLL_INTERVAL_SECONDS = 15
MAX_PUBSUB_RECONNECT_ATTEMPTS = 3
PUBSUB_RECONNECT_DELAY_SECONDS = 1


async def _job_to_sse_data(job: DownloadJob) -> dict:
    """Convert a DownloadJob model to SSE data dictionary."""
    return {
        "id": str(job.id),
        "url": job.url,
        "status": job.status,
        "file_name": job.file_name,
        "error": job.error,
        "created_at": job.created_at.isoformat() if job.created_at else None,
        "updated_at": job.updated_at.isoformat() if job.updated_at else None,
    }


async def _subscribe_to_pubsub(
    pubsub,
    user_id: uuid.UUID,
    last_seen_job_ids: OrderedDict[str, str],
) -> AsyncGenerator[ServerSentEvent, None]:
    """Inner generator that yields events from pubsub subscription."""
    async for job_data in pubsub.subscribe(user_id):
        job_id = job_data.get("id")

        if job_id:
            job_updated_at = job_data.get("updated_at")
            status_key = f"{job_id}:{job_updated_at}"
            if job_id not in last_seen_job_ids or last_seen_job_ids[job_id] != status_key:
                last_seen_job_ids[job_id] = status_key
                last_seen_job_ids.move_to_end(job_id)

                while len(last_seen_job_ids) > MAX_SEEN_JOBS:
                    last_seen_job_ids.popitem(last=False)

                yield ServerSentEvent(
                    event="job_update",
                    data=json.dumps(job_data),
                )


async def pubsub_event_generator(
    request: Request,
    user_id: uuid.UUID,
) -> AsyncGenerator[ServerSentEvent, None]:
    """SSE event generator that subscribes to Redis Pub/Sub for real-time updates.

    This generator subscribes to the user's Redis pub/sub channel and yields
    SSE events as job status updates are received. It includes reconnection
    logic to handle transient disconnections.

    Yields:
        ServerSentEvent objects with job_update events.
    """
    pubsub = get_pubsub_service()
    reconnect_attempts = 0
    last_seen_job_ids: OrderedDict[str, str] = OrderedDict()

    while reconnect_attempts < MAX_PUBSUB_RECONNECT_ATTEMPTS:
        if await request.is_disconnected():
            break

        try:
            async for event in _subscribe_to_pubsub(pubsub, user_id, last_seen_job_ids):
                yield event
            break

        except asyncio.CancelledError:
            break
        except Exception as e:
            reconnect_attempts += 1
            logger.warning(
                "pubsub_subscription_error",
                user_id=str(user_id),
                attempt=reconnect_attempts,
                error=str(e),
            )

            if reconnect_attempts < MAX_PUBSUB_RECONNECT_ATTEMPTS:
                await asyncio.sleep(PUBSUB_RECONNECT_DELAY_SECONDS * reconnect_attempts)
            else:
                logger.error("pubsub_max_reconnect_attempts", user_id=str(user_id))
                break


async def fallback_polling_generator(
    request: Request,
    session_factory,
    user_id: uuid.UUID,
) -> AsyncGenerator[ServerSentEvent, None]:
    """Fallback polling generator when Pub/Sub is unavailable.

    This is a less efficient fallback that polls the database periodically.
    It should only be used when Redis pub/sub connection fails.
    """
    seen_jobs: OrderedDict[str, str] = OrderedDict()

    try:
        while True:
            if await request.is_disconnected():
                break

            async with session_factory() as db:
                query = (
                    select(DownloadJob)
                    .where(DownloadJob.user_id == user_id)
                    .order_by(DownloadJob.updated_at.desc())
                    .limit(50)
                )
                result = await db.execute(query)
                jobs = result.scalars().all()

                for job in jobs:
                    job_id_str = str(job.id)
                    job_updated_at = job.updated_at.isoformat() if job.updated_at else None
                    status_key = f"{job_id_str}:{job_updated_at}"

                    if job_id_str not in seen_jobs or seen_jobs[job_id_str] != status_key:
                        seen_jobs[job_id_str] = status_key
                        seen_jobs.move_to_end(job_id_str)

                        # Trim to max size
                        while len(seen_jobs) > MAX_SEEN_JOBS:
                            seen_jobs.popitem(last=False)

                        yield ServerSentEvent(
                            event="job_update",
                            data=json.dumps(
                                {
                                    "id": str(job.id),
                                    "url": job.url,
                                    "status": job.status,
                                    "file_name": job.file_name,
                                    "error": job.error,
                                    "created_at": job.created_at.isoformat()
                                    if job.created_at
                                    else None,
                                }
                            ),
                        )

            await asyncio.sleep(POLL_INTERVAL_SECONDS)
    except asyncio.CancelledError:
        # Client disconnected — normal shutdown
        pass


async def event_generator(
    request: Request,
    session_factory,
    user_id: uuid.UUID,
) -> AsyncGenerator[ServerSentEvent, None]:
    """SSE event generator that prioritizes Pub/Sub with polling fallback.

    This generator first attempts to subscribe to Redis Pub/Sub for real-time
    job status updates. If that fails after several attempts, it falls back to
    polling the database.

    Sends heartbeat comments every 15 seconds to keep connections alive through proxies.
    """
    # First, send initial state from database
    try:
        async with session_factory() as db:
            query = (
                select(DownloadJob)
                .where(DownloadJob.user_id == user_id)
                .order_by(DownloadJob.created_at.desc())
                .limit(50)
            )
            result = await db.execute(query)
            jobs = result.scalars().all()

            seen_initial: OrderedDict[str, str] = OrderedDict()
            for job in jobs:
                job_id_str = str(job.id)
                job_updated_at = job.updated_at.isoformat() if job.updated_at else None
                status_key = f"{job_id_str}:{job_updated_at}"
                if job_id_str not in seen_initial:
                    seen_initial[job_id_str] = status_key
                    yield ServerSentEvent(
                        event="job_update",
                        data=json.dumps(
                            {
                                "id": str(job.id),
                                "url": job.url,
                                "status": job.status,
                                "file_name": job.file_name,
                                "error": job.error,
                                "created_at": job.created_at.isoformat()
                                if job.created_at
                                else None,
                            }
                        ),
                    )
    except Exception as e:
        logger.warning("sse_initial_state_failed", user_id=str(user_id), error=str(e))

    # Try pub/sub first, fall back to polling when pub/sub ends or fails
    try:
        async for event in pubsub_event_generator(request, user_id):
            yield event
    except Exception as e:
        logger.warning(
            "sse_pubsub_generator_failed",
            user_id=str(user_id),
            error=str(e),
            fallback_to_polling=True,
        )
    # Fall back to polling (also covers normal pub/sub termination after max reconnects)
    async for event in fallback_polling_generator(request, session_factory, user_id):
        yield event


@router.get("/downloads/stream")
async def download_status_stream(
    request: Request,
    current_user: CurrentUserFromCookie,
):
    """Server-Sent Events endpoint for real-time download status updates.

    Requires authentication — unauthenticated requests are rejected with 401.

    This endpoint uses Redis Pub/Sub for real-time updates with automatic
    fallback to polling if pub/sub is unavailable.
    """
    return EventSourceResponse(
        event_generator(request, get_async_session_factory(), current_user.id),
        media_type="text/event-stream",
        ping=POLL_INTERVAL_SECONDS,
    )
