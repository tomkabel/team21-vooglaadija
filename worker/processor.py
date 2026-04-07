import asyncio
import logging
import time
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update

from app.config import settings
from app.database import get_async_session_factory
from app.metrics import JOB_DURATION_SECONDS, JOBS_COMPLETED
from app.models.download_job import DownloadJob
from app.models.outbox import Outbox
from app.services.yt_dlp_service import extract_media_url
from worker.queue import enqueue_job, redis_client

logger = logging.getLogger(__name__)


async def process_next_job(job_id: UUID | str | None = None) -> None:
    """Process the next job in the queue.

    If job_id is provided, process that specific job (avoids race condition
    when using BRPOP in the main loop). Otherwise, pop from Redis queue.

    Sets job status to 'processing' before work begins so that
    reset_stuck_jobs() can detect and recover from crashes.

    Implements retry logic with exponential backoff for transient failures.
    """
    if job_id is None:
        job_id_str = await redis_client.rpop("download_queue")
        if not job_id_str:
            return
        job_id = UUID(job_id_str)
    elif isinstance(job_id, str):
        job_id = UUID(job_id)

    session_factory = get_async_session_factory()

    start_time = time.time()
    async with session_factory() as db:
        result = await db.execute(select(DownloadJob).where(DownloadJob.id == job_id))
        job = result.scalar_one_or_none()

        if not job:
            logger.warning(f"Job {job_id} not found in database, skipping")
            return

        if job.status == "pending" and job.next_retry_at:
            if datetime.now(UTC) < job.next_retry_at:
                # Job is not yet due for retry — re-enqueue and return
                # Use ZADD with score = retry timestamp for proper delayed execution
                retry_ts = job.next_retry_at.timestamp()
                await redis_client.zadd("retry_queue", {str(job_id): retry_ts})
                return

        # Only process if job is still pending
        if job.status != "pending":
            logger.info("Job %s is not pending (status=%s), skipping", job_id, job.status)
            return

        # Mark as processing so reset_stuck_jobs can detect crashes
        await db.execute(
            update(DownloadJob).where(DownloadJob.id == job_id).values(status="processing")
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
                )
            )
            await db.commit()
            JOBS_COMPLETED.labels(status="success").inc()
            logger.info("Job %s completed successfully", job_id)
        except asyncio.CancelledError:
            # Don't catch cancellation — let it propagate for clean shutdown
            raise
        except Exception as e:
            error_str = str(e)
            is_format_error = "format is not available" in error_str.lower()

            if is_format_error:
                logger.error(
                    "Job %s failed — video format unavailable (DASH/WebM only, no MP4/M4A): %s",
                    job_id,
                    error_str,
                )
            else:
                logger.error("Job %s failed: %s", job_id, error_str)

            # Format errors are non-retryable — YouTube's available formats won't change
            if is_format_error or job.retry_count >= job.max_retries:
                await db.execute(
                    update(DownloadJob)
                    .where(DownloadJob.id == job_id)
                    .values(
                        status="failed",
                        error=f"Format unavailable: {error_str}"
                        if is_format_error
                        else f"Max retries ({job.max_retries}) exceeded: {error_str}",
                        completed_at=datetime.now(UTC),
                    )
                )
                if not is_format_error:
                    logger.warning(
                        "Job %s failed permanently after %d retries", job_id, job.max_retries
                    )
                JOBS_COMPLETED.labels(status="failed").inc()
            else:
                next_retry = datetime.now(UTC) + timedelta(minutes=2**job.retry_count)
                # Enqueue first, then update DB only if enqueue succeeds
                # This ensures job is never in DB as "pending" without being in the queue
                try:
                    await enqueue_job(job_id)
                except Exception as enqueue_error:
                    logger.error("Job %s failed to enqueue for retry: %s", job_id, enqueue_error)
                    # Don't update DB - job stays processing for next sync cycle
                    return

                await db.execute(
                    update(DownloadJob)
                    .where(DownloadJob.id == job_id)
                    .values(
                        status="pending",
                        retry_count=job.retry_count + 1,
                        next_retry_at=next_retry,
                        error=f"Retry {job.retry_count + 1}/{job.max_retries}: {error_str}",
                    )
                )
                await db.commit()
                logger.info(
                    "Job %s scheduled for retry %d/%d",
                    job_id,
                    job.retry_count + 1,
                    job.max_retries,
                )

            await db.commit()
        finally:
            JOB_DURATION_SECONDS.observe(time.time() - start_time)


async def reset_stuck_jobs(timeout_minutes: int = 10) -> int:
    """Reset jobs that have been stuck in 'processing' for too long.

    Returns the number of jobs reset.
    """
    cutoff = datetime.now(UTC) - timedelta(minutes=timeout_minutes)
    session_factory = get_async_session_factory()

    async with session_factory() as db:
        result = await db.execute(
            update(DownloadJob)
            .where(
                DownloadJob.status == "processing",
                DownloadJob.updated_at < cutoff,
            )
            .values(status="failed", error="Job timed out", completed_at=datetime.now(UTC))
        )
        await db.commit()

        count = result.rowcount  # type: ignore[attr-defined]
        if count > 0:
            logger.warning(
                f"Reset {count} stuck jobs that exceeded {timeout_minutes} minute timeout"
            )

        return count


async def sync_outbox_to_queue(batch_size: int = 100) -> int:
    """Sync pending outbox entries to Redis queue.

    This handles recovery from crashes where the DB committed but the job
    was never enqueued to Redis. Polls for pending entries and pushes them
    to the Redis queue, then marks them as 'enqueued'.

    Uses a two-phase approach to prevent duplicate enqueues:
    1. Atomically claim entries by setting status to 'enqueuing'
    2. Push to Redis and mark as 'enqueued'

    Returns the number of entries synced.
    """
    session_factory = get_async_session_factory()
    synced = 0

    async with session_factory() as db:
        # Phase 1: Atomically claim pending entries to prevent duplicate processing
        # First, select the entries we want to claim (ordered by age)
        select_result = await db.execute(
            select(Outbox)
            .where(Outbox.status == "pending")
            .order_by(Outbox.created_at)
            .limit(batch_size)
        )
        pending_entries = select_result.scalars().all()

        if not pending_entries:
            return 0

        # Claim them atomically with FOR UPDATE to prevent race conditions
        claim_result = await db.execute(
            select(Outbox)
            .where(Outbox.status == "pending")
            .order_by(Outbox.created_at)
            .limit(batch_size)
            .with_for_update(skip_locked=True)  # Skip locked rows to avoid deadlocks
        )
        entries = claim_result.scalars().all()

        if not entries:
            return 0

        # Phase 2: Push to Redis and finalize (without committing intermediate "enqueuing" state)
        # Keep track of entries that successfully reached Redis
        successfully_enqueued = []

        for entry in entries:
            try:
                await redis_client.lpush("download_queue", str(entry.job_id))
                successfully_enqueued.append(entry)
                synced += 1
            except Exception as e:
                logger.error(f"Failed to enqueue job {entry.job_id} from outbox: {e}")
                # Don't change status - entry stays "pending" for next sync cycle

        # Batch update all successfully enqueued entries
        if successfully_enqueued:
            for entry in successfully_enqueued:
                entry.status = "enqueued"
                entry.processed_at = datetime.now(UTC)
            await db.commit()

    if synced > 0:
        logger.info(f"Synced {synced} outbox entries to Redis queue")

    return synced
