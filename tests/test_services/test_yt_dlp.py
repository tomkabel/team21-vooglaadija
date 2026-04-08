"""yt_dlp service tests."""

from __future__ import annotations

import asyncio
import tempfile
import uuid
from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from app.services.yt_dlp_service import StorageError, extract_media_url
from app.utils.validators import is_youtube_url


class TestIsYoutubeUrl:
    """Tests for URL validation."""

    def test_valid_youtube_watch_url(self) -> None:
        assert is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True

    def test_valid_youtube_short_url(self) -> None:
        assert is_youtube_url("https://youtu.be/dQw4w9WgXcQ") is True

    def test_valid_youtube_nocookie_url(self) -> None:
        assert is_youtube_url("https://www.youtube-nocookie.com/watch?v=dQw4w9WgXcQ") is True

    def test_valid_youtube_shorts_url(self) -> None:
        assert is_youtube_url("https://www.youtube.com/shorts/dQw4w9WgXcQ") is True

    def test_valid_youtube_mobile_url(self) -> None:
        assert is_youtube_url("https://m.youtube.com/watch?v=dQw4w9WgXcQ") is True

    def test_invalid_google_url(self) -> None:
        assert is_youtube_url("https://www.google.com") is False

    def test_invalid_vimeo_url(self) -> None:
        assert is_youtube_url("https://vimeo.com/123456") is False

    def test_invalid_random_url(self) -> None:
        assert is_youtube_url("https://example.com/video") is False

    def test_invalid_not_url(self) -> None:
        assert is_youtube_url("not-a-url") is False

    def test_invalid_empty_string(self) -> None:
        assert is_youtube_url("") is False

    def test_invalid_ftp_url(self) -> None:
        assert is_youtube_url("ftp://youtube.com/video") is False

    def test_case_insensitive(self) -> None:
        assert is_youtube_url("https://WWW.YOUTUBE.COM/watch?v=dQw4w9WgXcQ") is True

    def test_subdomain_bypass_rejected(self) -> None:
        """Critical: subdomain bypass must be rejected."""
        assert is_youtube_url("https://youtube.com.evil.com/watch?v=abc") is False
        assert is_youtube_url("https://notyoutube.com/watch?v=abc") is False


def _make_subprocess_mock(title: str = "Test Video", ext: str | None = "mp4") -> AsyncMock:
    """Helper to create a mock for _extract_via_subprocess."""
    mock = AsyncMock()
    mock.return_value = {"title": title, "ext": ext}
    return mock


class TestExtractMediaUrl:
    """Tests for extract_media_url function."""

    @pytest.fixture
    def temp_storage_path(self) -> AsyncGenerator[Path, None]:
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.mark.asyncio
    async def test_extract_media_url_returns_tuple(
        self, temp_storage_path: Path, sample_url: str
    ) -> None:
        mock_extract = _make_subprocess_mock()
        with (
            patch("app.services.yt_dlp_service._extract_via_subprocess", mock_extract),
            patch("app.services.yt_dlp_service.os.path.isfile", return_value=True),
        ):
            result = await extract_media_url(sample_url, str(temp_storage_path))

            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], str)
            assert isinstance(result[1], str)

    @pytest.mark.asyncio
    async def test_extract_media_url_creates_download_dir(
        self, temp_storage_path: Path, sample_url: str
    ) -> None:
        download_dir = temp_storage_path / "downloads"
        assert not download_dir.exists()

        mock_extract = _make_subprocess_mock()
        with (
            patch("app.services.yt_dlp_service._extract_via_subprocess", mock_extract),
            patch("app.services.yt_dlp_service.os.path.isfile", return_value=True),
        ):
            await extract_media_url(sample_url, str(temp_storage_path))
            assert download_dir.exists()

    @pytest.mark.asyncio
    async def test_extract_media_url_uses_uuid_filename(
        self, temp_storage_path: Path, sample_url: str
    ) -> None:
        mock_extract = _make_subprocess_mock()
        with (
            patch("app.services.yt_dlp_service._extract_via_subprocess", mock_extract),
            patch("app.services.yt_dlp_service.os.path.isfile", return_value=True),
        ):
            file_path, _ = await extract_media_url(sample_url, str(temp_storage_path))

            # file_path should contain a UUID, NOT the title
            file_id = Path(file_path).stem
            uuid.UUID(file_id)  # Should not raise

    @pytest.mark.asyncio
    async def test_extract_media_url_path_uses_only_uuid(
        self, temp_storage_path: Path, sample_url: str
    ) -> None:
        """Critical: file path must NOT contain the video title (prevents injection)."""
        mock_extract = _make_subprocess_mock(title="../../etc/passwd")
        with (
            patch("app.services.yt_dlp_service._extract_via_subprocess", mock_extract),
            patch("app.services.yt_dlp_service.os.path.isfile", return_value=True),
        ):
            file_path, file_name = await extract_media_url(sample_url, str(temp_storage_path))

            # file_path must NOT contain path traversal
            assert "../../etc/passwd" not in file_path
            assert ".." not in file_path
            # file_name is sanitized (for display only)
            assert ".." not in file_name

    @pytest.mark.asyncio
    async def test_extract_media_url_file_extension(
        self, temp_storage_path: Path, sample_url: str
    ) -> None:
        mock_extract = _make_subprocess_mock(ext="webm")
        with (
            patch("app.services.yt_dlp_service._extract_via_subprocess", mock_extract),
            patch("app.services.yt_dlp_service.os.path.isfile", return_value=True),
        ):
            file_path, file_name = await extract_media_url(sample_url, str(temp_storage_path))

            assert file_path.endswith(".webm")
            assert file_name.endswith(".webm")

    @pytest.mark.asyncio
    async def test_extract_media_url_fallback_extension(
        self, temp_storage_path: Path, sample_url: str
    ) -> None:
        mock_extract = _make_subprocess_mock(ext=None)
        with (
            patch("app.services.yt_dlp_service._extract_via_subprocess", mock_extract),
            patch("app.services.yt_dlp_service.os.path.isfile", return_value=True),
        ):
            file_path, file_name = await extract_media_url(sample_url, str(temp_storage_path))

            assert file_path.endswith(".mp4")
            assert file_name.endswith(".mp4")

    @pytest.mark.asyncio
    async def test_extract_media_url_sanitizes_title_for_filename(
        self, temp_storage_path: Path, sample_url: str
    ) -> None:
        """Title in file_name is sanitized (display only)."""
        mock_extract = _make_subprocess_mock(title="My Cool Video")
        with (
            patch("app.services.yt_dlp_service._extract_via_subprocess", mock_extract),
            patch("app.services.yt_dlp_service.os.path.isfile", return_value=True),
        ):
            _, file_name = await extract_media_url(sample_url, str(temp_storage_path))

            assert "My Cool Video" in file_name

    @pytest.mark.asyncio
    async def test_extract_media_url_yt_dlp_options(
        self, temp_storage_path: Path, sample_url: str
    ) -> None:
        """Verify the asyncio.create_subprocess_exec call uses correct options."""
        captured_calls: list = []

        async def mock_subprocess_exec(*args, **kwargs):
            captured_calls.append({"args": args, "kwargs": kwargs})
            # Return a mock process
            mock_process = AsyncMock()
            mock_process.communicate = AsyncMock(
                return_value=(b'{"title": "Test", "ext": "mp4"}', b"")
            )
            mock_process.returncode = 0
            return mock_process

        with (
            patch(
                "app.services.yt_dlp_service.asyncio.create_subprocess_exec", mock_subprocess_exec
            ),
            patch("app.services.yt_dlp_service.os.path.isfile", return_value=True),
        ):
            await extract_media_url(sample_url, str(temp_storage_path))

            # Verify create_subprocess_exec was called
            assert len(captured_calls) == 1
            call_kwargs = captured_calls[0]["kwargs"]
            # Verify start_new_session=True is passed for proper process group handling
            assert call_kwargs.get("start_new_session") is True
            # Verify stdout and stderr pipes are configured
            assert call_kwargs.get("stdout") == asyncio.subprocess.PIPE
            assert call_kwargs.get("stderr") == asyncio.subprocess.PIPE

    @pytest.mark.asyncio
    async def test_extract_media_url_timeout_propagates(
        self, temp_storage_path: Path, sample_url: str
    ) -> None:
        """Verify asyncio.TimeoutError is raised when extraction times out."""

        async def mock_wait_for(coro, timeout=None):
            raise TimeoutError("timed out")

        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(return_value=(b'{"title": "Test", "ext": "mp4"}', b""))
        mock_process.returncode = 0
        mock_process.pid = 1234

        async def mock_subprocess_exec(*args, **kwargs):
            return mock_process

        with (
            patch(
                "app.services.yt_dlp_service.asyncio.create_subprocess_exec", mock_subprocess_exec
            ),
            patch("app.services.yt_dlp_service.asyncio.wait_for", mock_wait_for),
        ):
            with pytest.raises(asyncio.TimeoutError):
                await extract_media_url(sample_url, str(temp_storage_path))

    @pytest.mark.asyncio
    async def test_extract_media_url_makedirs_failure(
        self, temp_storage_path: Path, sample_url: str
    ) -> None:
        """Verify StorageError is raised when download directory creation fails."""
        with (
            patch(
                "app.services.yt_dlp_service.os.makedirs", side_effect=OSError("Permission denied")
            ),
        ):
            with pytest.raises(StorageError) as exc_info:
                await extract_media_url(sample_url, str(temp_storage_path))
            assert "Failed to create download directory" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_extract_media_url_missing_output_file(
        self, temp_storage_path: Path, sample_url: str
    ) -> None:
        """Verify StorageError is raised when output file is not found."""
        mock_extract = _make_subprocess_mock()
        with (
            patch("app.services.yt_dlp_service._extract_via_subprocess", mock_extract),
            patch("app.services.yt_dlp_service.os.path.isfile", return_value=False),
        ):
            with pytest.raises(StorageError) as exc_info:
                await extract_media_url(sample_url, str(temp_storage_path))
            assert "Expected output file not found" in str(exc_info.value)
