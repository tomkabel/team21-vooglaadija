import logging
import os
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select

from app.api.dependencies import CurrentUser, DbSession
from app.config import settings
from app.models.download_job import DownloadJob
from app.schemas.download import (
    DownloadCreate,
    DownloadListResponse,
    DownloadResponse,
    PaginationInfo,
)
from worker.queue import enqueue_job

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/downloads", tags=["downloads"])

# Resolved path to the storage downloads directory
_DOWNLOADS_DIR = os.path.realpath(os.path.join(settings.storage_path, "downloads"))


def _validate_file_path(file_path: str) -> str:
    """Validate that file_path resolves within the downloads directory.

    Returns the resolved path if valid.
    Raises HTTPException(403) if path is outside the allowed directory.
    """
    resolved = os.path.realpath(file_path)
    # Ensure trailing separator for prefix matching
    safe_dir = _DOWNLOADS_DIR
    if not safe_dir.endswith(os.sep):
        safe_dir += os.sep
    if not resolved.startswith(safe_dir):
        logger.warning(f"Path traversal attempt blocked: {file_path}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: invalid file path",
        )
    return resolved


async def _get_user_job(db, user_id: str, job_id: str) -> DownloadJob:
    """Fetch a download job belonging to the specified user.

    Raises HTTPException(404) if not found.
    """
    result = await db.execute(
        select(DownloadJob).where(
            DownloadJob.id == job_id,
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
async def create_download(
    data: DownloadCreate,
    current_user: CurrentUser,
    db: DbSession,
) -> DownloadResponse:
    """Create a new download job for the authenticated user."""
    job_id = str(uuid.uuid4())

    job = DownloadJob(
        id=job_id,
        user_id=str(current_user.id),
        url=data.url,
        status="pending",
    )

    db.add(job)
    await db.commit()
    await db.refresh(job)

    await enqueue_job(job_id)

    return DownloadResponse(
        id=job.id,
        url=job.url,
        status=job.status,
        file_name=job.file_name,
        error=job.error,
        created_at=job.created_at,
        completed_at=job.completed_at,
        expires_at=job.expires_at,
    )


@router.get("", response_model=DownloadListResponse)
async def list_downloads(
    current_user: CurrentUser,
    db: DbSession,
    page: int = Query(default=1, ge=1, description="Page number"),
    per_page: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> DownloadListResponse:
    """List all download jobs for the authenticated user with pagination."""
    user_id = str(current_user.id)

    # Get total count
    count_result = await db.execute(select(func.count()).where(DownloadJob.user_id == user_id))
    total = count_result.scalar_one()

    # Get paginated results
    result = await db.execute(
        select(DownloadJob)
        .where(DownloadJob.user_id == user_id)
        .order_by(DownloadJob.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    jobs = result.scalars().all()

    return DownloadListResponse(
        downloads=[
            DownloadResponse(
                id=job.id,
                url=job.url,
                status=job.status,
                file_name=job.file_name,
                error=job.error,
                created_at=job.created_at,
                completed_at=job.completed_at,
                expires_at=job.expires_at,
            )
            for job in jobs
        ],
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
    job = await _get_user_job(db, str(current_user.id), job_id)

    return DownloadResponse(
        id=job.id,
        url=job.url,
        status=job.status,
        file_name=job.file_name,
        error=job.error,
        created_at=job.created_at,
        completed_at=job.completed_at,
        expires_at=job.expires_at,
    )


@router.get("/{job_id}/file")
async def get_download_file(
    job_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> FileResponse:
    """Download the file for a completed job."""
    job = await _get_user_job(db, str(current_user.id), job_id)

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
        logger.error(f"File missing from disk for job {job_id}: {safe_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk",
        )

    return FileResponse(
        path=safe_path,
        filename=job.file_name,
        media_type="application/octet-stream",
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_download(
    job_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete a download job and its associated file."""
    job = await _get_user_job(db, str(current_user.id), job_id)

    # Delete DB record first (source of truth), then clean up file
    await db.delete(job)
    await db.commit()

    if job.file_path:
        try:
            # Validate path before deletion
            safe_path = _validate_file_path(job.file_path)
            if os.path.isfile(safe_path):
                os.remove(safe_path)
                logger.info(f"Deleted file: {safe_path}")
        except HTTPException:
            raise
        except OSError as e:
            # File deletion failure is non-fatal — DB record is already gone
            logger.warning(f"Failed to delete file {job.file_path}: {e}")
