import asyncio
import logging
import os
import signal
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.download_job import DownloadJob
from worker.processor import process_next_job, reset_stuck_jobs

logger = logging.getLogger(__name__)

# Graceful shutdown event
shutdown_event = asyncio.Event()


def _signal_handler() -> None:
    logger.info("Received shutdown signal, stopping worker...")
    shutdown_event.set()


async def cleanup_expired_jobs() -> int:
    """Delete expired jobs and their files. Returns number of jobs cleaned up."""
    async with AsyncSessionLocal() as db:
        now = datetime.now(UTC)

        result = await db.execute(
            select(DownloadJob).where(
                DownloadJob.expires_at < now, DownloadJob.status == "completed"
            )
        )
        expired_jobs = result.scalars().all()

        cleanup_count = 0
        for job in expired_jobs:
            if job.file_path and os.path.exists(job.file_path):
                try:
                    os.remove(job.file_path)
                    logger.info(f"Cleaned up expired file: {job.file_path}")
                except OSError as e:
                    logger.warning(f"Failed to delete expired file {job.file_path}: {e}")

            await db.delete(job)
            cleanup_count += 1

        await db.commit()

        if cleanup_count > 0:
            logger.info(f"Cleaned up {cleanup_count} expired jobs")

        return cleanup_count


async def main() -> None:
    """Main worker loop with graceful shutdown."""
    # Register signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _signal_handler)

    logger.info("Worker started, waiting for jobs...")

    cleanup_counter = 0
    cleanup_interval = 100  # Run cleanup every 100 iterations

    while not shutdown_event.is_set():
        try:
            await process_next_job()
        except Exception as e:
            logger.error(f"Error processing job: {e}")
            # Brief backoff on error to avoid tight error loop
            await asyncio.sleep(1)

        # Run cleanup and stuck-job recovery every N iterations
        cleanup_counter += 1
        if cleanup_counter >= cleanup_interval:
            try:
                await cleanup_expired_jobs()
                await reset_stuck_jobs(timeout_minutes=10)
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            cleanup_counter = 0

        # Use wait with timeout instead of unconditional sleep for faster shutdown
        try:
            await asyncio.wait_for(shutdown_event.wait(), timeout=1.0)
        except asyncio.TimeoutError:
            pass

    logger.info("Worker stopped gracefully")


if __name__ == "__main__":
    asyncio.run(main())
