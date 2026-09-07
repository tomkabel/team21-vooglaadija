import json
import logging
import time
from typing import TypedDict

from fastapi import APIRouter, Response, status
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import create_async_engine

from app.schemas.error import ErrorCode, error_response_doc, success_response_doc
from core.config import settings
from core.redis_client import get_redis_client

logger = logging.getLogger(__name__)


class HealthDependencies(TypedDict):
    database: str
    redis: str


class HealthStatus(TypedDict):
    status: str
    timestamp: float
    dependencies: HealthDependencies


router = APIRouter(prefix="/health", tags=["health"])


class ReadinessResponse(BaseModel):
    """Response model for readiness check."""

    status: str
    database: str
    redis: str


async def _check_database(database_url: str) -> str:
    if not database_url:
        return "missing DATABASE_URL"

    # PostgreSQL traffic is routed through PgBouncer in transaction-pooling
    # mode, which does not preserve server-side prepared statements across
    # pooled connections. Disable asyncpg's statement cache so this one-shot
    # engine never reuses a prepared statement that PgBouncer has recycled.
    connect_args: dict[str, object] = {}
    url = make_url(database_url)
    if url.get_backend_name() == "postgresql" and url.get_driver_name() == "asyncpg":
        connect_args = {"statement_cache_size": 0}

    engine = create_async_engine(database_url, connect_args=connect_args)
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return "ok"
    except Exception:
        logger.warning("database_health_check_failed", exc_info=True)
        return "error: unavailable"
    finally:
        await engine.dispose()


async def _check_redis(redis_url: str) -> str:
    if not redis_url:
        return "missing REDIS_URL"

    try:
        client = get_redis_client()
        if await client.ping():
            return "ok"
        return "error: unavailable"
    except Exception:
        logger.warning("redis_health_check_failed", exc_info=True)
        return "error: unavailable"


@router.get(
    "",
    summary="Service Health Check",
    description="Independent endpoint to monitor database and redis connectivity.",
    responses={
        200: success_response_doc("Service is healthy", {"status": "healthy"}),
        503: error_response_doc(
            "Service unavailable",
            ErrorCode.INTERNAL_ERROR,
            "Dependency check failed",
        ),
    },
)
async def health_check() -> HealthStatus:
    """
    Reports the health of the database and Redis dependencies.

    Returns:
        HealthStatus: A timestamped health result with dependency statuses and an
        overall status of "healthy" or "unhealthy".
    """
    health_status: HealthStatus = {
        "status": "healthy",
        "timestamp": time.time(),
        "dependencies": {"database": "unknown", "redis": "unknown"},
    }

    health_status["dependencies"]["database"] = await _check_database(settings.database_url)
    health_status["dependencies"]["redis"] = await _check_redis(settings.redis_url)

    if health_status["dependencies"]["database"] != "ok":
        health_status["status"] = "unhealthy"

    if health_status["dependencies"]["redis"] != "ok":
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
                "database": "ok",
                "redis": "ok",
            },
        ),
        503: error_response_doc(
            "Service not ready",
            ErrorCode.SERVICE_UNAVAILABLE,
            "One or more dependencies are unavailable",
        ),
    },
)
async def readiness_check() -> ReadinessResponse | Response:
    """Readiness probe that checks all dependencies.

    Returns 503 if any dependency is unhealthy, allowing
    Kubernetes to remove this pod from service endpoints.
    """
    db_status = await _check_database(settings.database_url)
    if db_status != "ok":
        logger.warning("Database readiness check failed", extra={"database_status": db_status})
        if not db_status.startswith("missing "):
            db_status = "error: unavailable"

    redis_status = await _check_redis(settings.redis_url)
    if redis_status != "ok":
        logger.warning("Redis readiness check failed", extra={"redis_status": redis_status})
        if not redis_status.startswith("missing "):
            redis_status = "error: unavailable"

    # Determine overall status
    is_ready = db_status == "ok" and redis_status == "ok"

    response_data = {
        "status": "ready" if is_ready else "not_ready",
        "database": db_status,
        "redis": redis_status,
    }

    if is_ready:
        return ReadinessResponse(**response_data)

    return Response(
        content=json.dumps(response_data),
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        media_type="application/json",
    )
