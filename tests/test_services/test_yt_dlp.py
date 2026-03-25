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
        """Test YouTube watch URL is valid."""
        assert is_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True

    def test_valid_youtube_short_url(self):
        """Test YouTube short URL is valid."""
        assert is_youtube_url("https://youtu.be/dQw4w9WgXcQ") is True

    def test_valid_youtube_nocookie_url(self):
        """Test YouTube no-cookie URL is valid."""
        assert is_youtube_url("https://www.youtube-nocookie.com/watch?v=dQw4w9WgXcQ") is True

    def test_valid_youtube_shorts_url(self):
        """Test YouTube shorts URL is valid."""
        assert is_youtube_url("https://www.youtube.com/shorts/dQw4w9WgXcQ") is True

    def test_valid_youtube_mobile_url(self):
        """Test YouTube mobile URL is valid."""
        assert is_youtube_url("https://m.youtube.com/watch?v=dQw4w9WgXcQ") is True

    def test_invalid_google_url(self):
        """Test Google URL is invalid."""
        assert is_youtube_url("https://www.google.com") is False

    def test_invalid_vimeo_url(self):
        """Test Vimeo URL is invalid."""
        assert is_youtube_url("https://vimeo.com/123456") is False

    def test_invalid_random_url(self):
        """Test random URL is invalid."""
        assert is_youtube_url("https://example.com/video") is False

    def test_invalid_not_url(self):
        """Test non-URL string is invalid."""
        assert is_youtube_url("not-a-url") is False

    def test_invalid_empty_string(self):
        """Test empty string is invalid."""
        assert is_youtube_url("") is False

    def test_invalid_ftp_url(self):
        """Test FTP URL is invalid."""
        assert is_youtube_url("ftp://youtube.com/video") is False

    def test_case_insensitive(self):
        """Test URL validation is case insensitive."""
        assert is_youtube_url("https://WWW.YOUTUBE.COM/watch?v=dQw4w9WgXcQ") is True


class TestExtractMediaUrl:
    """Tests for extract_media_url function."""

    @pytest.fixture
    def temp_storage_path(self):
        """Create a temporary directory for downloads."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.mark.asyncio
    async def test_extract_media_url_returns_tuple(self, temp_storage_path: str, sample_url: str):
        """Test that extract_media_url returns a tuple of (file_path, file_name)."""
        with patch("app.services.yt_dlp_service.yt_dlp.YoutubeDL") as mock_yt:
            # Mock the YoutubeDL context manager
            mock_instance = MagicMock()
            mock_yt.return_value.__enter__ = MagicMock(return_value=mock_instance)
            mock_yt.return_value.__exit__ = MagicMock(return_value=False)

            # Mock extract_info to return valid data
            mock_instance.extract_info.return_value = {
                "title": "Test Video",
                "ext": "mp4",
            }

            result = await extract_media_url(sample_url, temp_storage_path)

            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], str)  # file_path
            assert isinstance(result[1], str)  # file_name

    @pytest.mark.asyncio
    async def test_extract_media_url_creates_download_dir(
        self, temp_storage_path: str, sample_url: str
    ):
        """Test that extract_media_url creates the downloads directory."""
        download_dir = os.path.join(temp_storage_path, "downloads")
        assert not os.path.exists(download_dir)

        with patch("app.services.yt_dlp_service.yt_dlp.YoutubeDL") as mock_yt:
            mock_instance = MagicMock()
            mock_yt.return_value.__enter__ = MagicMock(return_value=mock_instance)
            mock_yt.return_value.__exit__ = MagicMock(return_value=False)
            mock_instance.extract_info.return_value = {"title": "Test", "ext": "mp4"}

            await extract_media_url(sample_url, temp_storage_path)

            assert os.path.exists(download_dir)

    @pytest.mark.asyncio
    async def test_extract_media_url_uses_uuid_filename(
        self, temp_storage_path: str, sample_url: str
    ):
        """Test that extract_media_url generates a UUID-based filename."""
        with patch("app.services.yt_dlp_service.yt_dlp.YoutubeDL") as mock_yt:
            mock_instance = MagicMock()
            mock_yt.return_value.__enter__ = MagicMock(return_value=mock_instance)
            mock_yt.return_value.__exit__ = MagicMock(return_value=False)
            mock_instance.extract_info.return_value = {"title": "Test", "ext": "mp4"}

            file_path, _ = await extract_media_url(sample_url, temp_storage_path)

            # file_path should contain a UUID
            file_id = os.path.basename(file_path).replace(".mp4", "")
            uuid.UUID(file_id)  # Should not raise

    @pytest.mark.asyncio
    async def test_extract_media_url_file_extension(self, temp_storage_path: str, sample_url: str):
        """Test that extract_media_url uses the correct file extension."""
        with patch("app.services.yt_dlp_service.yt_dlp.YoutubeDL") as mock_yt:
            mock_instance = MagicMock()
            mock_yt.return_value.__enter__ = MagicMock(return_value=mock_instance)
            mock_yt.return_value.__exit__ = MagicMock(return_value=False)
            mock_instance.extract_info.return_value = {"title": "Test Video", "ext": "webm"}

            file_path, file_name = await extract_media_url(sample_url, temp_storage_path)

            assert file_path.endswith(".webm")
            assert file_name.endswith(".webm")

    @pytest.mark.asyncio
    async def test_extract_media_url_fallback_extension(
        self, temp_storage_path: str, sample_url: str
    ):
        """Test that extract_media_url falls back to mp4 when no extension provided."""
        with patch("app.services.yt_dlp_service.yt_dlp.YoutubeDL") as mock_yt:
            mock_instance = MagicMock()
            mock_yt.return_value.__enter__ = MagicMock(return_value=mock_instance)
            mock_yt.return_value.__exit__ = MagicMock(return_value=False)
            mock_instance.extract_info.return_value = {"title": "Test Video", "ext": None}

            file_path, file_name = await extract_media_url(sample_url, temp_storage_path)

            assert file_path.endswith(".mp4")
            assert file_name.endswith(".mp4")

    @pytest.mark.asyncio
    async def test_extract_media_url_uses_title_for_filename(
        self, temp_storage_path: str, sample_url: str
    ):
        """Test that extract_media_url uses video title in returned filename."""
        with patch("app.services.yt_dlp_service.yt_dlp.YoutubeDL") as mock_yt:
            mock_instance = MagicMock()
            mock_yt.return_value.__enter__ = MagicMock(return_value=mock_instance)
            mock_yt.return_value.__exit__ = MagicMock(return_value=False)
            mock_instance.extract_info.return_value = {"title": "My Cool Video", "ext": "mp4"}

            _, file_name = await extract_media_url(sample_url, temp_storage_path)

            assert file_name == "My Cool Video.mp4"

    @pytest.mark.asyncio
    async def test_extract_media_url_fallback_to_uuid_when_no_title(
        self, temp_storage_path: str, sample_url: str
    ):
        """Test that UUID is used when title is not available."""
        with patch("app.services.yt_dlp_service.yt_dlp.YoutubeDL") as mock_yt:
            mock_instance = MagicMock()
            mock_yt.return_value.__enter__ = MagicMock(return_value=mock_instance)
            mock_yt.return_value.__exit__ = MagicMock(return_value=False)
            mock_instance.extract_info.return_value = {"title": None, "ext": "mp4"}

            file_path, file_name = await extract_media_url(sample_url, temp_storage_path)

            file_id = os.path.basename(file_path).replace(".mp4", "")
            uuid.UUID(file_id)  # Should use UUID
            # file_name should be UUID.mp4 since title is None
            assert file_name == f"{file_id}.mp4"

    @pytest.mark.asyncio
    async def test_extract_media_url_yt_dlp_options(self, temp_storage_path: str, sample_url: str):
        """Test that correct yt_dlp options are passed."""
        with patch("app.services.yt_dlp_service.yt_dlp.YoutubeDL") as mock_yt:
            mock_instance = MagicMock()
            mock_yt.return_value.__enter__ = MagicMock(return_value=mock_instance)
            mock_yt.return_value.__exit__ = MagicMock(return_value=False)
            mock_instance.extract_info.return_value = {"title": "Test", "ext": "mp4"}

            await extract_media_url(sample_url, temp_storage_path)

            # Verify YoutubeDL was called with correct options
            mock_yt.assert_called_once()
            call_args = mock_yt.call_args

            # call_args is (args, kwargs) - options passed as positional arg
            args, _ = call_args
            ydl_opts = args[0] if args else {}

            assert ydl_opts.get("format") == "best[ext=mp4]/best"
            assert "quiet" in ydl_opts
            assert "no_warnings" in ydl_opts
            assert "outtmpl" in ydl_opts
