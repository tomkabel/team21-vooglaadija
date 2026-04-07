import logging
import os
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select, update

from app.api.dependencies import CurrentUser, DbSession
from app.config import settings
from app.models.download_job import DownloadJob
from app.schemas.error import ErrorCode, build_error_example, error_response_doc, success_response_doc
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
        ),
    )
    job: DownloadJob | None = result.scalar_one_or_none()
    if not job:
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
        401: error_response_doc("Unauthorized", ErrorCode.UNAUTHORIZED, "Could not validate credentials"),
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

    # Re-fetch to get server-generated fields
    result = await db.execute(select(DownloadJob).where(DownloadJob.id == job.id))
    job = result.scalar_one()

    try:
        await enqueue_job(job_id)
    except Exception:
        logger.error(f"Failed to enqueue job {job_id}, marking as enqueue_failed")
        await db.execute(
            update(DownloadJob)
            .where(DownloadJob.id == job_id)
            .values(status="enqueue_failed", error="Failed to enqueue job"),
        )
        await db.commit()
        # Re-fetch after status update
        result = await db.execute(select(DownloadJob).where(DownloadJob.id == job.id))
        job = result.scalar_one()

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
        401: error_response_doc("Unauthorized", ErrorCode.UNAUTHORIZED, "Could not validate credentials"),
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
        .limit(per_page),
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
        401: error_response_doc("Unauthorized", ErrorCode.UNAUTHORIZED, "Could not validate credentials"),
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
        401: error_response_doc("Unauthorized", ErrorCode.UNAUTHORIZED, "Could not validate credentials"),
        403: error_response_doc("Invalid file path", ErrorCode.FORBIDDEN, "Access denied: invalid file path"),
        404: error_response_doc(
            "Job or file not found",
            ErrorCode.NOT_FOUND,
            "File not found",
            details={"job_id": "550e8400-e29b-41d4-a716-446655440000"},
        ),
        410: error_response_doc("Download link expired", ErrorCode.VALIDATION_ERROR, "Download link has expired"),
    },
)
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
    now = datetime.now(UTC)
    expires_at = job.expires_at
    if expires_at:
        if expires_at.tzinfo is None:  # type: ignore[attr-defined]
            expires_at = expires_at.replace(tzinfo=UTC)  # type: ignore[attr-defined]
        if expires_at <= now:  # type: ignore[operator]
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Download link has expired",
            )

    # Validate path is within storage directory (prevents path traversal)
    safe_path = _validate_file_path(job.file_path)

    # Check file exists on disk
    if not os.path.isfile(safe_path):
        # Sanitize user-controlled job_id before logging to prevent log injection
        safe_job_id = job_id.replace("\r", "").replace("\n", "")
        logger.error(f"File missing from disk for job {safe_job_id}: {safe_path}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk",
        )

    return FileResponse(
        path=safe_path,
        filename=job.file_name,
        media_type="application/octet-stream",
    )


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete download job",
    description="Delete a download job and remove its file from storage when present.",
    responses={
        204: {"description": "Download job deleted"},
        401: error_response_doc("Unauthorized", ErrorCode.UNAUTHORIZED, "Could not validate credentials"),
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
    job = await _get_user_job(db, str(current_user.id), job_id)

    # Validate and clean up file before DB deletion
    if job.file_path:
        try:
            safe_path = _validate_file_path(job.file_path)
            if os.path.isfile(safe_path):
                os.remove(safe_path)
                logger.info(f"Deleted file: {safe_path}")
        except HTTPException:
            # Path validation failed — log and proceed with DB cleanup
            safe_job_id = job_id.replace("\r", "").replace("\n", "")
            logger.warning(f"Invalid file path for job {safe_job_id}: {job.file_path}")
        except OSError as e:
            logger.warning(f"Failed to delete file {job.file_path}: {e}")

    # Delete DB record (source of truth)
    await db.delete(job)
    await db.commit()
