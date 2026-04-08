import asyncio
import json
import logging
import time
import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update

from app.config import settings
from app.database import get_async_session_factory
from app.metrics import JOB_DURATION_SECONDS, JOBS_COMPLETED
from app.models.download_job import DownloadJob
from app.models.outbox import Outbox
from app.services.yt_dlp_service import extract_media_url
from worker.health import update_worker_state
from worker.queue import redis_client

logger = logging.getLogger(__name__)


async def _heartbeat(db, job_id: UUID) -> None:
    """Write a lightweight heartbeat to keep the job from being reset as stuck."""
    await db.execute(
        update(DownloadJob).where(DownloadJob.id == job_id).values(updated_at=datetime.now(UTC))
    )
    await db.commit()


async def process_next_job(job_id: UUID | str | None = None) -> None:
    """Process the next job in the queue.

    If job_id is provided, process that specific job (avoids race condition
    when using BRPOP in the main loop). Otherwise, pop from Redis queue.

    Uses atomic guarded claim: UPDATE ... WHERE id=? AND status='pending'
    and checks rowcount to prevent race conditions.

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
        # Atomic guarded claim: UPDATE ... WHERE id=? AND status='pending'
        # Only proceeds if exactly one row was claimed
        result = await db.execute(
            update(DownloadJob)
            .where(DownloadJob.id == job_id, DownloadJob.status == "pending")
            .values(
                status="processing",
                updated_at=datetime.now(UTC),
            )
        )
        await db.commit()

        # Check if we actually claimed the job (rowcount == 1)
        claimed = result.rowcount == 1  # type: ignore[attr-defined]

        if not claimed:
            # Job was already claimed by another worker or is not pending
            logger.info("Job %s was not claimed (possibly by another worker)", job_id)
            return

        # Job claimed successfully - mark as running in health state
        update_worker_state(status="running", current_job_started_at=datetime.now(UTC).isoformat())

        try:
            # Fetch the job for processing
            result = await db.execute(select(DownloadJob).where(DownloadJob.id == job_id))
            job = result.scalar_one_or_none()

            if not job:
                logger.warning("Job %s not found after claim", job_id)
                update_worker_state(status="running", current_job_started_at=None)
                return

            # Initial heartbeat after claiming
            await _heartbeat(db, job_id)

            file_path, file_name = await extract_media_url(job.url, settings.storage_path)

            # Heartbeat after extract_media_url completes
            await _heartbeat(db, job_id)

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
            update_worker_state(status="running", current_job_started_at=None)
            JOBS_COMPLETED.labels(status="success").inc()
            logger.info("Job %s completed successfully", job_id)
        except asyncio.CancelledError:
            # Requeue the job to prevent it being stuck in 'processing'
            # reset_stuck_jobs would otherwise hard-fail it later
            await db.execute(
                update(DownloadJob)
                .where(DownloadJob.id == job_id)
                .values(
                    status="queued",
                    updated_at=datetime.now(UTC),
                )
            )
            await db.commit()
            update_worker_state(status="running", current_job_started_at=None)
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

            update_worker_state(status="running", current_job_started_at=None)

            # Fetch job for retry/error handling
            result = await db.execute(select(DownloadJob).where(DownloadJob.id == job_id))
            job = result.scalar_one_or_none()

            if not job:
                logger.error("Job %s not found during error handling", job_id)
                return

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
                await db.commit()
            else:
                next_retry = datetime.now(UTC) + timedelta(minutes=2**job.retry_count)

                # Create outbox entry for retry in same transaction as DB update
                outbox_entry = Outbox(
                    id=uuid.uuid4(),
                    job_id=job_id,
                    event_type="retry_scheduled",
                    payload=json.dumps(
                        {
                            "retry_count": job.retry_count + 1,
                            "next_retry_at": next_retry.isoformat(),
                        }
                    ),
                    status="pending",
                )
                db.add(outbox_entry)

                # Update DB with pending status and next_retry_at
                await db.execute(
                    update(DownloadJob)
                    .where(DownloadJob.id == job_id)
                    .values(
                        status="pending",
                        retry_count=job.retry_count + 1,
                        next_retry_at=next_retry,
                        error=f"Retry {job.retry_count + 1}/{job.max_retries}: {error_str}",
                        updated_at=datetime.now(UTC),
                    )
                )
                await db.commit()

                # Only after DB commit succeeds, enqueue to retry queue
                try:
                    retry_ts = next_retry.timestamp()
                    await redis_client.zadd("retry_queue", {str(job_id): retry_ts})
                    # Mark outbox entry as enqueued after successful zadd
                    outbox_entry.status = "enqueued"
                    outbox_entry.processed_at = datetime.now(UTC)
                    await db.commit()
                    logger.info(
                        "Job %s scheduled for retry %d/%d",
                        job_id,
                        job.retry_count + 1,
                        job.max_retries,
                    )
                except Exception as enqueue_error:
                    # DB is already committed with pending status and outbox entry
                    # This is recoverable - sync_outbox will eventually enqueue it
                    logger.error("Job %s failed to enqueue for retry: %s", job_id, enqueue_error)

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
                "Reset %d stuck jobs that exceeded %d minute timeout",
                count,
                timeout_minutes,
            )

        return count


async def sync_outbox_to_queue(batch_size: int = 100) -> int:
    """Sync pending outbox entries to Redis queue.

    This handles recovery from crashes where the DB committed but the job
    was never enqueued to Redis. Polls for pending entries and pushes them
    to the Redis queue, then marks them as 'enqueued'.

    Uses a two-phase approach to minimize lock hold time:
    1. Claim entries with FOR UPDATE SKIP LOCKED and collect IDs (DB lock held briefly)
    2. Release DB lock, push to Redis (no lock during network I/O)
    3. Reopen session to mark entries as enqueued

    Returns the number of entries synced.
    """
    session_factory = get_async_session_factory()
    synced = 0

    # Phase 1: Claim entries, push to Redis, and mark as enqueued (DB lock held throughout)
    async with session_factory() as db:
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

        # Phase 2: Push to Redis and mark as enqueued (DB lock held)
        now = datetime.now(UTC)
        for entry in entries:
            try:
                if entry.event_type == "retry_scheduled":
                    # Parse payload to get next_retry_at and add to retry_queue
                    payload_data = json.loads(entry.payload) if entry.payload else {}
                    next_retry_at = payload_data.get("next_retry_at")
                    if next_retry_at:
                        # Convert to UNIX timestamp using datetime.timestamp()
                        retry_timestamp = datetime.fromisoformat(next_retry_at).timestamp()
                        await redis_client.zadd("retry_queue", {str(entry.job_id): retry_timestamp})
                    else:
                        logger.error(
                            "Missing next_retry_at in retry_scheduled payload for job %s",
                            entry.job_id,
                        )
                        continue
                else:
                    # Default: push to download_queue
                    await redis_client.lpush("download_queue", str(entry.job_id))

                # Mark as enqueued
                await db.execute(
                    update(Outbox)
                    .where(Outbox.id == entry.id)
                    .values(status="enqueued", processed_at=now)
                )
                synced += 1
            except Exception as e:
                logger.error("Failed to enqueue job %s from outbox: %s", entry.job_id, e)
                # Don't change status - entry stays "pending" for next sync cycle

        await db.commit()

    if synced > 0:
        logger.info("Synced %d outbox entries to Redis queue", synced)

    return synced