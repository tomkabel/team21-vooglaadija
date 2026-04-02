"""Tests for YouTube URL validation with subdomain bypass prevention."""

from app.utils.validators import is_youtube_url


class TestIsYouTubeUrl:
    """Test the is_youtube_url validator."""

    def test_valid_youtube_urls(self):
        valid = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtube.com/watch?v=dQw4w9WgXcQ",
            "https://m.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://music.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/shorts/dQw4w9WgXcQ",
            "https://youtube-nocookie.com/watch?v=dQw4w9WgXcQ",
            "https://www.youtube-nocookie.com/watch?v=dQw4w9WgXcQ",
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
        ]
        for url in valid:
            assert is_youtube_url(url), f"Expected valid: {url}"

    def test_subdomain_bypass_rejected(self):
        """Critical security test: subdomain bypass must be rejected."""
        bypassed = [
            "https://youtube.com.evil.com/watch?v=abc",
            "https://notyoutube.com/watch?v=abc",
            "https://fakeyoutube.com/watch?v=abc",
            "https://youtube.com.attacker.net/watch?v=abc",
            "https://evil-youtube.com/watch?v=abc",
        ]
        for url in bypassed:
            assert not is_youtube_url(url), f"Should reject bypass: {url}"

    def test_invalid_schemes(self):
        invalid = [
            "ftp://youtube.com/watch?v=abc",
            "file://youtube.com/watch?v=abc",
            "javascript:alert(1)",
        ]
        for url in invalid:
            assert not is_youtube_url(url), f"Should reject scheme: {url}"

    def test_non_youtube_domains(self):
        invalid = [
            "https://www.google.com",
            "https://vimeo.com/123456",
            "https://dailymotion.com/video/abc",
        ]
        for url in invalid:
            assert not is_youtube_url(url), f"Should reject domain: {url}"

    def test_invalid_input(self):
        assert not is_youtube_url("")
        assert not is_youtube_url("not-a-url")
        assert not is_youtube_url("youtube.com")  # no scheme

    def test_case_insensitive(self):
        assert is_youtube_url("https://WWW.YOUTUBE.COM/watch?v=abc")
        assert is_youtube_url("HTTPS://YOUTU.BE/abc")

    def test_with_port(self):
        assert is_youtube_url("https://youtube.com:443/watch?v=abc")
        assert not is_youtube_url("https://youtube.com.evil.com:443/watch?v=abc")
