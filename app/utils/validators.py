from urllib.parse import urlparse

# Exact allowed YouTube domains
_YOUTUBE_DOMAINS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
}

_YOUTUBE_SHORT_DOMAINS = {
    "youtu.be",
}

_YOUTUBE_NOCOOKIE_DOMAINS = {
    "youtube-nocookie.com",
    "www.youtube-nocookie.com",
}


def is_youtube_url(url: str) -> bool:
    """Validate if URL is a YouTube URL.

    Uses exact domain matching to prevent subdomain bypass attacks
    (e.g., youtube.com.evil.com must NOT match).
    """
    try:
        parsed = urlparse(url)
        scheme = parsed.scheme.lower()

        # Only allow http and https schemes
        if scheme not in ("http", "https"):
            return False

        netloc = parsed.netloc.lower()
        # Strip port if present (e.g., "youtube.com:443" -> "youtube.com")
        hostname = netloc.rsplit(":", 1)[0] if ":" in netloc else netloc

        # Exact domain matching — no substring checks
        if hostname in _YOUTUBE_DOMAINS:
            return True
        if hostname in _YOUTUBE_SHORT_DOMAINS:
            return True
        if hostname in _YOUTUBE_NOCOOKIE_DOMAINS:
            return True

        return False
    except (ValueError, AttributeError):
        return False
