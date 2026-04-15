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
from app.schemas.error import (
    ErrorCode,
    build_error_example,
    error_response_doc,
    success_response_doc,
)
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


async def _get_user_job(db: DbSession, user_id: uuid.UUID, job_id: str) -> DownloadJob:
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
    job: DownloadJob | None = result.scalars().one_or_none()
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download job not found",
        )
    return job


@router.post(
    "",
    response_model=DownloadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create download job",
    description="Queue a new YouTube download job for the authenticated user.",
    responses={
        201: success_response_doc(
            "Download job created",
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "status": "pending",
                "file_name": None,
                "error": None,
                "created_at": "2026-04-07T12:00:00Z",
                "completed_at": None,
                "expires_at": None,
            },
        ),
        401: error_response_doc(
            "Unauthorized", ErrorCode.UNAUTHORIZED, "Could not validate credentials"
        ),
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": build_error_example(
                        ErrorCode.VALIDATION_ERROR,
                        "Request validation failed",
                        details={
                            "validation_errors": [
                                {
                                    "field": "url",
                                    "message": "Value error, Must be a valid YouTube URL",
                                    "type": "value_error",
                                },
                            ],
                        },
                    ),
                },
            },
        },
    },
)
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


@router.get(
    "",
    response_model=DownloadListResponse,
    summary="List download jobs",
    description="Return paginated download jobs belonging to the authenticated user.",
    responses={
        200: success_response_doc(
            "List of download jobs",
            {
                "downloads": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                        "status": "completed",
                        "file_name": "video.mp4",
                        "error": None,
                        "created_at": "2026-04-07T12:00:00Z",
                        "completed_at": "2026-04-07T12:01:00Z",
                        "expires_at": "2026-04-08T12:01:00Z",
                    },
                ],
                "pagination": {"page": 1, "per_page": 20, "total": 1},
            },
        ),
        401: error_response_doc(
            "Unauthorized", ErrorCode.UNAUTHORIZED, "Could not validate credentials"
        ),
        422: {
            "description": "Validation error",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/ErrorResponse"},
                    "example": build_error_example(
                        ErrorCode.VALIDATION_ERROR,
                        "Request validation failed",
                        details={
                            "validation_errors": [
                                {
                                    "field": "query.page",
                                    "message": "Input should be greater than or equal to 1",
                                    "type": "greater_than_equal",
                                },
                            ],
                        },
                    ),
                },
            },
        },
    },
)
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


@router.get(
    "/{job_id}",
    response_model=DownloadResponse,
    summary="Get download job",
    description="Return a specific download job by id if it belongs to the current user.",
    responses={
        200: success_response_doc(
            "Download job details",
            {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "status": "processing",
                "file_name": None,
                "error": None,
                "created_at": "2026-04-07T12:00:00Z",
                "completed_at": None,
                "expires_at": None,
            },
        ),
        401: error_response_doc(
            "Unauthorized", ErrorCode.UNAUTHORIZED, "Could not validate credentials"
        ),
        404: error_response_doc(
            "Download job not found",
            ErrorCode.NOT_FOUND,
            "Download job not found",
            details={"job_id": "unknown-id"},
        ),
    },
)
async def get_download(
    job_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> DownloadResponse:
    """Get a specific download job by ID."""
    job = await _get_user_job(db, current_user.id, job_id)
    return _job_to_response(job)


@router.get(
    "/{job_id}/file",
    summary="Download output file",
    description="Download the processed file for a completed, non-expired download job.",
    responses={
        200: {"description": "Binary file stream"},
        400: error_response_doc(
            "Job not completed",
            ErrorCode.VALIDATION_ERROR,
            "Job is not completed. Current status: processing",
        ),
        401: error_response_doc(
            "Unauthorized", ErrorCode.UNAUTHORIZED, "Could not validate credentials"
        ),
        403: error_response_doc(
            "Invalid file path", ErrorCode.FORBIDDEN, "Access denied: invalid file path"
        ),
        404: error_response_doc(
            "Job or file not found",
            ErrorCode.NOT_FOUND,
            "File not found",
            details={"job_id": "550e8400-e29b-41d4-a716-446655440000"},
        ),
        410: error_response_doc(
            "Download link expired", ErrorCode.VALIDATION_ERROR, "Download link has expired"
        ),
    },
)
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
    if job.expires_at:
        # SQLite compatibility workaround: SQLite can return naive datetimes even for
        # timezone-aware columns (datetime with UTC tzinfo), whereas PostgreSQL in
        # production returns proper timezone-aware datetimes. This normalization
        # ensures consistent comparison by stripping timezone info from both timestamps.
        now_utc = datetime.now(UTC)
        expires_at = job.expires_at
        # Strip timezone info if present (SQLite may return naive, PostgreSQL won't need this)
        if expires_at.tzinfo is not None:
            expires_at = expires_at.replace(tzinfo=None)
        now_naive = now_utc.replace(tzinfo=None)
        if expires_at < now_naive:
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
    job.completed_at = None

    await write_job_to_outbox(db, job.id)
    await db.commit()
    await db.refresh(job)

    return _job_to_response(job)


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete download job",
    description="Delete a download job and remove its file from storage when present.",
    responses={
        204: {"description": "Download job deleted"},
        401: error_response_doc(
            "Unauthorized", ErrorCode.UNAUTHORIZED, "Could not validate credentials"
        ),
        404: error_response_doc(
            "Download job not found",
            ErrorCode.NOT_FOUND,
            "Download job not found",
            details={"job_id": "unknown-id"},
        ),
    },
)
async def delete_download(
    job_id: str,
    current_user: CurrentUser,
    db: DbSession,
) -> None:
    """Delete a download job and its associated file."""
    job = await _get_user_job(db, current_user.id, job_id)

    # Validate and remove file first, before DB commit
    if job.file_path:
        try:
            safe_path = _validate_file_path(job.file_path)
            if os.path.isfile(safe_path):
                os.remove(safe_path)
                logger.info("Deleted file: %s", safe_path)
        except HTTPException:
            raise
        except OSError as e:
            # File deletion failed - do not commit DB deletion so cleanup_expired_jobs can retry
            logger.warning("Failed to delete file %s: %s", job.file_path, e)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete file from disk",
            ) from e

    # Only delete DB record after successful file deletion
    await db.delete(job)
    await db.commit()
