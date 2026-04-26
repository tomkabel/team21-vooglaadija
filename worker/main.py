"""Worker main loop for processing download jobs with structured logging."""

import asyncio
import os
import signal
import time
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.config import settings
from app.database import get_async_session_factory
from app.logging_config import configure_logging, get_logger
from app.models.download_job import DownloadJob
from worker.health import (
    start_health_server,
    stop_health_server,
    update_worker_state,
    write_health_async,
)
from worker.processor import process_next_job, reset_stuck_jobs, sync_outbox_to_queue
from worker.queue import redis_client

# Initialize structured logging
configure_logging(log_level=os.environ.get("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

# Graceful shutdown configuration
# Configurable grace period per 2026 Kubernetes best practices
GRACE_PERIOD_SECONDS: int = int(os.environ.get("WORKER_GRACE_PERIOD_SECONDS", "25"))

# Graceful shutdown event and timestamp tracking
shutdown_event = asyncio.Event()
shutdown_requested_at: float | None = None  # Timestamp when SIGTERM was received


def _signal_handler() -> None:
    """Handle shutdown signals gracefully with timestamp tracking."""
    global shutdown_requested_at
    if shutdown_requested_at is None:
        shutdown_requested_at = time.monotonic()
        logger.info(
            "received_shutdown_signal",
            signal="SIGTERM/SIGINT",
            grace_period_seconds=GRACE_PERIOD_SECONDS,
        )
    shutdown_event.set()


def get_grace_period_remaining() -> float | None:
    """Get remaining grace period in seconds, or None if shutdown not requested."""
    if shutdown_requested_at is None:
        return None
    elapsed = time.monotonic() - shutdown_requested_at
    remaining = GRACE_PERIOD_SECONDS - elapsed
    return max(0.0, remaining)


async def cleanup_expired_jobs() -> int:
    """Delete expired jobs and their files. Returns number of jobs cleaned up."""
    session_factory = get_async_session_factory()
    downloads_dir = os.path.realpath(os.path.join(settings.storage_path, "downloads"))

    async with session_factory() as db:
        now = datetime.now(UTC)

        result = await db.execute(
            select(DownloadJob).where(
                DownloadJob.expires_at < now, DownloadJob.status == "completed"
            )
        )
        expired_jobs = result.scalars().all()

        cleanup_count = 0
        for job in expired_jobs:
            if job.file_path:
                resolved_path = os.path.realpath(job.file_path)
                # Validate path is within downloads directory
                safe_dir = (
                    downloads_dir if downloads_dir.endswith(os.sep) else downloads_dir + os.sep
                )
                if resolved_path.startswith(safe_dir) and os.path.exists(resolved_path):
                    try:
                        os.remove(resolved_path)
                        logger.info(
                            "cleaned_up_expired_file", file_path=resolved_path, job_id=str(job.id)
                        )
                        # Only delete DB row after successful file removal
                        await db.delete(job)
                        cleanup_count += 1
                    except OSError as e:
                        logger.warning(
                            "failed_to_delete_expired_file", file_path=job.file_path, error=str(e)
                        )
                        # Don't delete DB row - cleanup will retry next interval
                elif resolved_path.startswith(safe_dir):
                    # File already deleted, just remove DB row
                    logger.info("file_already_deleted", job_id=str(job.id), file_path=job.file_path)
                    await db.delete(job)
                    cleanup_count += 1
                else:
                    logger.warning(
                        "path_traversal_attempt_skipped",
                        job_id=str(job.id),
                        file_path=job.file_path,
                    )
            else:
                # No file_path, just delete the DB row
                try:
                    await db.delete(job)
                    cleanup_count += 1
                except Exception as db_err:
                    logger.warning("failed_to_delete_db_row", job_id=job.id, error=str(db_err), exc_info=True)

        # Batch commit after processing all jobs
        try:
            await db.commit()
        except Exception as commit_err:
            logger.warning("db_commit_failed", error=str(commit_err))

        if cleanup_count > 0:
            logger.info("cleanup_completed", expired_jobs_cleaned=cleanup_count)

        return cleanup_count


async def main() -> None:
    """Main worker loop with graceful shutdown.

    Uses BRPOP with timeout for efficient blocking queue consumption
    instead of polling with rpop + sleep.
    """
    # Register signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _signal_handler)

    logger.info("worker_started")

    # Test Redis connection before starting
    logger.info("testing_redis_connection")
    try:
        await redis_client.ping()
        logger.info("redis_connection_successful")
    except Exception as e:
        logger.error("redis_connection_failed", error=str(e))
        raise

    # Test database connection before starting
    logger.info("testing_database_connection")
    try:
        session_factory = get_async_session_factory()
        async with session_factory() as db:
            from sqlalchemy import text

            await db.execute(text("SELECT 1"))
        logger.info("database_connection_successful")
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        raise

    # Start HTTP health server for orchestration tools
    health_server = start_health_server()

    cleanup_interval_minutes: int = int(os.environ.get("CLEANUP_INTERVAL_MINUTES", "5"))
    cleanup_interval = timedelta(minutes=cleanup_interval_minutes)
    last_cleanup = datetime.now(UTC) - cleanup_interval
    heartbeat_counter = 0
    heartbeat_interval = (
        10  # Write heartbeat every 10 iterations (~20 seconds, since brpop_timeout=2)
    )
    brpop_timeout = 2  # Seconds to block on BRPOP

    # Mark worker as running
    update_worker_state(status="running")

    while not shutdown_event.is_set():
        # Check if grace period has expired (force exit even if jobs are running)
        grace_remaining = get_grace_period_remaining()
        if grace_remaining is not None and grace_remaining <= 0:
            logger.warning(
                "grace_period_expired_forcing_shutdown",
                grace_period_seconds=GRACE_PERIOD_SECONDS,
            )
            break

        try:
            # Move due retry jobs from retry_queue to download_queue atomically
            # Uses Lua script to prevent race conditions between workers
            now_ts = datetime.now(UTC).timestamp()
            lua_script = """
            local due_jobs = redis.call('ZRANGEBYSCORE', KEYS[1], 0, ARGV[1])
            if #due_jobs > 0 then
                redis.call('ZREM', KEYS[1], unpack(due_jobs))
                for _, job_id in ipairs(due_jobs) do
                    redis.call('LPUSH', KEYS[2], job_id)
                end
            end
            return #due_jobs
            """
            moved_count = await redis_client.eval(
                lua_script, 2, "retry_queue", "download_queue", now_ts
            )
            if moved_count and moved_count > 0:
                logger.info("retry_jobs_moved", moved_count=moved_count)

            # Calculate remaining time for dynamic BRPOP timeout
            # Don't block longer than grace period remaining
            grace_remaining = get_grace_period_remaining()
            if grace_remaining is not None and grace_remaining <= 0:
                # Grace period expired, exit immediately
                break
            effective_timeout = min(brpop_timeout, grace_remaining or brpop_timeout)
            # Ensure minimum timeout of 1 second to avoid busy-waiting
            effective_timeout = max(1, int(effective_timeout))

            # Use BRPOP with timeout for efficient blocking — no busy-waiting
            # Pass the job_id directly to process_next_job to avoid race condition
            result = await redis_client.brpop("download_queue", timeout=effective_timeout)
            if result:
                _, job_id_str = result
                await process_next_job(job_id_str)
            # If BRPOP timed out, no jobs available — continue to cleanup/heartbeat
        except asyncio.CancelledError:
            # This can happen if we were cancelled during brpop or job processing
            logger.info("Worker loop cancelled, exiting...")
            break
        except Exception as e:
            logger.error("job_processing_error", error=str(e))
            await asyncio.sleep(1)

        now = datetime.now(UTC)
        if now - last_cleanup >= cleanup_interval:
            try:
                # Sync outbox to queue during cleanup (handles crash recovery)
                await sync_outbox_to_queue()
                cleanup_count = await cleanup_expired_jobs()
                stuck_count = await reset_stuck_jobs(timeout_minutes=10)
                logger.info(
                    "cleanup_cycle_completed",
                    expired_jobs_cleaned=cleanup_count,
                    stuck_jobs_reset=stuck_count,
                )
                last_cleanup = now
                update_worker_state(last_cleanup=last_cleanup.isoformat())
            except Exception as e:
                logger.error("cleanup_error", error=str(e))

        heartbeat_counter += 1
        if heartbeat_counter >= heartbeat_interval:
            try:
                await write_health_async()
                update_worker_state()
            except Exception as e:
                logger.warning("health_write_failed", error=str(e))
            heartbeat_counter = 0

        # Check if graceful shutdown was requested and log remaining time
        if shutdown_event.is_set():
            grace_remaining = get_grace_period_remaining()
            logger.info(
                "Shutdown requested, exiting main loop...",
                grace_period_seconds_remaining=grace_remaining,
            )
            break

    # Graceful shutdown phase
    # Log final grace period status
    if shutdown_requested_at is not None:
        total_shutdown_time = time.monotonic() - shutdown_requested_at
        logger.info(
            "Worker shutdown complete",
            total_shutdown_seconds=total_shutdown_time,
            grace_period_configured=GRACE_PERIOD_SECONDS,
        )

    logger.info("Worker shutdown complete, stopping health server...")

    # Shutdown health server
    if health_server:
        stop_health_server()
    logger.info("worker_stopped_gracefully")


if __name__ == "__main__":
    asyncio.run(main())
