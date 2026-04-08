import asyncio
import json
import logging
import os
import re
import signal
import sys
import uuid
from typing import Any

logger = logging.getLogger(__name__)

# Timeout for yt-dlp operations in seconds (5 minutes)
YT_DLP_TIMEOUT = 300


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


async def _extract_via_subprocess(url: str, output_template: str) -> dict:
    """
    Extract media info via subprocess that can be forcibly killed on timeout.

    This runs yt-dlp as a separate OS process so that on TimeoutError,
    process.kill() can terminate it immediately rather than leaving a thread running.
    """
    # Create a temporary Python script that runs yt-dlp extraction
    # We write it to a temp file to avoid command-line quoting issues with the URL
    extract_script = f"""
import sys
import json
import yt_dlp

url = {json.dumps(url)}
output_template = {json.dumps(output_template)}

ydl_opts = {{
    "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
    "outtmpl": output_template,
    "quiet": True,
    "no_warnings": True,
    "socket_timeout": 60,
    "retries": 3,
    "extractor_args": {{"youtube": {{"player_client": ["web", "ios"]}}}},
}}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        sanitized_info = ydl.sanitize_info(info)
        print(json.dumps(sanitized_info))
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
    sys.exit(1)
"""
    process = None
    try:
        # Use asyncio.create_subprocess_exec to run the extraction
        # start_new_session=True so killpg kills all descendants (e.g., ffmpeg)
        process = await asyncio.create_subprocess_exec(
            sys.executable,
            "-c",
            extract_script,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            start_new_session=True,
        )

        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=YT_DLP_TIMEOUT)
        except TimeoutError as e:
            # Kill the entire process group to ensure all descendants (e.g., ffmpeg) are terminated
            try:
                os.killpg(process.pid, signal.SIGTERM)
                await process.wait()
            except ProcessLookupError:
                pass  # Process already terminated
            raise TimeoutError(f"yt-dlp extraction timed out after {YT_DLP_TIMEOUT}s") from e

        if process.returncode != 0:
            # Try to parse stdout first for extractor error payloads
            try:
                error_result: dict[str, Any] = json.loads(stdout.decode())
                if "error" in error_result:
                    raise RuntimeError(f"yt-dlp extraction failed: {error_result['error']}")
            except (json.JSONDecodeError, UnicodeDecodeError):
                pass
            # Fall back to stderr if stdout is empty or unparseable
            error_msg = stderr.decode() if stderr else "Unknown error"
            raise RuntimeError(f"yt-dlp failed: {error_msg}")

        success_result: dict[str, Any] = json.loads(stdout.decode())
        return success_result

    finally:
        # Ensure process is fully cleaned up using process group kill
        if process and process.returncode is None:
            try:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
                await process.wait()
            except (ProcessLookupError, OSError):
                pass  # Process already terminated


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

    # Run via subprocess so it can be killed on timeout
    info = await _extract_via_subprocess(url, output_template)

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
