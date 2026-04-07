"""Prometheus metrics endpoint."""

from fastapi import APIRouter, Depends, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.dependencies import get_current_user
from app.models.user import User

router = APIRouter(tags=["metrics"])


@router.get("/metrics")
async def metrics(user: User = Depends(get_current_user)) -> Response:
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
