"""Zombie Sweeper module for handling jobs stuck in PROCESSING state.

This module handles SIGKILL/OOM scenarios where graceful shutdown never runs.
It polls for jobs that have been stuck in 'PROCESSING' status for too long
and requeues them as 'pending' instead of marking them as failed.

Poll interval: 5 minutes
Timeout: 15 minutes stuck in 'PROCESSING' = zombie
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update

from app.database import get_async_session_factory
from app.logging_config import get_logger
from app.models.download_job import DownloadJob
from worker.queue import redis_client

logger = get_logger(__name__)


async def requeue_stuck_jobs(timeout_minutes: int = 15) -> int:
    """Requeue jobs that have been stuck in 'PROCESSING' status too long.

    These are "zombie" jobs - workers that were killed (SIGKILL/OOM) without
    running graceful shutdown, leaving jobs permanently stuck in PROCESSING.

    Instead of marking as 'failed', we requeue them as 'pending' so they
    can be retried by another worker.

    Args:
        timeout_minutes: Jobs stuck in PROCESSING for longer than this are requeued.

    Returns:
        Number of jobs requeued.
    """
    cutoff = datetime.now(UTC) - timedelta(minutes=timeout_minutes)
    session_factory = get_async_session_factory()

    async with session_factory() as db:
        result = await db.execute(
            select(DownloadJob).where(
                DownloadJob.status == "processing",
                DownloadJob.updated_at < cutoff,
            )
        )
        stuck_jobs = result.scalars().all()

        if not stuck_jobs:
            logger.debug("no_zombie_jobs_found", timeout_minutes=timeout_minutes)
            return 0

        requeued_count = 0
        for job in stuck_jobs:
            try:
                await db.execute(
                    update(DownloadJob)
                    .where(DownloadJob.id == job.id)
                    .values(
                        status="pending",
                        updated_at=datetime.now(UTC),
                    )
                )
                await redis_client.lpush("download_queue", str(job.id))
                requeued_count += 1
                logger.info(
                    "zombie_job_requeued",
                    job_id=str(job.id),
                    stuck_minutes=int((datetime.now(UTC) - job.updated_at).total_seconds() / 60),
                )
            except Exception as e:
                logger.error(
                    "failed_to_requeue_zombie_job",
                    job_id=str(job.id),
                    error=str(e),
                )

        await db.commit()

        if requeued_count > 0:
            logger.warning(
                "zombie_sweep_completed",
                requeued_count=requeued_count,
                total_stuck=len(stuck_jobs),
                timeout_minutes=timeout_minutes,
            )

        return requeued_count
