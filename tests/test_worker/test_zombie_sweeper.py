"""Tests for zombie sweeper functionality.

The zombie sweeper requeues jobs that have been stuck in 'processing'
status for too long, indicating a worker crashed or stalled.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from sqlalchemy import select

from app.models.download_job import DownloadJob


@pytest.fixture
def user_id() -> UUID:
    """Fixed user ID for consistent testing."""
    return UUID("550e8400-e29b-41d4-a716-446655440001")


@pytest.fixture
async def stuck_processing_job(db_session, user_id) -> DownloadJob:
    """Create a job stuck in processing state for 20 minutes."""
    job = DownloadJob(
        id=UUID("550e8400-e29b-41d4-a716-446655441001"),
        user_id=user_id,
        url="https://www.youtube.com/watch?v=stuck",
        status="processing",
        updated_at=datetime.now(UTC) - timedelta(minutes=20),
    )
    db_session.add(job)
    await db_session.commit()
    return job


@pytest.fixture
async def recent_processing_job(db_session, user_id) -> DownloadJob:
    """Create a job in processing state but only 5 minutes old."""
    job = DownloadJob(
        id=UUID("550e8400-e29b-41d4-a716-446655441002"),
        user_id=user_id,
        url="https://www.youtube.com/watch?v=recent",
        status="processing",
        updated_at=datetime.now(UTC) - timedelta(minutes=5),
    )
    db_session.add(job)
    await db_session.commit()
    return job


@pytest.fixture
async def pending_job(db_session, user_id) -> DownloadJob:
    """Create a pending job."""
    job = DownloadJob(
        id=UUID("550e8400-e29b-41d4-a716-446655441003"),
        user_id=user_id,
        url="https://www.youtube.com/watch?v=pending",
        status="pending",
    )
    db_session.add(job)
    await db_session.commit()
    return job


@pytest.fixture
async def completed_job(db_session, user_id) -> DownloadJob:
    """Create a completed job."""
    job = DownloadJob(
        id=UUID("550e8400-e29b-41d4-a716-446655441004"),
        user_id=user_id,
        url="https://www.youtube.com/watch?v=completed",
        status="completed",
    )
    db_session.add(job)
    await db_session.commit()
    return job


@pytest.fixture
async def failed_job(db_session, user_id) -> DownloadJob:
    """Create a failed job."""
    job = DownloadJob(
        id=UUID("550e8400-e29b-41d4-a716-446655441005"),
        user_id=user_id,
        url="https://www.youtube.com/watch?v=failed",
        status="failed",
        error="Previous failure",
    )
    db_session.add(job)
    await db_session.commit()
    return job


class TestRequeueStuckJobs:
    """Tests for requeue_stuck_jobs function."""

    @pytest.mark.unit
    async def test_requeue_stuck_jobs_finds_stuck_processing_jobs(
        self, db_session, stuck_processing_job
    ):
        """Test that stuck jobs in processing status are found."""
        stuck_job_id = stuck_processing_job.id

        mock_redis = AsyncMock()
        mock_redis.lpush = AsyncMock(return_value=1)

        with patch("worker.zombie_sweeper.redis_client", mock_redis):
            from worker.zombie_sweeper import requeue_stuck_jobs

            count = await requeue_stuck_jobs(timeout_minutes=15)

            assert count >= 1
            mock_redis.lpush.assert_called()

    @pytest.mark.unit
    async def test_requeue_stuck_jobs_resets_status_to_pending(self, db_session, user_id):
        """Test that stuck jobs are set to 'pending', NOT 'failed'."""
        job_id = UUID("550e8400-e29b-41d4-a716-446655441010")
        job = DownloadJob(
            id=job_id,
            user_id=user_id,
            url="https://www.youtube.com/watch?v=stuck_reset",
            status="processing",
            updated_at=datetime.now(UTC) - timedelta(minutes=20),
        )
        db_session.add(job)
        await db_session.commit()

        mock_redis = AsyncMock()
        mock_redis.lpush = AsyncMock(return_value=1)

        with patch("worker.zombie_sweeper.redis_client", mock_redis):
            from worker.zombie_sweeper import requeue_stuck_jobs

            count = await requeue_stuck_jobs(timeout_minutes=15)

            assert count == 1
            assert mock_redis.lpush.call_count == 1

            await db_session.refresh(job)
            assert job.status == "pending"

    @pytest.mark.unit
    async def test_requeue_stuck_jobs_returns_count(self, db_session, user_id):
        """Test that the function returns the count of requeued jobs."""
        job1_id = UUID("550e8400-e29b-41d4-a716-446655441011")
        job2_id = UUID("550e8400-e29b-41d4-a716-446655441012")

        for job_id in [job1_id, job2_id]:
            job = DownloadJob(
                id=job_id,
                user_id=user_id,
                url="https://www.youtube.com/watch?v=stuck",
                status="processing",
                updated_at=datetime.now(UTC) - timedelta(minutes=30),
            )
            db_session.add(job)
        await db_session.commit()

        mock_redis = AsyncMock()
        mock_redis.lpush = AsyncMock(return_value=1)

        with patch("worker.zombie_sweeper.redis_client", mock_redis):
            from worker.zombie_sweeper import requeue_stuck_jobs

            count = await requeue_stuck_jobs(timeout_minutes=15)

            assert count == 2

    @pytest.mark.unit
    async def test_requeue_stuck_jobs_ignores_pending(self, db_session, pending_job):
        """Test that pending jobs are NOT affected."""
        pending_job_id = pending_job.id

        mock_redis = AsyncMock()

        with patch("worker.zombie_sweeper.redis_client", mock_redis):
            from worker.zombie_sweeper import requeue_stuck_jobs

            count = await requeue_stuck_jobs(timeout_minutes=15)

            assert count == 0
            mock_redis.lpush.assert_not_called()

        result = await db_session.execute(
            select(DownloadJob).where(DownloadJob.id == pending_job_id)
        )
        job = result.scalar_one()
        assert job.status == "pending"

    @pytest.mark.unit
    async def test_requeue_stuck_jobs_ignores_completed(self, db_session, completed_job):
        """Test that completed jobs are NOT affected."""
        completed_job_id = completed_job.id

        mock_redis = AsyncMock()

        with patch("worker.zombie_sweeper.redis_client", mock_redis):
            from worker.zombie_sweeper import requeue_stuck_jobs

            count = await requeue_stuck_jobs(timeout_minutes=15)

            assert count == 0
            mock_redis.lpush.assert_not_called()

        result = await db_session.execute(
            select(DownloadJob).where(DownloadJob.id == completed_job_id)
        )
        job = result.scalar_one()
        assert job.status == "completed"

    @pytest.mark.unit
    async def test_requeue_stuck_jobs_ignores_failed(self, db_session, failed_job):
        """Test that failed jobs are NOT affected."""
        failed_job_id = failed_job.id

        mock_redis = AsyncMock()

        with patch("worker.zombie_sweeper.redis_client", mock_redis):
            from worker.zombie_sweeper import requeue_stuck_jobs

            count = await requeue_stuck_jobs(timeout_minutes=15)

            assert count == 0
            mock_redis.lpush.assert_not_called()

        result = await db_session.execute(
            select(DownloadJob).where(DownloadJob.id == failed_job_id)
        )
        job = result.scalar_one()
        assert job.status == "failed"

    @pytest.mark.unit
    async def test_requeue_stuck_jobs_ignores_recent_processing(
        self, db_session, recent_processing_job
    ):
        """Test that processing jobs that are not stuck (too recent) are NOT affected."""
        recent_job_id = recent_processing_job.id

        mock_redis = AsyncMock()

        with patch("worker.zombie_sweeper.redis_client", mock_redis):
            from worker.zombie_sweeper import requeue_stuck_jobs

            count = await requeue_stuck_jobs(timeout_minutes=15)

            assert count == 0
            mock_redis.lpush.assert_not_called()

        result = await db_session.execute(
            select(DownloadJob).where(DownloadJob.id == recent_job_id)
        )
        job = result.scalar_one()
        assert job.status == "processing"

    @pytest.mark.unit
    async def test_requeue_stuck_jobs_boundary_condition(self, db_session, user_id):
        """Test boundary: job exactly at timeout should be requeued."""
        boundary_job_id = UUID("550e8400-e29b-41d4-a716-446655441020")

        exactly_at_timeout = datetime.now(UTC) - timedelta(minutes=15, seconds=1)
        job = DownloadJob(
            id=boundary_job_id,
            user_id=user_id,
            url="https://www.youtube.com/watch?v=boundary",
            status="processing",
            updated_at=exactly_at_timeout,
        )
        db_session.add(job)
        await db_session.commit()

        mock_redis = AsyncMock()
        mock_redis.lpush = AsyncMock(return_value=1)

        with patch("worker.zombie_sweeper.redis_client", mock_redis):
            from worker.zombie_sweeper import requeue_stuck_jobs

            count = await requeue_stuck_jobs(timeout_minutes=15)

            assert count == 1
            mock_redis.lpush.assert_called_once()

    @pytest.mark.unit
    async def test_requeue_stuck_jobs_just_under_timeout(self, db_session, user_id):
        """Test boundary: job just under timeout should NOT be requeued."""
        just_under_timeout_id = UUID("550e8400-e29b-41d4-a716-446655441021")

        just_under_timeout = datetime.now(UTC) - timedelta(minutes=14, seconds=59)
        job = DownloadJob(
            id=just_under_timeout_id,
            user_id=user_id,
            url="https://www.youtube.com/watch?v=just_under",
            status="processing",
            updated_at=just_under_timeout,
        )
        db_session.add(job)
        await db_session.commit()

        mock_redis = AsyncMock()

        with patch("worker.zombie_sweeper.redis_client", mock_redis):
            from worker.zombie_sweeper import requeue_stuck_jobs

            count = await requeue_stuck_jobs(timeout_minutes=15)

            assert count == 0
            mock_redis.lpush.assert_not_called()

        result = await db_session.execute(
            select(DownloadJob).where(DownloadJob.id == just_under_timeout_id)
        )
        still_processing = result.scalar_one()
        assert still_processing.status == "processing"

    @pytest.mark.unit
    async def test_requeue_stuck_jobs_with_mixed_job_types(self, db_session, user_id):
        """Test with a mix of job types - only stuck processing jobs are requeued."""
        stuck_job_id = UUID("550e8400-e29b-41d4-a716-446655441030")
        pending_job_id = UUID("550e8400-e29b-41d4-a716-446655441031")
        completed_job_id = UUID("550e8400-e29b-41d4-a716-446655441032")
        recent_processing_id = UUID("550e8400-e29b-41d4-a716-446655441033")

        jobs_data = [
            (stuck_job_id, "processing", datetime.now(UTC) - timedelta(minutes=20)),
            (pending_job_id, "pending", datetime.now(UTC)),
            (completed_job_id, "completed", datetime.now(UTC)),
            (recent_processing_id, "processing", datetime.now(UTC) - timedelta(minutes=5)),
        ]

        for job_id, status, updated_at in jobs_data:
            job = DownloadJob(
                id=job_id,
                user_id=user_id,
                url=f"https://www.youtube.com/watch?v={job_id}",
                status=status,
                updated_at=updated_at,
            )
            db_session.add(job)
        await db_session.commit()

        mock_redis = AsyncMock()
        mock_redis.lpush = AsyncMock(return_value=1)

        with patch("worker.zombie_sweeper.redis_client", mock_redis):
            from worker.zombie_sweeper import requeue_stuck_jobs

            count = await requeue_stuck_jobs(timeout_minutes=15)

            assert count == 1
            mock_redis.lpush.assert_called_once_with("download_queue", str(stuck_job_id))


class TestRequeueStuckJobsEdgeCases:
    """Edge case tests for requeue_stuck_jobs."""

    @pytest.fixture
    def user_id(self) -> UUID:
        """Fixed user ID for consistent testing."""
        return UUID("550e8400-e29b-41d4-a716-446655440002")

    @pytest.mark.unit
    async def test_requeue_stuck_jobs_empty_database(self, db_session):
        """Test with no jobs in database - should return 0."""
        mock_redis = AsyncMock()

        with patch("worker.zombie_sweeper.redis_client", mock_redis):
            from worker.zombie_sweeper import requeue_stuck_jobs

            count = await requeue_stuck_jobs(timeout_minutes=15)

            assert count == 0
            mock_redis.lpush.assert_not_called()

    @pytest.mark.unit
    async def test_requeue_stuck_jobs_all_stuck(self, db_session, user_id):
        """Test when all processing jobs are stuck."""
        stuck_job_ids = [
            UUID("550e8400-e29b-41d4-a716-446655441040"),
            UUID("550e8400-e29b-41d4-a716-446655441041"),
            UUID("550e8400-e29b-41d4-a716-446655441042"),
        ]

        for job_id in stuck_job_ids:
            job = DownloadJob(
                id=job_id,
                user_id=user_id,
                url="https://www.youtube.com/watch?v=stuck",
                status="processing",
                updated_at=datetime.now(UTC) - timedelta(minutes=30),
            )
            db_session.add(job)
        await db_session.commit()

        mock_redis = AsyncMock()
        mock_redis.lpush = AsyncMock(return_value=1)

        with patch("worker.zombie_sweeper.redis_client", mock_redis):
            from worker.zombie_sweeper import requeue_stuck_jobs

            count = await requeue_stuck_jobs(timeout_minutes=15)

            assert count == 3
            assert mock_redis.lpush.call_count == 3

    @pytest.mark.unit
    async def test_requeue_stuck_jobs_no_stuck_jobs(self, db_session, user_id):
        """Test when there are no stuck jobs."""
        job = DownloadJob(
            id=UUID("550e8400-e29b-41d4-a716-446655441050"),
            user_id=user_id,
            url="https://www.youtube.com/watch?v=recent",
            status="processing",
            updated_at=datetime.now(UTC) - timedelta(minutes=5),
        )
        db_session.add(job)
        await db_session.commit()

        mock_redis = AsyncMock()

        with patch("worker.zombie_sweeper.redis_client", mock_redis):
            from worker.zombie_sweeper import requeue_stuck_jobs

            count = await requeue_stuck_jobs(timeout_minutes=15)

            assert count == 0
            mock_redis.lpush.assert_not_called()
