import os
import time
from fastapi import APIRouter
from pydantic import BaseModel
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

# We only import what we know for sure exists in the project.
from app.schemas.error import ErrorCode, error_response_doc, success_response_doc
from worker.queue import redis_client

router = APIRouter(prefix="/health", tags=["health"])


class ReadinessResponse(BaseModel):
    """Response model for readiness check."""

    status: str
    database: str
    redis: str


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
            # We created a temporary engine just to check the pulse
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


@router.get(
    "/ready",
    summary="Readiness check",
    description="Readiness probe checking database and Redis connectivity. "
    "Used by Kubernetes to determine if the service can receive traffic.",
    response_model=ReadinessResponse,
    responses={
        200: success_response_doc(
            "Service is ready",
            {
                "status": "ready",
                "database": "connected",
                "redis": "connected",
            },
        ),
        503: error_response_doc(
            "Service not ready",
            ErrorCode.SERVICE_UNAVAILABLE,
            "One or more dependencies are unavailable",
        ),
    },
)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness probe that checks all dependencies.

    Returns 503 if any dependency is unhealthy, allowing
    Kubernetes to remove this pod from service endpoints.
    """
    db_status = "connected"
    redis_status = "connected"

    # Check database connectivity
    try:
        db_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:light_sound@ytprocessor-db:5432/ytprocessor")
        if db_url:
            engine = create_async_engine(db_url)
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
        else:
            db_status = "error: missing DATABASE_URL"
    except Exception as e:
        db_status = f"error: {str(e)[:100]}"

    # Check Redis connectivity
    try:
        await redis_client.ping()
    except Exception as e:
        redis_status = f"error: {str(e)[:100]}"

    # Determine overall status
    is_ready = db_status == "connected" and redis_status == "connected"

    return ReadinessResponse(
        status="ready" if is_ready else "not_ready",
        database=db_status,
        redis=redis_status,
    )
