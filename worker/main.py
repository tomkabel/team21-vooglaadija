import asyncio
import logging
import os
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.models.download_job import DownloadJob
from worker.processor import process_next_job

logger = logging.getLogger(__name__)

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def cleanup_expired_jobs() -> int:
    """Delete expired jobs and their files. Returns number of jobs cleaned up."""
    async with AsyncSessionLocal() as db:
        expired_time = datetime.now(UTC) - timedelta(hours=settings.file_expire_hours)

        result = await db.execute(
            select(DownloadJob).where(
                DownloadJob.expires_at < expired_time, DownloadJob.status == "completed"
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
    cleanup_counter = 0
    cleanup_interval = 100  # Run cleanup every 100 iterations

    while True:
        await process_next_job()

        # Run cleanup every N iterations (approximately every N seconds)
        cleanup_counter += 1
        if cleanup_counter >= cleanup_interval:
            try:
                await cleanup_expired_jobs()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")
            cleanup_counter = 0

        await asyncio.sleep(1)  # Brief pause between jobs


if __name__ == "__main__":
    asyncio.run(main())
