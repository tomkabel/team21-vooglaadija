from urllib.parse import urlparse


def is_youtube_url(url: str) -> bool:
    """Validate if URL is a YouTube URL."""
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()

        # Only allow http and https schemes
        if scheme not in ("http", "https"):
            return False

        netloc = parsed.netloc.lower()

        # Check for youtube.com domains (with dot) - youtube.com, www.youtube.com, m.youtube.com
        # or youtube-nocookie.com domains (with hyphen) - youtube-nocookie.com, www.youtube-nocookie.com
        # or youtu.be short URLs
        if "youtube.com" in netloc or "youtube-nocookie.com" in netloc or "youtu.be" in netloc:
            return True

        return False
    except (ValueError, AttributeError):
        return False
