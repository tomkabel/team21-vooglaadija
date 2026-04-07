from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.utils.validators import is_youtube_url


class DownloadCreate(BaseModel):
    url: Annotated[str, Field(min_length=1, max_length=2000)]

    @field_validator("url")
    @classmethod
    def validate_youtube_url(cls, v: str) -> str:
        if not is_youtube_url(v):
            raise ValueError("Must be a valid YouTube URL")
        return v


class DownloadResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    url: str
    status: str
    file_name: str | None = None
    error: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    next_retry_at: datetime | None = None
    created_at: datetime
    completed_at: datetime | None = None
    expires_at: datetime | None = None


class PaginationInfo(BaseModel):
    page: int
    per_page: int
    total: int


class DownloadListResponse(BaseModel):
    downloads: list[DownloadResponse]
    pagination: PaginationInfo
