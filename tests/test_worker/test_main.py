"""Tests for worker main module."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from app.config import settings
from app.models.download_job import DownloadJob
from worker.main import cleanup_expired_jobs


class TestCleanupExpiredJobs:
    """Tests for cleanup_expired_jobs function."""

    @pytest.mark.unit
    async def test_cleanup_expired_jobs_no_expired(self, db_session):
        """Test cleanup when no jobs are expired."""
        # Create a job that expires in the future
        future_time = datetime.now(UTC) + timedelta(hours=24)
        job = DownloadJob(
            id="future-job",
            user_id="user-456",
            url="https://www.youtube.com/watch?v=test",
            status="completed",
            expires_at=future_time,
        )
        db_session.add(job)
        await db_session.commit()

        count = await cleanup_expired_jobs()
        assert count == 0

    @pytest.mark.unit
    async def test_cleanup_expired_jobs_deletes_expired(self, db_session):
        """Test cleanup deletes expired jobs."""
        # Create an expired job with file path within storage
        past_time = datetime.now(UTC) - timedelta(hours=1)
        job = DownloadJob(
            id="expired-job-1",
            user_id="user-456",
            url="https://www.youtube.com/watch?v=test",
            status="completed",
            expires_at=past_time,
            file_path=f"{settings.storage_path}/test.mp4",
        )
        db_session.add(job)
        await db_session.commit()

        # Mock file operations to avoid actual file deletion
        with patch(
            "worker.main.os.path.realpath", return_value=f"{settings.storage_path}/test.mp4"
        ):
            with patch("worker.main.os.path.exists", return_value=False):
                with patch("worker.main.os.remove", create=True):
                    count = await cleanup_expired_jobs()
                    assert count == 1

    @pytest.mark.unit
    async def test_cleanup_expired_jobs_skips_path_traversal(self, db_session):
        """Test cleanup skips files outside storage directory."""
        # Create an expired job with a path outside storage
        past_time = datetime.now(UTC) - timedelta(hours=1)
        job = DownloadJob(
            id="path-traversal-job",
            user_id="user-456",
            url="https://www.youtube.com/watch?v=test",
            status="completed",
            expires_at=past_time,
            file_path="/etc/passwd",  # Dangerous path
        )
        db_session.add(job)
        await db_session.commit()

        # Mock realpath to return actual paths - job file outside storage, but settings storage properly
        storage_base = settings.storage_path
        with patch("worker.main.os.path.realpath") as mock_realpath:

            def realpath_side_effect(path):
                if path == "/etc/passwd":
                    return "/etc/passwd"  # Outside storage
                elif path == settings.storage_path:
                    return storage_base  # Actual storage path
                return path

            mock_realpath.side_effect = realpath_side_effect

            with patch("worker.main.os.path.exists", return_value=True):
                with patch("worker.main.os.remove") as mock_remove:
                    count = await cleanup_expired_jobs()
                    # Job should be deleted but file should NOT be removed
                    assert count == 1
                    mock_remove.assert_not_called()

    @pytest.mark.unit
    async def test_cleanup_expired_jobs_handles_missing_file(self, db_session):
        """Test cleanup handles missing files gracefully."""
        # Create an expired job pointing to non-existent file
        past_time = datetime.now(UTC) - timedelta(hours=1)
        job = DownloadJob(
            id="missing-file-job",
            user_id="user-456",
            url="https://www.youtube.com/watch?v=test",
            status="completed",
            expires_at=past_time,
            file_path=f"{settings.storage_path}/nonexistent.mp4",
        )
        db_session.add(job)
        await db_session.commit()

        # os.path.exists returns False for missing file
        with patch(
            "worker.main.os.path.realpath", return_value=f"{settings.storage_path}/nonexistent.mp4"
        ):
            with patch("worker.main.os.path.exists", return_value=False):
                with patch("worker.main.os.remove") as mock_remove:
                    count = await cleanup_expired_jobs()
                    # Job should still be deleted even if file doesn't exist
                    assert count == 1
                    mock_remove.assert_not_called()

    @pytest.mark.unit
    async def test_cleanup_expired_jobs_ignores_pending(self, db_session):
        """Test cleanup ignores pending jobs even if expired."""
        # Create a pending job that's past its expiry
        past_time = datetime.now(UTC) - timedelta(hours=1)
        job = DownloadJob(
            id="pending-expired-job",
            user_id="user-456",
            url="https://www.youtube.com/watch?v=test",
            status="pending",  # Not completed
            expires_at=past_time,
        )
        db_session.add(job)
        await db_session.commit()

        count = await cleanup_expired_jobs()
        # Should not delete pending job even though expired
        assert count == 0

    @pytest.mark.unit
    async def test_cleanup_expired_jobs_ignores_failed(self, db_session):
        """Test cleanup ignores failed jobs even if expired."""
        # Create a failed job that's past its expiry
        past_time = datetime.now(UTC) - timedelta(hours=1)
        job = DownloadJob(
            id="failed-expired-job",
            user_id="user-456",
            url="https://www.youtube.com/watch?v=test",
            status="failed",
            expires_at=past_time,
        )
        db_session.add(job)
        await db_session.commit()

        count = await cleanup_expired_jobs()
        # Should not delete failed job even though expired
        assert count == 0

    @pytest.mark.unit
    async def test_cleanup_expired_jobs_multiple(self, db_session):
        """Test cleanup handles multiple expired jobs."""
        past_time = datetime.now(UTC) - timedelta(hours=1)

        # Create multiple expired jobs
        for i in range(3):
            job = DownloadJob(
                id=f"multi-expired-job-{i}",
                user_id="user-456",
                url="https://www.youtube.com/watch?v=test",
                status="completed",
                expires_at=past_time,
                file_path=f"{settings.storage_path}/test{i}.mp4",
            )
            db_session.add(job)
        await db_session.commit()

        with patch(
            "worker.main.os.path.realpath", return_value=f"{settings.storage_path}/test0.mp4"
        ):
            with patch("worker.main.os.path.exists", return_value=False):
                count = await cleanup_expired_jobs()
                assert count == 3
