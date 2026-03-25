import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import CurrentUser, DbSession
from app.models.download_job import DownloadJob
from app.schemas.download import DownloadCreate, DownloadListResponse, DownloadResponse
from worker.queue import enqueue_job

router = APIRouter(prefix="/downloads", tags=["downloads"])


@router.post("", response_model=DownloadResponse, status_code=status.HTTP_201_CREATED)
async def create_download(
    data: DownloadCreate,
    db: Annotated[AsyncSession, Depends(DbSession)],
    current_user: Annotated[CurrentUser, Depends()],
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
    
    enqueue_job(job_id)
    
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
    db: Annotated[AsyncSession, Depends(DbSession)],
    current_user: Annotated[CurrentUser, Depends()],
) -> DownloadListResponse:
    """List all download jobs for the authenticated user."""
    result = await db.execute(
        select(DownloadJob)
        .where(DownloadJob.user_id == str(current_user.id))
        .order_by(DownloadJob.created_at.desc())
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
        ]
    )


@router.get("/{job_id}", response_model=DownloadResponse)
async def get_download(
    job_id: str,
    db: Annotated[AsyncSession, Depends(DbSession)],
    current_user: Annotated[CurrentUser, Depends()],
) -> DownloadResponse:
    """Get a specific download job by ID."""
    result = await db.execute(
        select(DownloadJob).where(
            DownloadJob.id == job_id,
            DownloadJob.user_id == str(current_user.id),
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download job not found",
        )
    
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
    db: Annotated[AsyncSession, Depends(DbSession)],
    current_user: Annotated[CurrentUser, Depends()],
):
    """Download the file for a completed job."""
    result = await db.execute(
        select(DownloadJob).where(
            DownloadJob.id == job_id,
            DownloadJob.user_id == str(current_user.id),
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download job not found",
        )
    
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
    
    from fastapi.responses import FileResponse
    return FileResponse(
        path=job.file_path,
        filename=job.file_name,
        media_type="application/octet-stream",
    )


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_download(
    job_id: str,
    db: Annotated[AsyncSession, Depends(DbSession)],
    current_user: Annotated[CurrentUser, Depends()],
) -> None:
    """Delete a download job and its associated file."""
    result = await db.execute(
        select(DownloadJob).where(
            DownloadJob.id == job_id,
            DownloadJob.user_id == str(current_user.id),
        )
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Download job not found",
        )
    
    if job.file_path:
        import os
        try:
            os.remove(job.file_path)
        except OSError:
            pass
    
    await db.delete(job)
    await db.commit()
