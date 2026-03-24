from urllib.parse import urlparse


def is_youtube_url(url: str) -> bool:
    netloc = urlparse(url).netloc.lower()
    return "youtube.com" in netloc or "youtu.be" in netloc
