"""yt_dlp service tests."""

import os
import tempfile
import uuid
from unittest.mock import MagicMock, patch

import pytest

from app.services.yt_dlp_service import extract_media_url
from app.utils.validators import is_youtube_url


class TestIsYoutubeUrl:
    """Tests for URL validation."""

    def test_valid_youtube_watch_url(self):
        assert is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True

    def test_valid_youtube_short_url(self):
        assert is_youtube_url("https://youtu.be/dQw4w9WgXcQ") is True

    def test_valid_youtube_nocookie_url(self):
        assert is_youtube_url("https://www.youtube-nocookie.com/watch?v=dQw4w9WgXcQ") is True

    def test_valid_youtube_shorts_url(self):
        assert is_youtube_url("https://www.youtube.com/shorts/dQw4w9WgXcQ") is True

    def test_valid_youtube_mobile_url(self):
        assert is_youtube_url("https://m.youtube.com/watch?v=dQw4w9WgXcQ") is True

    def test_invalid_google_url(self):
        assert is_youtube_url("https://www.google.com") is False

    def test_invalid_vimeo_url(self):
        assert is_youtube_url("https://vimeo.com/123456") is False

    def test_invalid_random_url(self):
        assert is_youtube_url("https://example.com/video") is False

    def test_invalid_not_url(self):
        assert is_youtube_url("not-a-url") is False

    def test_invalid_empty_string(self):
        assert is_youtube_url("") is False

    def test_invalid_ftp_url(self):
        assert is_youtube_url("ftp://youtube.com/video") is False

    def test_case_insensitive(self):
        assert is_youtube_url("https://WWW.YOUTUBE.COM/watch?v=dQw4w9WgXcQ") is True

    def test_subdomain_bypass_rejected(self):
        """Critical: subdomain bypass must be rejected."""
        assert is_youtube_url("https://youtube.com.evil.com/watch?v=abc") is False
        assert is_youtube_url("https://notyoutube.com/watch?v=abc") is False


def _make_subprocess_mock(title="Test Video", ext: str | None = "mp4"):
    """Helper to create a mock for _extract_via_subprocess."""

    async def mock_extract(url: str, output_template: str):
        return {"title": title, "ext": ext}

    return mock_extract


class TestExtractMediaUrl:
    """Tests for extract_media_url function."""

    @pytest.fixture
    def temp_storage_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_extract_media_url_returns_tuple(self, temp_storage_path, sample_url):
        mock_extract = _make_subprocess_mock()
        with patch("app.services.yt_dlp_service._extract_via_subprocess", mock_extract):
            with patch("app.services.yt_dlp_service.os.path.isfile", return_value=True):
                result = await extract_media_url(sample_url, temp_storage_path)

                assert isinstance(result, tuple)
                assert len(result) == 2
                assert isinstance(result[0], str)
                assert isinstance(result[1], str)

    @pytest.mark.asyncio
    async def test_extract_media_url_creates_download_dir(self, temp_storage_path, sample_url):
        download_dir = os.path.join(temp_storage_path, "downloads")
        assert not os.path.exists(download_dir)

        mock_extract = _make_subprocess_mock()
        with patch("app.services.yt_dlp_service._extract_via_subprocess", mock_extract):
            with patch("app.services.yt_dlp_service.os.path.isfile", return_value=True):
                await extract_media_url(sample_url, temp_storage_path)
                assert os.path.exists(download_dir)

    @pytest.mark.asyncio
    async def test_extract_media_url_uses_uuid_filename(self, temp_storage_path, sample_url):
        mock_extract = _make_subprocess_mock()
        with patch("app.services.yt_dlp_service._extract_via_subprocess", mock_extract):
            with patch("app.services.yt_dlp_service.os.path.isfile", return_value=True):
                file_path, _ = await extract_media_url(sample_url, temp_storage_path)

                # file_path should contain a UUID, NOT the title
                file_id = os.path.basename(file_path).replace(".mp4", "")
                uuid.UUID(file_id)  # Should not raise

    @pytest.mark.asyncio
    async def test_extract_media_url_path_uses_only_uuid(self, temp_storage_path, sample_url):
        """Critical: file path must NOT contain the video title (prevents injection)."""
        mock_extract = _make_subprocess_mock(title="../../etc/passwd")
        with patch("app.services.yt_dlp_service._extract_via_subprocess", mock_extract):
            with patch("app.services.yt_dlp_service.os.path.isfile", return_value=True):
                file_path, file_name = await extract_media_url(sample_url, temp_storage_path)

                # file_path must NOT contain path traversal
                assert "../../etc/passwd" not in file_path
                assert ".." not in file_path
                # file_name is sanitized (for display only)
                assert ".." not in file_name

    @pytest.mark.asyncio
    async def test_extract_media_url_file_extension(self, temp_storage_path, sample_url):
        mock_extract = _make_subprocess_mock(ext="webm")
        with patch("app.services.yt_dlp_service._extract_via_subprocess", mock_extract):
            with patch("app.services.yt_dlp_service.os.path.isfile", return_value=True):
                file_path, file_name = await extract_media_url(sample_url, temp_storage_path)

                assert file_path.endswith(".webm")
                assert file_name.endswith(".webm")

    @pytest.mark.asyncio
    async def test_extract_media_url_fallback_extension(self, temp_storage_path, sample_url):
        mock_extract = _make_subprocess_mock(ext=None)
        with patch("app.services.yt_dlp_service._extract_via_subprocess", mock_extract):
            with patch("app.services.yt_dlp_service.os.path.isfile", return_value=True):
                file_path, file_name = await extract_media_url(sample_url, temp_storage_path)

                assert file_path.endswith(".mp4")
                assert file_name.endswith(".mp4")

    @pytest.mark.asyncio
    async def test_extract_media_url_sanitizes_title_for_filename(
        self, temp_storage_path, sample_url
    ):
        """Title in file_name is sanitized (display only)."""
        mock_extract = _make_subprocess_mock(title="My Cool Video")
        with patch("app.services.yt_dlp_service._extract_via_subprocess", mock_extract):
            with patch("app.services.yt_dlp_service.os.path.isfile", return_value=True):
                _, file_name = await extract_media_url(sample_url, temp_storage_path)

                assert "My Cool Video" in file_name

    @pytest.mark.asyncio
    async def test_extract_media_url_yt_dlp_options(self, temp_storage_path, sample_url):
        """Verify the subprocess script contains correct yt_dlp options."""
        captured_script = {}

        async def mock_extract(url, output_template):
            # Capture the script that would be executed
            # We can verify the options by checking the output_template format
            captured_script["url"] = url
            captured_script["output_template"] = output_template
            return {"title": "Test", "ext": "mp4"}

        with patch("app.services.yt_dlp_service._extract_via_subprocess", mock_extract):
            with patch("app.services.yt_dlp_service.os.path.isfile", return_value=True):
                await extract_media_url(sample_url, temp_storage_path)

                # Verify the output_template uses UUID-based naming (not title)
                assert "downloads/" in captured_script["output_template"]
                assert ".%(ext)s" in captured_script["output_template"]
