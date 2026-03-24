from app.services.yt_dlp_service import extract_media_url


def test_extract_media_url_placeholder(sample_url: str) -> None:
    assert extract_media_url(sample_url) == sample_url
