import asyncio
import logging
import os
import uuid
from concurrent.futures import ThreadPoolExecutor

import yt_dlp

logger = logging.getLogger(__name__)


class StorageError(Exception):
    """Raised when storage operations fail."""


def _extract_sync(url: str, output_template: str) -> dict:
    """Synchronous wrapper for yt_dlp.extract_info."""
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
    }
    # Pass options as first positional argument (params)
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=True)  # type: ignore[no-any-return]


async def extract_media_url(url: str, storage_path: str) -> tuple[str, str]:
    """
    Extract media URL from a YouTube URL using yt-dlp.

    Returns:
        tuple of (file_path, file_name)

    Raises:
        StorageError: If the download directory cannot be created.
    """
    download_dir = os.path.join(storage_path, "downloads")
    try:
        os.makedirs(download_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create download directory {download_dir}: {e}")
        raise StorageError(f"Failed to create download directory: {e}") from e

    file_id = str(uuid.uuid4())
    output_template = os.path.join(download_dir, f"{file_id}.%(ext)s")

    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(
        ThreadPoolExecutor(max_workers=1), _extract_sync, url, output_template
    )

    title = info.get("title") or file_id
    ext = info.get("ext") or "mp4"
    file_name = f"{title}.{ext}"
    file_path = os.path.join(download_dir, f"{file_id}.{ext}")

    return file_path, file_name
