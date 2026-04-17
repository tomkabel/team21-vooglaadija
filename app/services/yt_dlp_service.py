import asyncio
import json
import os
import re
import signal
import sys
import uuid
from typing import Any

from app.logging_config import get_logger

logger = get_logger(__name__)

# Timeout for yt-dlp operations in seconds (5 minutes)
YT_DLP_TIMEOUT = 300

FORMAT_FALLBACK_CHAIN = [
    {"format": "bestvideo*+bestaudio/best", "S": ["res:1080", "codec:h264"]},
    {"format": "bestvideo+bestaudio/best", "S": ["res", "codec"]},
    {"format": "worstvideo*+bestaudio/best", "S": ["res:720"]},
    {"format": "best", "S": ["quality"]},
    {"format": "worst", "S": ["quality"]},
]


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
        if "ERROR" in stripped or "error" in stripped.lower():
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

    Uses a format fallback chain to handle "Requested format is not available" errors
    that occur when YouTube doesn't have the exact formats needed for merging.
    """
    url_json = json.dumps(url)
    output_template_json = json.dumps(output_template)
    fallback_chain_json = json.dumps(FORMAT_FALLBACK_CHAIN)

    extract_script = f"""
import sys
import json
import yt_dlp

url = {url_json}
output_template = {output_template_json}
fallback_chain = {fallback_chain_json}

last_error = None

for i, format_spec in enumerate(fallback_chain):
    ydl_opts = {{
        "format": format_spec["format"],
        "format_sort": format_spec.get("S", []),
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
        "socket_timeout": 60,
        "retries": 3,
        "prefer_free_formats": True,
        "check_formats": "missable",
        "extractor_args": {{
            "youtube": {{
                "player_client": ["tv", "web", "default", "mobile"],
            }},
        }},
    }}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if info is None:
                last_error = "No video info returned"
                continue
            sanitized_info = ydl.sanitize_info(info)
            print(json.dumps(sanitized_info))
            sys.exit(0)
    except Exception as e:
        err_str = str(e)
        if "Requested format" in err_str and "not available" in err_str:
            last_error = err_str
            continue
        print(json.dumps({{"error": err_str}}))
        sys.exit(1)

attempted_formats = [spec["format"] for spec in fallback_chain]
print(json.dumps({{
    "error": f"All formats failed. Last error: {{last_error}}. Attempted formats: {{attempted_formats}}"
}}))
sys.exit(1)
"""
    process = None
    try:
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
            try:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    await asyncio.wait_for(process.wait(), timeout=5)
                except TimeoutError:
                    await _kill_process_group(process)
            except (ProcessLookupError, OSError):
                pass
            raise TimeoutError(f"yt-dlp extraction timed out after {YT_DLP_TIMEOUT}s") from e

        output = stdout.decode().strip()

        # Extract JSON from last non-empty line for reliability
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        if lines:
            json_str = lines[-1]
            try:
                result: dict[str, Any] = json.loads(json_str)
                if "error" in result:
                    raise RuntimeError(f"yt-dlp extraction failed: {result['error']}")
                return result
            except json.JSONDecodeError as e:
                raise RuntimeError(f"yt-dlp produced malformed JSON: {json_str!r}") from e

        if process.returncode != 0:
            error_msg = stderr.decode().strip() if stderr else "Unknown error"
            error_msg = _extract_error_message(error_msg, output if output else "")
            if not error_msg:
                error_msg = "Unknown error"
            raise RuntimeError(f"yt-dlp failed: {error_msg}")

        raise RuntimeError("yt-dlp extraction completed but produced no usable output")

    finally:
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
        logger.error("failed_to_create_download_directory", directory=download_dir, error=str(e))
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
