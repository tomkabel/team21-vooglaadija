import os
import uuid


async def extract_media_url(url: str, storage_path: str) -> tuple[str, str]:
    """
    Extract media URL from a YouTube URL using yt-dlp.
    
    Returns:
        tuple of (file_path, file_name)
    """
    import yt_dlp
    
    download_dir = os.path.join(storage_path, "downloads")
    os.makedirs(download_dir, exist_ok=True)
    
    file_id = str(uuid.uuid4())
    output_template = os.path.join(download_dir, f"{file_id}.%(ext)s")
    
    ydl_opts = {
        "format": "best[ext=mp4]/best",
        "outtmpl": output_template,
        "quiet": True,
        "no_warnings": True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        file_name = info.get("title", file_id) + "." + (info.get("ext") or "mp4")
    
    file_path = os.path.join(download_dir, f"{file_id}.{info.get('ext', 'mp4')}")
    
    return file_path, file_name
