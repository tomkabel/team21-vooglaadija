"""Prometheus metrics endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter(tags=["metrics"])


async def require_authenticated_user(
    user: User = Depends(get_current_user),
) -> User:
    """Require authenticated user for metrics access. Returns 403 if unauthorized."""
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access to metrics endpoint is forbidden",
        )
    return user


@router.get("/metrics")
async def metrics(user: User = Depends(require_authenticated_user)) -> Response:
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
