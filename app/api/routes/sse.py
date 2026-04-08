import asyncio
import json
import uuid
from collections import OrderedDict

from fastapi import APIRouter, Request
from sqlalchemy import select
from sse_starlette import EventSourceResponse, ServerSentEvent

from app.api.dependencies import CurrentUserFromCookie
from app.database import get_async_session_factory
from app.models.download_job import DownloadJob

router = APIRouter(prefix="/web", tags=["sse"])

MAX_SEEN_JOBS = 100
POLL_INTERVAL_SECONDS = 15


async def event_generator(
    request: Request,
    session_factory,
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
    last_id = None

    try:
        while True:
            if await request.is_disconnected():
                break

            async with session_factory() as db:
                # Order by created_at for initial load, (updated_at, id) for incremental polls
                if last_updated_at is not None:
                    # Incremental: stable forward cursor using (updated_at, id)
                    query = (
                        select(DownloadJob)
                        .where(DownloadJob.user_id == user_id)
                        .order_by(DownloadJob.updated_at.asc(), DownloadJob.id.asc())
                        .limit(50)
                    )
                    # Filter: (updated_at > last_updated_at) OR (updated_at = last_updated_at AND id > last_id)
                    from sqlalchemy import and_, or_

                    query = query.where(
                        or_(
                            DownloadJob.updated_at > last_updated_at,
                            and_(
                                DownloadJob.updated_at == last_updated_at, DownloadJob.id > last_id
                            ),
                        )
                    )
                else:
                    # Initial load: use created_at descending
                    query = (
                        select(DownloadJob)
                        .where(DownloadJob.user_id == user_id)
                        .order_by(DownloadJob.created_at.desc())
                        .limit(50)
                    )

                result = await db.execute(query)
                jobs = result.scalars().all()

                if jobs:
                    # Update cursor from the last row in the ordered batch
                    if last_updated_at is not None:
                        # Incremental: cursor is from last row
                        last_job = jobs[-1]
                        last_updated_at = last_job.updated_at
                        last_id = last_job.id
                    else:
                        # Initial load: set cursor for next incremental poll
                        # Find the job with max updated_at, then max id if tied
                        sorted_by_cursor = sorted(jobs, key=lambda j: (j.updated_at, j.id))
                        last_job = sorted_by_cursor[-1]
                        last_updated_at = last_job.updated_at
                        last_id = last_job.id

                for job in jobs:
                    job_id_str = str(job.id)
                    status_key = f"{job_id_str}:{job.status}"

                    if job_id_str not in seen_jobs or seen_jobs[job_id_str] != status_key:
                        seen_jobs[job_id_str] = status_key
                        seen_jobs.move_to_end(job_id_str)

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

                while len(seen_jobs) > MAX_SEEN_JOBS:
                    seen_jobs.popitem(last=False)

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
        event_generator(request, get_async_session_factory(), current_user.id),
        media_type="text/event-stream",
        ping=POLL_INTERVAL_SECONDS,
    )
