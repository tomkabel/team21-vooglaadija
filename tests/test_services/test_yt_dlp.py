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


def _make_ytdlp_mock(title="Test Video", ext="mp4"):
    """Helper to create a properly mocked YoutubeDL context manager."""
    mock_instance = MagicMock()
    mock_instance.extract_info.return_value = {"title": title, "ext": ext}
    mock_yt = MagicMock()
    mock_yt.return_value.__enter__ = MagicMock(return_value=mock_instance)
    mock_yt.return_value.__exit__ = MagicMock(return_value=False)
    return mock_yt, mock_instance


class TestExtractMediaUrl:
    """Tests for extract_media_url function."""

    @pytest.fixture
    def temp_storage_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_extract_media_url_returns_tuple(self, temp_storage_path, sample_url):
        mock_yt, _ = _make_ytdlp_mock()
        with patch("app.services.yt_dlp_service.yt_dlp.YoutubeDL", mock_yt):
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

        mock_yt, _ = _make_ytdlp_mock()
        with patch("app.services.yt_dlp_service.yt_dlp.YoutubeDL", mock_yt):
            with patch("app.services.yt_dlp_service.os.path.isfile", return_value=True):
                await extract_media_url(sample_url, temp_storage_path)
                assert os.path.exists(download_dir)

    @pytest.mark.asyncio
    async def test_extract_media_url_uses_uuid_filename(self, temp_storage_path, sample_url):
        mock_yt, _ = _make_ytdlp_mock()
        with patch("app.services.yt_dlp_service.yt_dlp.YoutubeDL", mock_yt):
            with patch("app.services.yt_dlp_service.os.path.isfile", return_value=True):
                file_path, _ = await extract_media_url(sample_url, temp_storage_path)

                # file_path should contain a UUID, NOT the title
                file_id = os.path.basename(file_path).replace(".mp4", "")
                uuid.UUID(file_id)  # Should not raise

    @pytest.mark.asyncio
    async def test_extract_media_url_path_uses_only_uuid(self, temp_storage_path, sample_url):
        """Critical: file path must NOT contain the video title (prevents injection)."""
        mock_yt, _ = _make_ytdlp_mock(title="../../etc/passwd")
        with patch("app.services.yt_dlp_service.yt_dlp.YoutubeDL", mock_yt):
            with patch("app.services.yt_dlp_service.os.path.isfile", return_value=True):
                file_path, file_name = await extract_media_url(sample_url, temp_storage_path)

                # file_path must NOT contain path traversal
                assert "../../etc/passwd" not in file_path
                assert ".." not in file_path
                # file_name is sanitized (for display only)
                assert ".." not in file_name

    @pytest.mark.asyncio
    async def test_extract_media_url_file_extension(self, temp_storage_path, sample_url):
        mock_yt, _ = _make_ytdlp_mock(ext="webm")
        with patch("app.services.yt_dlp_service.yt_dlp.YoutubeDL", mock_yt):
            with patch("app.services.yt_dlp_service.os.path.isfile", return_value=True):
                file_path, file_name = await extract_media_url(sample_url, temp_storage_path)

                assert file_path.endswith(".webm")
                assert file_name.endswith(".webm")

    @pytest.mark.asyncio
    async def test_extract_media_url_fallback_extension(self, temp_storage_path, sample_url):
        mock_yt, _ = _make_ytdlp_mock(ext=None)
        with patch("app.services.yt_dlp_service.yt_dlp.YoutubeDL", mock_yt):
            with patch("app.services.yt_dlp_service.os.path.isfile", return_value=True):
                file_path, file_name = await extract_media_url(sample_url, temp_storage_path)

                assert file_path.endswith(".mp4")
                assert file_name.endswith(".mp4")

    @pytest.mark.asyncio
    async def test_extract_media_url_sanitizes_title_for_filename(
        self, temp_storage_path, sample_url
    ):
        """Title in file_name is sanitized (display only)."""
        mock_yt, _ = _make_ytdlp_mock(title="My Cool Video")
        with patch("app.services.yt_dlp_service.yt_dlp.YoutubeDL", mock_yt):
            with patch("app.services.yt_dlp_service.os.path.isfile", return_value=True):
                _, file_name = await extract_media_url(sample_url, temp_storage_path)

                assert "My Cool Video" in file_name

    @pytest.mark.asyncio
    async def test_extract_media_url_yt_dlp_options(self, temp_storage_path, sample_url):
        mock_yt, _mock_instance = _make_ytdlp_mock()
        with patch("app.services.yt_dlp_service.yt_dlp.YoutubeDL", mock_yt):
            with patch("app.services.yt_dlp_service.os.path.isfile", return_value=True):
                await extract_media_url(sample_url, temp_storage_path)

                mock_yt.assert_called_once()
                call_args = mock_yt.call_args
                args, _ = call_args
                ydl_opts = args[0] if args else {}

                assert ydl_opts.get("format") == "best[ext=mp4]/best"
                assert "quiet" in ydl_opts
                assert "no_warnings" in ydl_opts
                assert "outtmpl" in ydl_opts
                assert "socket_timeout" in ydl_opts
                assert "retries" in ydl_opts
