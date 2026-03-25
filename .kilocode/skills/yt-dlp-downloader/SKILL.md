---
name: yt-dlp-downloader
description: Download YouTube videos and extract media using yt-dlp. Use when processing YouTube URLs, extracting audio, downloading videos, or working with media URLs from video platforms.
version: 1.0.0
---

# YouTube Downloader Skill

This skill provides guidance for working with yt-dlp for media extraction in the project.

## Project Context

This project uses yt-dlp in `app/services/yt_dlp_service.py` for processing YouTube URLs. The worker process handles media downloads asynchronously.

## Usage Patterns

### Audio Extraction
```bash
yt-dlp --extract-audio --audio-format mp3 --output "%(title)s.%(ext)s" <url>
```

### Video Download
```bash
yt-dlp --format best --output "%(title)s.%(ext)s" <url>
```

### Specific Quality
```bash
yt-dlp --format "bestvideo[height<=1080]+bestaudio/best[height<=1080]" <url>
```

## Integration in Worker

The worker processes downloads in `worker/processor.py`:
- Job status stored in PostgreSQL
- File stored in `storage/downloads/`
- Temporary files in `storage/temp/`

## Error Handling

- **Rate Limiting**: Use `--sleep-interval 5` between downloads
- **Unavailable Videos**: Log error, update job status to 'failed'
- **Invalid URLs**: Validate URL format before processing
- **Disk Space**: Check available space before large downloads

## Best Practices

1. Always use `--no-playlist` unless playlist extraction is intended
2. Set appropriate timeouts: `--socket-timeout 30`
3. Use `--no-warnings` in production to reduce log noise
4. Implement retry logic with exponential backoff
5. Clean up temporary files after processing

## Security Considerations

- Validate URL input on the API layer
- Sanitize filename output to prevent path traversal
- Limit file size to prevent disk exhaustion
- Scan downloads for malware if hosting content
