import asyncio
import json
import uuid
from collections import OrderedDict

from fastapi import APIRouter, Request
from sqlalchemy import select
from sse_starlette import EventSourceResponse

from app.api.dependencies import CurrentUserFromCookie
from app.database import get_async_session_factory
from app.models.download_job import DownloadJob

router = APIRouter(prefix="/web", tags=["sse"])

MAX_SEEN_JOBS = 100
POLL_INTERVAL_SECONDS = 15


async def event_generator(
    request: Request,
    db_session_factory,
    user_id: uuid.UUID,
):
    """SSE event generator that polls for job status changes.

    Uses a fresh DB session per poll cycle to avoid connection leaks
    and stale data. Only queries when there's a chance of new data
    by checking the most recent updated_at timestamp.
    Sends heartbeat comments every 15 seconds to keep connections alive through proxies.
    """
    seen_jobs: OrderedDict[str, str] = OrderedDict()
    last_updated_at = None

    try:
        while True:
            if await request.is_disconnected():
                break

            async with db_session_factory()() as db:
                # Order by created_at for initial load, updated_at for subsequent polls
                order_by = (
                    DownloadJob.updated_at.desc()
                    if last_updated_at is not None
                    else DownloadJob.created_at.desc()
                )

                query = (
                    select(DownloadJob)
                    .where(DownloadJob.user_id == user_id)
                    .order_by(order_by)
                    .limit(50)
                )

                # Only query if there might be new data
                if last_updated_at is not None:
                    query = query.where(DownloadJob.updated_at > last_updated_at)

                result = await db.execute(query)
                jobs = result.scalars().all()

                if jobs:
                    # Track the most recent update for conditional polling
                    last_updated_at = max(job.updated_at for job in jobs if job.updated_at)

                for job in jobs:
                    status_key = f"{job.id}:{job.status}"

                    if job.id not in seen_jobs or seen_jobs[job.id] != status_key:
                        seen_jobs[job.id] = status_key
                        seen_jobs.move_to_end(job.id)

                        yield {
                            "event": "job_update",
                            "data": json.dumps(
                                {
                                    "id": str(job.id),
                                    "url": job.url,
                                    "status": job.status,
                                    "file_name": job.file_name,
                                    "error": job.error,
                                }
                            ),
                        }

                while len(seen_jobs) > MAX_SEEN_JOBS:
                    seen_jobs.popitem(last=False)

            # Send heartbeat comment to keep connection alive through proxies
            yield {
                "event": "comment",
                "data": ": heartbeat",
            }

            await asyncio.sleep(POLL_INTERVAL_SECONDS)
    except asyncio.CancelledError:
        # Client disconnected — normal shutdown path
        pass


@router.get("/downloads/stream")
async def download_status_stream(
    request: Request,
    current_user: CurrentUserFromCookie,
):
    """Server-Sent Events endpoint for real-time download status updates.

    Requires authentication — unauthenticated requests are rejected with 401.
    """
    return EventSourceResponse(
        event_generator(request, get_async_session_factory, current_user.id),
        media_type="text/event-stream",
    )
