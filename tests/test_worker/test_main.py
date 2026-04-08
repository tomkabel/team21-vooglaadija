"""Tests for worker main module."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch
from uuid import UUID

import pytest

from app.config import settings
from app.models.download_job import DownloadJob
from worker.main import cleanup_expired_jobs

_DOWNLOADS_DIR = f"{settings.storage_path}/downloads"


class TestCleanupExpiredJobs:
    """Tests for cleanup_expired_jobs function."""

    @pytest.mark.unit
    async def test_cleanup_expired_jobs_no_expired(self, db_session):
        """Test cleanup when no jobs are expired."""
        # Create a job that expires in the future
        future_time = datetime.now(UTC) + timedelta(hours=24)
        job = DownloadJob(
            id=UUID("550e8400-e29b-41d4-a716-446655440020"),
            user_id=UUID("550e8400-e29b-41d4-a716-446655440005"),
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
        """Test cleanup deletes expired jobs and their files."""
        # Create an expired job with file path within downloads directory
        past_time = datetime.now(UTC) - timedelta(hours=1)
        job = DownloadJob(
            id=UUID("550e8400-e29b-41d4-a716-446655440021"),
            user_id=UUID("550e8400-e29b-41d4-a716-446655440005"),
            url="https://www.youtube.com/watch?v=test",
            status="completed",
            expires_at=past_time,
            file_path=f"{_DOWNLOADS_DIR}/test.mp4",
        )
        db_session.add(job)
        await db_session.commit()

        # Mock file operations: realpath resolves to downloads dir, file exists
        def mock_realpath(path):
            if path == settings.storage_path:
                return settings.storage_path
            if path == f"{settings.storage_path}/downloads":
                return f"{settings.storage_path}/downloads"
            return f"{_DOWNLOADS_DIR}/test.mp4"

        with (
            patch("worker.main.os.path.realpath", side_effect=mock_realpath),
            patch("worker.main.os.path.exists", return_value=True),
        ):
            with patch("worker.main.os.remove") as mock_remove:
                count = await cleanup_expired_jobs()
                assert count == 1
                mock_remove.assert_called_once()

    @pytest.mark.unit
    async def test_cleanup_expired_jobs_skips_path_traversal(self, db_session):
        """Test cleanup skips files outside storage directory."""
        past_time = datetime.now(UTC) - timedelta(hours=1)
        job = DownloadJob(
            id=UUID("550e8400-e29b-41d4-a716-446655440022"),
            user_id=UUID("550e8400-e29b-41d4-a716-446655440005"),
            url="https://www.youtube.com/watch?v=test",
            status="completed",
            expires_at=past_time,
            file_path="/etc/passwd",
        )
        db_session.add(job)
        await db_session.commit()

        def realpath_side_effect(path):
            if path == "/etc/passwd":
                return "/etc/passwd"
            if path == settings.storage_path or path == f"{settings.storage_path}/downloads":
                return f"{settings.storage_path}/downloads"
            return path

        with (
            patch("worker.main.os.path.realpath", side_effect=realpath_side_effect),
            patch("worker.main.os.path.exists", return_value=True),
        ):
            with patch("worker.main.os.remove") as mock_remove:
                count = await cleanup_expired_jobs()
                assert count == 0
                mock_remove.assert_not_called()

    @pytest.mark.unit
    async def test_cleanup_expired_jobs_handles_missing_file(self, db_session):
        """Test cleanup handles missing files gracefully."""
        past_time = datetime.now(UTC) - timedelta(hours=1)
        job = DownloadJob(
            id=UUID("550e8400-e29b-41d4-a716-446655440011"),
            user_id=UUID("550e8400-e29b-41d4-a716-446655440005"),
            url="https://www.youtube.com/watch?v=test",
            status="completed",
            expires_at=past_time,
            file_path=f"{_DOWNLOADS_DIR}/nonexistent.mp4",
        )
        db_session.add(job)
        await db_session.commit()

        def mock_realpath(path):
            if path == settings.storage_path or path == f"{settings.storage_path}/downloads":
                return f"{settings.storage_path}/downloads"
            return f"{_DOWNLOADS_DIR}/nonexistent.mp4"

        with (
            patch("worker.main.os.path.realpath", side_effect=mock_realpath),
            patch("worker.main.os.path.exists", return_value=False),
        ):
            with patch("worker.main.os.remove") as mock_remove:
                count = await cleanup_expired_jobs()
                assert count == 1
                mock_remove.assert_not_called()

    @pytest.mark.unit
    async def test_cleanup_expired_jobs_ignores_pending(self, db_session):
        """Test cleanup ignores pending jobs even if expired."""
        # Create a pending job that's past its expiry
        past_time = datetime.now(UTC) - timedelta(hours=1)
        job = DownloadJob(
            id=UUID("550e8400-e29b-41d4-a716-446655440010"),
            user_id=UUID("550e8400-e29b-41d4-a716-446655440005"),
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
            id=UUID("550e8400-e29b-41d4-a716-446655440012"),
            user_id=UUID("550e8400-e29b-41d4-a716-446655440005"),
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

        for i in range(3):
            job = DownloadJob(
                id=UUID(f"550e8400-e29b-41d4-a716-44665544002{i}"),
                user_id=UUID("550e8400-e29b-41d4-a716-446655440005"),
                url="https://www.youtube.com/watch?v=test",
                status="completed",
                expires_at=past_time,
                file_path=f"{_DOWNLOADS_DIR}/test{i}.mp4",
            )
            db_session.add(job)
        await db_session.commit()

        def mock_realpath(path):
            if path == settings.storage_path or path == f"{settings.storage_path}/downloads":
                return f"{settings.storage_path}/downloads"
            return f"{_DOWNLOADS_DIR}/test0.mp4"

        with (
            patch("worker.main.os.path.realpath", side_effect=mock_realpath),
            patch("worker.main.os.path.exists", return_value=False),
        ):
            count = await cleanup_expired_jobs()
            assert count == 3
