import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.download_job import DEFAULT_MAX_RETRIES, DownloadJob
from app.services.yt_dlp_service import extract_media_url
from worker.queue import enqueue_job, redis_client

logger = logging.getLogger(__name__)


async def process_next_job() -> None:
    """Process the next job in the queue.

    Two-phase approach:
    1. Pop from Redis, mark job as "processing" and commit immediately.
       This ensures reset_stuck_jobs can recover the job if the worker dies.
    2. Extract media, then update to "completed" or "failed" and commit.

    On failure, job is re-queued for retry if retry_count < max_retries.
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

        # Immediately mark as processing so reset_stuck_jobs can recover it
        await db.execute(
            update(DownloadJob)
            .where(DownloadJob.id == job_id)
            .values(status="processing", updated_at=datetime.now(UTC)),
        )
        await db.commit()

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
                    updated_at=datetime.now(UTC),
                ),
            )
            await db.commit()
            logger.info(f"Job {job_id} completed successfully")

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            await handle_job_failure(db, job, str(e))


async def handle_job_failure(db, job: DownloadJob, error_message: str) -> None:
    """Handle job failure with retry logic.

    If job can be retried, re-queues it with exponential backoff.
    Otherwise marks as permanently failed.
    """
    retry_count = job.retry_count or 0
    max_retries = job.max_retries or DEFAULT_MAX_RETRIES

    if retry_count < max_retries:
        # Increment retry count and re-queue
        new_retry_count = retry_count + 1

        await db.execute(
            update(DownloadJob)
            .where(DownloadJob.id == job.id)
            .values(
                status="pending",
                retry_count=new_retry_count,
                error=f"Retry {new_retry_count}/{max_retries}: {error_message}",
                updated_at=datetime.now(UTC),
            ),
        )
        await db.commit()

        # Re-queue the job immediately
        await enqueue_job(job.id)
        logger.info(
            f"Job {job.id} re-queued for retry {new_retry_count}/{max_retries}",
        )
    else:
        # Max retries exceeded, mark as permanently failed
        await db.execute(
            update(DownloadJob)
            .where(DownloadJob.id == job.id)
            .values(
                status="failed",
                error=f"Max retries ({max_retries}) exceeded: {error_message}",
                completed_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            ),
        )
        await db.commit()
        logger.warning(f"Job {job.id} permanently failed after {max_retries} retries")


async def reset_stuck_jobs(timeout_minutes: int = 10) -> int:
    """Reset jobs that have been stuck in 'processing' for too long.

    Returns the number of jobs reset.
    """
    cutoff = datetime.now(UTC) - timedelta(minutes=timeout_minutes)

    async with AsyncSessionLocal() as db:
        # First, select the IDs of stuck jobs to re-queue after update
        select_result = await db.execute(
            select(DownloadJob.id).where(
                DownloadJob.status == "processing",
                DownloadJob.updated_at < cutoff,
            ),
        )
        stuck_job_ids = list(select_result.scalars().all())

        if stuck_job_ids:
            # Update the jobs to pending status
            await db.execute(
                update(DownloadJob)
                .where(
                    DownloadJob.status == "processing",
                    DownloadJob.updated_at < cutoff,
                )
                .values(
                    status="pending",
                    error="Job timed out - will retry",
                    updated_at=datetime.now(UTC),
                ),
            )
            await db.commit()

            # Re-queue the stuck jobs
            requeued_count = 0
            for job_id in stuck_job_ids:
                try:
                    await enqueue_job(job_id)
                    requeued_count += 1
                except Exception as e:
                    logger.error(f"Failed to re-queue stuck job {job_id}: {e}")

            logger.warning(
                f"Reset {len(stuck_job_ids)} stuck jobs that exceeded {timeout_minutes} minute timeout, "
                f"re-queued {requeued_count}",
            )

        return len(stuck_job_ids)
