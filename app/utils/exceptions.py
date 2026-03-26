"""Custom exceptions for the application."""


class YTDLPError(Exception):
    """Raised when yt-dlp processing fails."""


class StorageError(Exception):
    """Raised when storage operations fail."""
