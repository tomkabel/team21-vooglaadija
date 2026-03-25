import os
import uuid
from datetime import datetime, timedelta

import redis
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, sessionmaker

from app.config import settings
from app.models.download_job import DownloadJob
from app.services.yt_dlp_service import extract_media_url

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

redis_client = redis.from_url(settings.redis_url, decode_responses=True)


async def process_next_job() -> None:
    """Process the next job in the queue."""
    job_id = redis_client.rpop("download_queue")
    if not job_id:
        return
    
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(DownloadJob).where(DownloadJob.id == job_id)
        )
        job = result.scalar_one_or_none()
        
        if not job:
            return
        
        job.status = "processing"
        await db.commit()
        
        try:
            file_path, file_name = await extract_media_url(job.url, settings.storage_path)
            
            await db.execute(
                update(DownloadJob)
                .where(DownloadJob.id == job_id)
                .values(
                    status="completed",
                    file_path=file_path,
                    file_name=file_name,
                    completed_at=datetime.utcnow(),
                    expires_at=datetime.utcnow() + timedelta(hours=settings.file_expire_hours),
                )
            )
        except Exception as e:
            await db.execute(
                update(DownloadJob)
                .where(DownloadJob.id == job_id)
                .values(
                    status="failed",
                    error=str(e),
                    completed_at=datetime.utcnow(),
                )
            )
        
        await db.commit()
