import asyncio
import atexit
import logging
import os
import re
import uuid
from concurrent.futures import ThreadPoolExecutor

import yt_dlp

logger = logging.getLogger(__name__)

# Shared thread pool for yt-dlp operations (avoids per-request leak)
_executor = ThreadPoolExecutor(max_workers=4)

# Timeout for yt-dlp operations in seconds (5 minutes)
YT_DLP_TIMEOUT = 300


def _shutdown_executor():
    """Gracefully shut down the thread pool on process exit."""
    _executor.shutdown(wait=False, cancel_futures=True)


atexit.register(_shutdown_executor)


class StorageError(Exception):
    """Raised when storage operations fail."""


def _sanitize_title(title: str) -> str:
    """Sanitize a video title for safe use as a display name (not a path)."""
    # Remove any path separators, null bytes, and dots (prevent path traversal in display name)
    sanitized = title.replace("\x00", "").replace("/", "_").replace("\\", "_").replace(".", "_")
    # Remove non-printable characters
    sanitized = re.sub(r"[^\w\s\-]", "", sanitized)
    # Collapse whitespace
    sanitized = re.sub(r"\s+", " ", sanitized).strip()
    return sanitized or "download"


def _extract_sync(url: str, output_template: str) -> dict:
    """Synchronous wrapper for yt_dlp.extract_info with timeout enforcement."""
    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 60,
        "retries": 3,
        # Prevent yt-dlp from hanging indefinitely
        "extractor_args": {"youtube": {"player_client": ["web", "ios"]}},
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:  # type: ignore[arg-type]
        return ydl.extract_info(url, download=True)  # type: ignore[no-any-return]


def _validate_path_within(base_path: str, target_path: str) -> str:
    """Validate that target_path resolves within base_path.

    Returns the resolved path if valid.
    Raises StorageError if the path escapes the base directory.
    """
    resolved_base = os.path.realpath(base_path)
    resolved_target = os.path.realpath(target_path)
    # Ensure trailing separator for prefix matching
    if not resolved_base.endswith(os.sep):
        resolved_base += os.sep
    if not resolved_target.startswith(resolved_base):
        raise StorageError(
            f"Path traversal detected: resolved path {resolved_target} "
            f"is outside allowed directory {resolved_base}"
        )
    return resolved_target


async def extract_media_url(url: str, storage_path: str) -> tuple[str, str]:
    """
    Extract media URL from a YouTube URL using yt-dlp.

    Returns:
        tuple of (file_path, file_name) where file_path is always within storage_path

    Raises:
        StorageError: If the download directory cannot be created or path is invalid.
        asyncio.TimeoutError: If the extraction takes longer than YT_DLP_TIMEOUT.
    """
    download_dir = os.path.join(storage_path, "downloads")
    try:
        os.makedirs(download_dir, exist_ok=True)
    except OSError as e:
        logger.error("Failed to create download directory %s: %s", download_dir, e)
        raise StorageError(f"Failed to create download directory: {e}") from e

    file_id = str(uuid.uuid4())
    # Use ONLY the UUID for the filesystem path — never the title
    output_template = os.path.join(download_dir, f"{file_id}.%(ext)s")

    loop = asyncio.get_running_loop()
    # Run with timeout to prevent thread pool exhaustion from hung yt-dlp calls
    info = await asyncio.wait_for(
        loop.run_in_executor(_executor, _extract_sync, url, output_template),
        timeout=YT_DLP_TIMEOUT,
    )

    title = info.get("title") or file_id
    ext = info.get("ext") or "mp4"
    # Sanitize title for display only — never used in filesystem path
    safe_title = _sanitize_title(str(title))
    file_name = f"{safe_title}.{ext}"
    file_path = os.path.join(download_dir, f"{file_id}.{ext}")

    # Validate the resolved path is within download_dir
    file_path = _validate_path_within(download_dir, file_path)

    # Verify the file was actually created
    if not os.path.isfile(file_path):
        raise StorageError(f"Expected output file not found: {file_path}")

    return file_path, file_name
