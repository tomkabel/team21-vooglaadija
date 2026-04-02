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

        hostname = parsed.hostname
        if hostname is None:
            return False
        hostname = hostname.lower()

        # Exact domain matching — no substring checks
        return hostname in (_YOUTUBE_DOMAINS | _YOUTUBE_SHORT_DOMAINS | _YOUTUBE_NOCOOKIE_DOMAINS)
    except (ValueError, AttributeError):
        return False
