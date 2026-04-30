import asyncio
import json
import os
import time
import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import delete, select, update

from app.config import settings
from app.database import get_async_session_factory
from app.logging_config import get_logger
from app.metrics import JOB_DURATION_SECONDS, JOBS_COMPLETED
from app.models.download_job import DownloadJob
from app.models.outbox import Outbox
from app.services.retry_service import calculate_retry_with_jitter
from app.services.circuit_breaker import CircuitBreakerOpenError, extract_media_with_circuit_breaker
from app.services.pubsub_service import get_pubsub_service
from worker.health import update_worker_state
from worker.queue import redis_client

logger = get_logger(__name__)


async def _publish_job_status(job) -> None:
    """Publish job status update to Redis pub/sub.

    This is a fire-and-forget operation - failures are logged but don't
    affect the worker process. The job status is already persisted in the
    database, so pub/sub is just for real-time notifications.
    """
    try:
        pubsub = get_pubsub_service()
        await pubsub.publish_job_status(job.user_id, {
            "id": str(job.id),
            "status": job.status,
            "url": job.url,
            "file_name": job.file_name,
            "error": job.error,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "updated_at": job.updated_at.isoformat() if job.updated_at else None,
        })
    except Exception as e:
        # Log but don't fail - pub/sub is best-effort notification
        logger.warning("pubsub_publish_failed", job_id=str(job.id), error=str(e))


async def _heartbeat(db, job_id: UUID) -> None:
    """Write a lightweight heartbeat to keep the job from being reset as stuck."""
    await db.execute(
        update(DownloadJob).where(DownloadJob.id == job_id).values(updated_at=datetime.now(UTC))
    )
    await db.commit()


async def _requeue_job(job_id: UUID, db) -> None:
    """Requeue a job by setting its status back to 'pending' and pushing to download_queue."""
    outbox_entry = Outbox(
        id=uuid.uuid4(),
        job_id=job_id,
        event_type="retry_scheduled",
        payload=json.dumps(
            {
                "retry_count": 0,
                "next_retry_at": datetime.now(UTC).isoformat(),
            }
        ),
        status="pending",
    )
    db.add(outbox_entry)

    await db.execute(
        update(DownloadJob)
        .where(DownloadJob.id == job_id)
        .values(
            status="pending",
            updated_at=datetime.now(UTC),
        )
    )
    await db.commit()


def _cleanup_downloaded_file(file_path: str | None) -> None:
    """Clean up a downloaded file if it exists."""
    if file_path:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info("Cleaned up partial download: %s", file_path)
        except OSError as e:
            logger.warning("Failed to clean up partial download %s: %s", file_path, e)


async def process_next_job(job_id: UUID | str | None = None) -> bool:
    """Process the next job in the queue.

    If job_id is provided, process that specific job (avoids race condition
    when using BRPOP in the main loop). Otherwise, pop from Redis queue.

    Uses atomic guarded claim: UPDATE ... WHERE id=? AND status='pending'
    and checks rowcount to prevent race conditions.

    Sets job status to 'processing' before work begins so that
    reset_stuck_jobs() can detect and recover from crashes.

    Implements retry logic with exponential backoff for transient failures.

    Returns True if job completed successfully, False if cancelled or skipped.
    """
    # Import here to avoid circular import and get reference to shutdown event
    from worker.main import shutdown_event

    if job_id is None:
        try:
            job_id_str = await redis_client.rpop("download_queue")
        except Exception as e:
            logger.warning("redis_rpop_failed", error=str(e))
            return False
        if not job_id_str:
            return False
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
            logger.info("job_not_claimed", job_id=str(job_id))
            return False

        # Job claimed successfully - mark as running in health state
        update_worker_state(status="running", current_job_started_at=datetime.now(UTC).isoformat())

        try:
            # Fetch the job for processing
            result = await db.execute(select(DownloadJob).where(DownloadJob.id == job_id))
            job = result.scalar_one_or_none()

            if not job:
                logger.warning("job_not_found_after_claim", job_id=str(job_id))
                update_worker_state(status="running", current_job_started_at=None)
                return False

            # Initial heartbeat after claiming
            await _heartbeat(db, job_id)

            # Publish status="processing" to Redis pub/sub
            result = await db.execute(select(DownloadJob).where(DownloadJob.id == job_id))
            job = result.scalar_one_or_none()
            if job:
                await _publish_job_status(job)

            # Check for cancellation before starting download
            if shutdown_event.is_set():
                logger.info("Shutdown requested, requeueing job %s", job_id)
                await _requeue_job(job_id, db)
                update_worker_state(status="running", current_job_started_at=None)
                return False

            file_path, file_name = await extract_media_with_circuit_breaker(
                job.url, settings.storage_path
            )

            # Check for cancellation after download (before marking complete)
            if shutdown_event.is_set():
                logger.info("Shutdown requested after download, requeueing job %s", job_id)
                await _requeue_job(job_id, db)
                # Clean up the downloaded file since job is being requeued
                _cleanup_downloaded_file(file_path)
                update_worker_state(status="running", current_job_started_at=None)
                return False

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

            # Refetch job to get updated values for pub/sub
            result = await db.execute(select(DownloadJob).where(DownloadJob.id == job_id))
            job = result.scalar_one_or_none()
            if job:
                await _publish_job_status(job)

            update_worker_state(status="running", current_job_started_at=None)
            JOBS_COMPLETED.labels(status="success").inc()
            logger.info("job_completed_successfully", job_id=str(job_id))
            return True
        except asyncio.CancelledError:
            # Requeue the job to prevent it being stuck in 'processing'
            # reset_stuck_jobs would otherwise hard-fail it later
            logger.info("Job %s cancelled, requeueing...", job_id)
            await _requeue_job(job_id, db)
            update_worker_state(status="running", current_job_started_at=None)
            raise
        except CircuitBreakerOpenError as cb_error:
            # Circuit breaker is open - service is unhealthy, fail fast without retry
            logger.warning(
                "circuit_breaker_open_circuit_tripped",
                job_id=str(job_id),
                service=cb_error.service_name,
                reset_timeout=cb_error.reset_timeout,
            )
            await db.execute(
                update(DownloadJob)
                .where(DownloadJob.id == job_id)
                .values(
                    status="failed",
                    error=f"Service unavailable (circuit breaker open): {cb_error.service_name}",
                    completed_at=datetime.now(UTC),
                )
            )
            JOBS_COMPLETED.labels(status="failed").inc()
            await db.commit()

            # Publish status="failed" to Redis pub/sub
            result = await db.execute(select(DownloadJob).where(DownloadJob.id == job_id))
            job = result.scalar_one_or_none()
            if job:
                await _publish_job_status(job)

            return False
        except Exception as e:
            error_str = str(e)
            is_format_error = "format is not available" in error_str.lower()

            if is_format_error:
                logger.error(
                    "job_failed_format_unavailable",
                    job_id=str(job_id),
                    error=error_str,
                )
            else:
                logger.error("job_failed", job_id=str(job_id), error=error_str)

            update_worker_state(status="running", current_job_started_at=None)

            # Re-fetch job for error handling (job may be stale after long operations)
            result = await db.execute(select(DownloadJob).where(DownloadJob.id == job_id))
            job = result.scalar_one_or_none()

            if not job:
                logger.error("job_not_found_during_error_handling", job_id=str(job_id))
                return False

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
                JOBS_COMPLETED.labels(status="failed").inc()
                if not is_format_error:
                    logger.warning(
                        "job_failed_permanently_max_retries",
                        job_id=str(job_id),
                        retry_count=job.retry_count,
                        max_retries=job.max_retries,
                    )
                await db.commit()

                # Publish status="failed" to Redis pub/sub (permanent failure)
                result = await db.execute(select(DownloadJob).where(DownloadJob.id == job_id))
                job = result.scalar_one_or_none()
                if job:
                    await _publish_job_status(job)

            else:
                # Calculate next retry with exponential backoff + full jitter
                # This prevents thundering herd problem per AWS Well-Architected Framework
                next_retry = calculate_retry_with_jitter(job.retry_count)

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
                        "job_scheduled_for_retry",
                        job_id=str(job_id),
                        retry_count=job.retry_count + 1,
                        max_retries=job.max_retries,
                        next_retry_at=next_retry.isoformat(),
                    )

                    # Publish status="pending" (retry scheduled) to Redis pub/sub
                    result = await db.execute(select(DownloadJob).where(DownloadJob.id == job_id))
                    job = result.scalar_one_or_none()
                    if job:
                        await _publish_job_status(job)

                except Exception as enqueue_error:
                    # DB is already committed with pending status and outbox entry
                    # This is recoverable - sync_outbox will eventually enqueue it
                    logger.error(
                        "job_failed_to_enqueue_for_retry",
                        job_id=str(job_id),
                        error=str(enqueue_error),
                    )

        finally:
            JOB_DURATION_SECONDS.observe(time.time() - start_time)

    # Fallback return for paths that don't explicitly return
    return False


async def reset_stuck_jobs(timeout_minutes: int = 10) -> int:
    """Reset jobs that have been stuck in 'processing' for too long.

    Returns the number of jobs reset.
    """
    cutoff = datetime.now(UTC) - timedelta(minutes=timeout_minutes)
    session_factory = get_async_session_factory()

    async with session_factory() as db:
        # Find stuck jobs first to publish status changes after update
        result = await db.execute(
            select(DownloadJob)
            .where(
                DownloadJob.status == "processing",
                DownloadJob.updated_at < cutoff,
            )
        )
        stuck_jobs = result.scalars().all()

        if stuck_jobs:
            result = await db.execute(
                update(DownloadJob)
                .where(
                    DownloadJob.status == "processing",
                    DownloadJob.updated_at < cutoff,
                )
                .values(status="failed", error="Job timed out", completed_at=datetime.now(UTC), updated_at=datetime.now(UTC))
            )
            await db.commit()

            # Refresh and publish status changes so SSE clients see timeouts in real-time
            for job in stuck_jobs:
                await db.refresh(job)
                await _publish_job_status(job)

        count = len(stuck_jobs)
        if count > 0:
            logger.warning(
                "reset_stuck_jobs",
                count=count,
                timeout_minutes=timeout_minutes,
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

        # Phase 2: Push to Redis and delete from outbox (DB lock held)
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
                            "missing_next_retry_at_in_payload",
                            job_id=str(entry.job_id),
                        )
                        continue
                else:
                    # Default: push to download_queue
                    await redis_client.lpush("download_queue", str(entry.job_id))

                # Delete after successful Redis publish to keep outbox table empty
                await db.execute(delete(Outbox).where(Outbox.id == entry.id))
                synced += 1
            except Exception as e:
                logger.error(
                    "failed_to_enqueue_job_from_outbox", job_id=str(entry.job_id), error=str(e)
                )
                # Don't change status - entry stays "pending" for next sync cycle

        await db.commit()

    if synced > 0:
        logger.info("synced_outbox_entries_to_queue", count=synced)

    return synced
