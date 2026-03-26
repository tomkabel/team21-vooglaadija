import os
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.download_job import DownloadJob
from app.services.yt_dlp_service import extract_media_url

from worker.queue import redis_client

import logging

logger = logging.getLogger(__name__)


async def process_next_job() -> None:
    """Process the next job in the queue.

    Uses a single transaction: if anything fails, the job stays as-is
    and will not be stuck in 'processing' state.
    """
    job_id = await redis_client.rpop("download_queue")
    if not job_id:
        return

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(DownloadJob).where(DownloadJob.id == job_id))
        job = result.scalar_one_or_none()

        if not job:
            logger.warning(f"Job {job_id} not found in database, skipping")
            return

        try:
            file_path, file_name = await extract_media_url(job.url, settings.storage_path)

            await db.execute(
                update(DownloadJob)
                .where(DownloadJob.id == job_id)
                .values(
                    status="completed",
                    file_path=file_path,
                    file_name=file_name,
                    completed_at=datetime.now(UTC),
                    expires_at=datetime.now(UTC) + timedelta(hours=settings.file_expire_hours),
                )
            )
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            await db.execute(
                update(DownloadJob)
                .where(DownloadJob.id == job_id)
                .values(
                    status="failed",
                    error=str(e),
                    completed_at=datetime.now(UTC),
                )
            )

        await db.commit()


async def reset_stuck_jobs(timeout_minutes: int = 10) -> int:
    """Reset jobs that have been stuck in 'processing' for too long.

    Returns the number of jobs reset.
    """
    cutoff = datetime.now(UTC) - timedelta(minutes=timeout_minutes)

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            update(DownloadJob)
            .where(
                DownloadJob.status == "processing",
                DownloadJob.created_at < cutoff,
            )
            .values(status="failed", error="Job timed out", completed_at=datetime.now(UTC))
        )
        await db.commit()

        count = result.rowcount
        if count > 0:
            logger.warning(
                f"Reset {count} stuck jobs that exceeded {timeout_minutes} minute timeout"
            )

        return count
