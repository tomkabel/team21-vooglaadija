"""Download job CRUD endpoints."""

import logging
import os
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select

from app.api.dependencies import CurrentUser, DbSession
from app.api.rate_limit_config import limiter
from app.config import settings
from app.models.download_job import DownloadJob
from app.schemas.download import (
    DownloadCreate,
    DownloadListResponse,
    DownloadResponse,
    PaginationInfo,
)
from app.services.outbox_service import write_job_to_outbox

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/downloads", tags=["downloads"])


def _get_downloads_dir() -> str:
    """Get the resolved downloads directory path."""
    return os.path.realpath(os.path.join(settings.storage_path, "downloads"))


def _validate_file_path(file_path: str) -> str:
    """Validate that file_path resolves within the downloads directory.

    Returns the resolved path if valid.
    Raises HTTPException(403) if path is outside the allowed directory.
    """
    resolved = os.path.realpath(file_path)
    # Ensure trailing separator for prefix matching
    safe_dir = _get_downloads_dir()
    if not safe_dir.endswith(os.sep):
        safe_dir += os.sep
    if not resolved.startswith(safe_dir):
        logger.warning("Path traversal attempt blocked: %s", file_path)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: invalid file path",
        )
    return resolved


def _job_to_response(job: DownloadJob) -> DownloadResponse:
    """Convert a DownloadJob ORM model to a DownloadResponse schema.

    Uses Pydantic's model_validate to avoid manual field mapping.
    """
    return DownloadResponse.model_validate(job)


async def _get_user_job(db, user_id, job_id) -> DownloadJob:
    """Fetch a download job belonging to the specified user.

    Raises HTTPException(404) if not found.
    """
    # Validate job_id is a valid UUID
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format",
        ) from None

    result = await db.execute(
        select(DownloadJob).where(
            DownloadJob.id == job_uuid,
            DownloadJob.user_id == user_id,
        )
    )
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download job not found",
        )
    return job


@router.post("", response_model=DownloadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_download(
    request: Request,
    data: DownloadCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> DownloadResponse:
    """Create a new download job for the authenticated user."""
    job_id = uuid.uuid4()

    job = DownloadJob(
        id=job_id,
        user_id=current_user.id,
        url=data.url,
        status="pending",
    )

    db.add(job)
    await write_job_to_outbox(db, job_id)
    await db.commit()
    await db.refresh(job)

    return _job_to_response(job)


@router.get("", response_model=DownloadListResponse)
async def list_downloads(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> DownloadListResponse:
    """List all download jobs for the authenticated user with pagination."""

    # Get total count
    count_result = await db.execute(
        select(func.count()).where(DownloadJob.user_id == current_user.id)
    )
    total = count_result.scalar_one()

    # Get paginated results
    result = await db.execute(
        select(DownloadJob)
        .where(DownloadJob.user_id == current_user.id)
        .order_by(DownloadJob.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    jobs = result.scalars().all()

    return DownloadListResponse(
        downloads=[_job_to_response(job) for job in jobs],
        pagination=PaginationInfo(
            page=page,
            per_page=per_page,
            total=total,
        ),
    )


@router.get("/{job_id}", response_model=DownloadResponse)
async def get_download(
    job_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> DownloadResponse:
    """Get a specific download job by ID."""
    job = await _get_user_job(db, current_user.id, job_id)
    return _job_to_response(job)


@router.get("/{job_id}/file")
async def get_download_file(
    job_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> FileResponse:
    """Download the file for a completed job."""
    job = await _get_user_job(db, current_user.id, job_id)

    if job.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed. Current status: {job.status}",
        )

    if not job.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    # Check if download has expired
    if job.expires_at and job.expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Download link has expired",
        )

    # Validate path is within storage directory (prevents path traversal)
    safe_path = _validate_file_path(job.file_path)

    # Check file exists on disk
    if not os.path.isfile(safe_path):
        safe_job_id = str(job_id).replace("\r", "").replace("\n", "")
        logger.error("File missing from disk for job %s: %s", safe_job_id, safe_path)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk",
        )

    return FileResponse(
        path=safe_path,
        filename=job.file_name,
        media_type="application/octet-stream",
    )


@router.post("/{job_id}/retry", response_model=DownloadResponse)
@limiter.limit("10/minute")
async def retry_download(
    request: Request,
    job_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> DownloadResponse:
    """Retry a failed download job."""
    job = await _get_user_job(db, current_user.id, job_id)

    if job.status != "failed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only failed jobs can be retried",
        )

    job.status = "pending"
    job.retry_count = 0
    job.next_retry_at = None
    job.error = None

    await write_job_to_outbox(db, job.id)
    await db.commit()
    await db.refresh(job)

    return _job_to_response(job)


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_download(
    job_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete a download job and its associated file."""
    job = await _get_user_job(db, current_user.id, job_id)

    # Delete DB record first (source of truth), then clean up file
    await db.delete(job)
    await db.commit()

    if job.file_path:
        try:
            # Validate path before deletion
            safe_path = _validate_file_path(job.file_path)
            if os.path.isfile(safe_path):
                os.remove(safe_path)
                logger.info("Deleted file: %s", safe_path)
        except HTTPException:
            raise
        except OSError as e:
            # File deletion failure is non-fatal — DB record is already gone
            logger.warning("Failed to delete file %s: %s", job.file_path, e)
