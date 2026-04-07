"""Prometheus metrics endpoint."""

from fastapi import APIRouter, Depends, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.dependencies import get_current_user

router = APIRouter(tags=["metrics"])


@router.get("/metrics", dependencies=[Depends(get_current_user)])
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )
