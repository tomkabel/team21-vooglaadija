"""Tests for worker processor module."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy import select

from app.models.download_job import DownloadJob


class TestProcessNextJob:
    """Tests for process_next_job function."""

    @pytest.fixture
    def mock_redis_client(self):
        """Create a mock Redis client."""
        mock = MagicMock()
        mock.rpop = AsyncMock(return_value=None)
        return mock

    @pytest.mark.unit
    async def test_process_next_job_empty_queue(self, db_session, mock_redis_client):
        """Test that processing an empty queue returns early."""
        from worker.processor import process_next_job

        with patch("worker.processor.redis_client", mock_redis_client):
            # No jobs in queue
            mock_redis_client.rpop = AsyncMock(return_value=None)

            # Should return without error
            await process_next_job()

        # Verify no jobs were processed
        mock_redis_client.rpop.assert_called_once_with("download_queue")

    @pytest.mark.unit
    async def test_process_next_job_not_found(self, db_session, mock_redis_client):
        """Test processing a job that doesn't exist in database."""
        from worker.processor import process_next_job

        with patch("worker.processor.redis_client", mock_redis_client):
            # Job exists in queue but not in database
            mock_redis_client.rpop = AsyncMock(return_value="non-existent-job-id")

            # Should log warning and return
            await process_next_job()

        mock_redis_client.rpop.assert_called_once()

    @pytest.mark.unit
    async def test_process_next_job_completes_success(self, db_session, mock_redis_client):
        """Test successful job completion."""
        from app.database import AsyncSessionLocal
        from worker.processor import process_next_job

        # Create a pending job in the database
        job = DownloadJob(
            id="test-job-123",
            user_id="user-456",
            url="https://www.youtube.com/watch?v=test",
            status="pending",
        )
        db_session.add(job)
        await db_session.commit()

        with patch("worker.processor.redis_client", mock_redis_client), patch(
            "worker.processor.extract_media_url", new_callable=AsyncMock,
        ) as mock_extract:
            mock_extract.return_value = ("/storage/test.mp4", "test.mp4")
            mock_redis_client.rpop = AsyncMock(return_value="test-job-123")

            await process_next_job()

        # Use a fresh session to read the job (bypass session cache)
        async with AsyncSessionLocal() as new_session:
            result = await new_session.execute(
                select(DownloadJob).where(DownloadJob.id == "test-job-123"),
            )
            completed_job = result.scalar_one()
            assert completed_job.status == "completed"
            assert completed_job.file_path == "/storage/test.mp4"
            assert completed_job.file_name == "test.mp4"
            assert completed_job.completed_at is not None

    @pytest.mark.unit
    async def test_process_next_job_handles_failure(self, db_session, mock_redis_client):
        """Test job failure handling."""
        from app.database import AsyncSessionLocal
        from worker.processor import process_next_job

        # Create a pending job in the database
        job = DownloadJob(
            id="test-job-fail",
            user_id="user-456",
            url="https://www.youtube.com/watch?v=test",
            status="pending",
        )
        db_session.add(job)
        await db_session.commit()

        with patch("worker.processor.redis_client", mock_redis_client), patch(
            "worker.processor.extract_media_url", new_callable=AsyncMock,
        ) as mock_extract:
            with patch("worker.processor.enqueue_job", new_callable=AsyncMock) as mock_enqueue:
                mock_extract.side_effect = Exception("Download failed")
                mock_redis_client.rpop = AsyncMock(return_value="test-job-fail")

                await process_next_job()

                # Verify job was re-queued for retry
                mock_enqueue.assert_called_once_with("test-job-fail")

        # Use a fresh session to read the job (bypass session cache)
        async with AsyncSessionLocal() as new_session:
            result = await new_session.execute(
                select(DownloadJob).where(DownloadJob.id == "test-job-fail"),
            )
            # Job should be re-queued as pending for retry (not immediately failed)
            failed_job = result.scalar_one()
            assert failed_job.status == "pending"
            assert failed_job.retry_count == 1
            assert "Download failed" in failed_job.error


class TestResetStuckJobs:
    """Tests for reset_stuck_jobs function."""

    @pytest.mark.unit
    async def test_reset_stuck_jobs_none_stuck(self, db_session):
        """Test no stuck jobs to reset."""
        from worker.processor import reset_stuck_jobs

        # No stuck jobs
        count = await reset_stuck_jobs(timeout_minutes=10)
        assert count == 0

    @pytest.mark.unit
    async def test_reset_stuck_jobs_resets_old_processing(self, db_session):
        """Test resetting jobs stuck in processing state."""
        from app.database import AsyncSessionLocal
        from worker.processor import reset_stuck_jobs

        # Create a job stuck in processing for 15 minutes
        old_time = datetime.now(UTC) - timedelta(minutes=15)
        job = DownloadJob(
            id="stuck-job-1",
            user_id="user-456",
            url="https://www.youtube.com/watch?v=test",
            status="processing",
            updated_at=old_time,
        )
        db_session.add(job)
        await db_session.commit()

        # Reset with 10 minute timeout
        count = await reset_stuck_jobs(timeout_minutes=10)
        assert count == 1

        # Use a fresh session to read the job (bypass session cache)
        async with AsyncSessionLocal() as new_session:
            result = await new_session.execute(
                select(DownloadJob).where(DownloadJob.id == "stuck-job-1"),
            )
            reset_job = result.scalar_one()
            # With retry mechanism, stuck jobs are re-queued as pending
            assert reset_job.status == "pending"
            assert "Job timed out" in reset_job.error

    @pytest.mark.unit
    async def test_reset_stuck_jobs_ignores_recent_processing(self, db_session):
        """Test that recently started processing jobs are not reset."""
        from worker.processor import reset_stuck_jobs

        # Create a job in processing state but only 5 minutes old
        recent_time = datetime.now(UTC) - timedelta(minutes=5)
        job = DownloadJob(
            id="recent-job",
            user_id="user-456",
            url="https://www.youtube.com/watch?v=test",
            status="processing",
            updated_at=recent_time,
        )
        db_session.add(job)
        await db_session.commit()

        # Reset with 10 minute timeout - should not affect recent job
        count = await reset_stuck_jobs(timeout_minutes=10)
        assert count == 0

        # Verify job still has processing status
        result = await db_session.execute(select(DownloadJob).where(DownloadJob.id == "recent-job"))
        still_processing = result.scalar_one()
        assert still_processing.status == "processing"

    @pytest.mark.unit
    async def test_reset_stuck_jobs_ignores_completed(self, db_session):
        """Test that completed jobs are not reset."""
        from worker.processor import reset_stuck_jobs

        # Create a completed job from 15 minutes ago
        old_time = datetime.now(UTC) - timedelta(minutes=15)
        job = DownloadJob(
            id="completed-job",
            user_id="user-456",
            url="https://www.youtube.com/watch?v=test",
            status="completed",
            updated_at=old_time,
        )
        db_session.add(job)
        await db_session.commit()

        # Reset with 10 minute timeout - should not affect completed job
        count = await reset_stuck_jobs(timeout_minutes=10)
        assert count == 0

        # Verify job still has completed status
        result = await db_session.execute(
            select(DownloadJob).where(DownloadJob.id == "completed-job"),
        )
        still_completed = result.scalar_one()
        assert still_completed.status == "completed"
