from typing import Any, Union

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.database import get_async_session_factory
from app.schemas.error import ErrorCode, error_response_doc, success_response_doc
from worker.queue import redis_client

router = APIRouter(prefix="/health", tags=["health"])


class ReadinessStatus(BaseModel):
    """Detailed readiness response with component status."""

    status: str
    database: str
    redis: str


@router.get(
    "",
    summary="Health check",
    description="Simple liveness endpoint used by orchestrators and monitoring.",
    responses={
        200: success_response_doc("Service is healthy", {"status": "ok"}),
        500: error_response_doc(
            "Unexpected server error", ErrorCode.INTERNAL_ERROR, "An internal error occurred"
        ),
    },
)
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@router.get(
    "/ready",
    summary="Readiness check",
    description="Readiness probe checking database and Redis connectivity. "
    "Used by Kubernetes to determine if the service can receive traffic.",
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
async def readiness_check() -> Union[JSONResponse, dict[str, Any]]:
    """
    Readiness probe that checks all dependencies.

    Returns 503 if any dependency is unhealthy, allowing
    Kubernetes to remove this pod from service endpoints.
    """
    db_status = "connected"
    redis_status = "connected"
    errors: list[str] = []

    # Check database connectivity
    try:
        session_factory = get_async_session_factory()
        async with session_factory() as db:
            from sqlalchemy import text

            await db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"error: {str(e)[:100]}"
        errors.append(f"database: {db_status}")

    # Check Redis connectivity
    try:
        await redis_client.ping()
    except Exception as e:
        redis_status = f"error: {str(e)[:100]}"
        errors.append(f"redis: {redis_status}")

    # Determine overall status
    is_ready = db_status == "connected" and redis_status == "connected"

    response_data: dict[str, Any] = {
        "status": "ready" if is_ready else "not_ready",
        "database": db_status,
        "redis": redis_status,
    }

    if not is_ready:
        response_data["error"] = {
            "code": ErrorCode.SERVICE_UNAVAILABLE.value,
            "message": f"Dependencies unavailable: {', '.join(errors)}",
        }
        return JSONResponse(status_code=503, content=response_data)

    return response_data
