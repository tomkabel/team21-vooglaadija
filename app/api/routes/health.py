import os
import time
from fastapi import APIRouter
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Solo importamos lo que sabemos con certeza que existe en el proyecto
from app.schemas.error import ErrorCode, error_response_doc, success_response_doc

router = APIRouter(prefix="/health", tags=["health"])

@router.get(
    "",
    summary="Service Health Check",
    description="Independent endpoint to monitor database and redis connectivity.",
    responses={
        200: success_response_doc("Service is healthy", {"status": "healthy"}),
        503: error_response_doc("Service unavailable", ErrorCode.INTERNAL_ERROR, "Dependency check failed"),
    },
)
async def health_check() -> dict:
    """
    Returns the health status using independent, direct connections.
    """
    health_status = {
        "status": "healthy",
        "timestamp": time.time(),
        "dependencies": {}
    }
    
    # 1. Independent Database Check
    db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:light_sound@ytprocessor-db:5432/ytprocessor")
    if db_url:
        try:
            # Creamos un motor temporal solo para revisar el pulso
            engine = create_async_engine(db_url)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            health_status["dependencies"]["database"] = "ok"
            await engine.dispose()
        except Exception as e:
            health_status["dependencies"]["database"] = f"error: {str(e)}"
            health_status["status"] = "unhealthy"
    else:
        health_status["dependencies"]["database"] = "missing DATABASE_URL"
        health_status["status"] = "unhealthy"

    # 2. Independent Redis Check
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        try:
            redis_client = Redis.from_url(redis_url, socket_timeout=2)
            if await redis_client.ping():
                health_status["dependencies"]["redis"] = "ok"
            await redis_client.close()
        except Exception as e:
            health_status["dependencies"]["redis"] = f"error: {str(e)}"
            health_status["status"] = "unhealthy"
    else:
        health_status["dependencies"]["redis"] = "missing REDIS_URL"
        health_status["status"] = "unhealthy"

    return health_status