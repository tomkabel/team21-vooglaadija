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


async def _kill_process_group(process: asyncio.subprocess.Process) -> None:
    """Kill a process group and wait for it to terminate."""
    try:
        os.killpg(process.pid, signal.SIGKILL)
        try:
            await asyncio.wait_for(process.wait(), timeout=5)
        except TimeoutError:
            # Process is stuck, but we've already sent SIGKILL, so just continue
            pass
    except (ProcessLookupError, OSError):
        pass  # Process already terminated


def _extract_error_message(error_msg: str, fallback: str) -> str:
    """Extract the most relevant error line from error output."""
    for error_line in error_msg.split("\n"):
        stripped = error_line.strip()
        if "ERROR" in stripped or "error" in stripped.lower()[:50]:
            return stripped
    return fallback if fallback else error_msg


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
    # Format: best video + best audio, merge if needed
    # Handles videos that are video-only or audio-only
    "format": "bestvideo*+bestaudio*/best",
    "outtmpl": output_template,
    "quiet": True,
    "no_warnings": True,
    "socket_timeout": 60,
    "retries": 3,
    # Merge formats when video-only and audio-only streams need combining
    "merge_formats": "prefer_merge",
    # Use youtube client that supports more formats
    "extractor_args": {{
        "youtube": {{
            "player_client": ["web", "default", "tv"],
        }},
    }},
}}

try:
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        if info is None:
            print(json.dumps({{"error": "No video info returned"}}))
            sys.exit(1)
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
                try:
                    await asyncio.wait_for(process.wait(), timeout=5)
                except TimeoutError:
                    # Escalate to SIGKILL if SIGTERM didn't work within 5 seconds
                    await _kill_process_group(process)
            except (ProcessLookupError, OSError):
                pass  # Process already terminated
            raise TimeoutError(f"yt-dlp extraction timed out after {YT_DLP_TIMEOUT}s") from e

        # Parse yt-dlp output - may have extra text before JSON
        output = stdout.decode().strip()

        # Find JSON in output (yt-dlp may output progress text before JSON)
        json_start = output.find("{")
        if json_start >= 0:
            json_str = output[json_start:]
            try:
                result: dict[str, Any] = json.loads(json_str)
                # Check for error in the result
                if "error" in result:
                    raise RuntimeError(f"yt-dlp extraction failed: {result['error']}")
                return result
            except json.JSONDecodeError:
                # JSON parse failed, fall through to error handling
                pass

        # If we get here with non-zero return code, or JSON parsing failed
        if process.returncode != 0:
            error_msg = stderr.decode().strip() if stderr else "Unknown error"
            error_msg = _extract_error_message(error_msg, output if output else "")
            if not error_msg:
                error_msg = "Unknown error"
            raise RuntimeError(f"yt-dlp failed: {error_msg}")

        # Should not reach here - either returned result or raised error
        raise RuntimeError("yt-dlp extraction completed but produced no usable output")

    finally:
        # Ensure process is fully cleaned up using process group kill
        # process.pid is the group ID since start_new_session=True
        if process and process.returncode is None:
            await _kill_process_group(process)


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
