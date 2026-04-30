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


async def _emit_initial_snapshot(
    session_factory,
    user_id: uuid.UUID,
    seen_initial: OrderedDict[str, str],
) -> list[ServerSentEvent]:
    """Emit initial job state from database."""
    events = []
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

            for job in jobs:
                job_id_str = str(job.id)
                job_updated_at = job.updated_at.isoformat() if job.updated_at else None
                status_key = f"{job_id_str}:{job_updated_at}"
                seen_initial[job_id_str] = status_key
                events.append(
                    ServerSentEvent(
                        event="job_update",
                        data=json.dumps(await _job_to_sse_data(job)),
                    )
                )
    except Exception as e:
        logger.warning("sse_initial_state_failed", user_id=str(user_id), error=str(e))
    return events


async def _replay_buffered_events(
    buffered_events: list[dict],
    seen_initial: OrderedDict[str, str],
) -> AsyncGenerator[ServerSentEvent, None]:
    """Replay buffered events, skipping ones already in seen_initial."""
    for buffered in buffered_events:
        key = buffered["key"]
        job_data = buffered["data"]
        job_id = job_data.get("id")
        if job_id and key not in seen_initial.values():
            seen_initial[job_id] = key
            while len(seen_initial) > MAX_SEEN_JOBS:
                seen_initial.popitem(last=False)
            yield ServerSentEvent(
                event="job_update",
                data=json.dumps(job_data),
            )


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
    last_seen_job_ids: OrderedDict[str, str] | None = None,
) -> AsyncGenerator[ServerSentEvent, None]:
    """SSE event generator that subscribes to Redis Pub/Sub for real-time updates."""
    pubsub = get_pubsub_service()
    reconnect_attempts = 0
    last_seen_job_ids = last_seen_job_ids if last_seen_job_ids is not None else OrderedDict()

    while reconnect_attempts < MAX_PUBSUB_RECONNECT_ATTEMPTS:
        if await request.is_disconnected():
            break

        try:
            async for event in _subscribe_to_pubsub(pubsub, user_id, last_seen_job_ids):
                yield event
            break  # Normal completion, no more events

        except (asyncio.CancelledError, GeneratorExit):
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
                return  # Use return instead of break for generator


async def fallback_polling_generator(
    request: Request,
    session_factory,
    user_id: uuid.UUID,
    seen_jobs: OrderedDict[str, str] | None = None,
) -> AsyncGenerator[ServerSentEvent, None]:
    """Fallback polling generator when Pub/Sub is unavailable."""
    # Reuse existing dedup cache from request state if available
    if hasattr(request.state, "seen_jobs") and request.state.seen_jobs:
        seen_jobs = request.state.seen_jobs
    elif seen_jobs is None:
        seen_jobs = OrderedDict()

    # Store back to request state for potential reuse
    request.state.seen_jobs = seen_jobs

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
                            data=json.dumps(await _job_to_sse_data(job)),
                        )

            await asyncio.sleep(POLL_INTERVAL_SECONDS)
    except (asyncio.CancelledError, GeneratorExit):
        pass


async def event_generator(  # noqa: C901
    request: Request,
    session_factory,
    user_id: uuid.UUID,
) -> AsyncGenerator[ServerSentEvent, None]:
    """SSE event generator that prioritizes Pub/Sub with polling fallback."""
    seen_initial: OrderedDict[str, str] = OrderedDict()
    buffered_events: list[dict] = []

    # Start pub/sub subscription first and buffer incoming messages
    pubsub = get_pubsub_service()
    reconnect_attempts = 0

    async def _buffer_pubsub_events():
        """Buffer pub/sub events before DB snapshot."""
        nonlocal reconnect_attempts
        while reconnect_attempts < MAX_PUBSUB_RECONNECT_ATTEMPTS:
            if await request.is_disconnected():
                break
            try:
                async for job_data in pubsub.subscribe(user_id):
                    job_id = job_data.get("id")
                    if job_id:
                        job_updated_at = job_data.get("updated_at")
                        status_key = f"{job_id}:{job_updated_at}"
                        buffered_events.append({"key": status_key, "data": job_data})
                break
            except (asyncio.CancelledError, GeneratorExit):
                break
            except Exception as e:
                reconnect_attempts += 1
                logger.warning(
                    "pubsub_buffer_error",
                    user_id=str(user_id),
                    attempt=reconnect_attempts,
                    error=str(e),
                )
                if reconnect_attempts < MAX_PUBSUB_RECONNECT_ATTEMPTS:
                    await asyncio.sleep(PUBSUB_RECONNECT_DELAY_SECONDS * reconnect_attempts)
                else:
                    break

    # Run buffering task concurrently with DB query
    buffer_task = asyncio.create_task(_buffer_pubsub_events())

    # Send initial state from database
    initial_events = await _emit_initial_snapshot(session_factory, user_id, seen_initial)
    for event in initial_events:
        yield event

    # Wait for buffering to complete (with timeout)
    try:
        await asyncio.wait_for(asyncio.shield(buffer_task), timeout=2.0)
    except (TimeoutError, Exception):
        pass

    # Replay buffered events (skipping ones already in seen_initial)
    async for event in _replay_buffered_events(buffered_events, seen_initial):
        yield event

    # Continue with pub/sub, fall back to polling if needed
    try:
        async for event in pubsub_event_generator(request, user_id, seen_initial):
            yield event
    except Exception as e:
        logger.warning(
            "sse_pubsub_generator_failed",
            user_id=str(user_id),
            error=str(e),
            fallback_to_polling=True,
        )

    # Fall back to polling
    async for event in fallback_polling_generator(request, session_factory, user_id, seen_initial):
        yield event


@router.get("/downloads/stream")
async def download_status_stream(
    request: Request,
    current_user: CurrentUserFromCookie,
):
    """Server-Sent Events endpoint for real-time download status updates."""
    return EventSourceResponse(
        event_generator(request, get_async_session_factory(), current_user.id),
        media_type="text/event-stream",
        ping=POLL_INTERVAL_SECONDS,
    )
