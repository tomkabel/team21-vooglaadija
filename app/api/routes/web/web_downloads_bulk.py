"""Bulk-delete web route for downloads (HTMX bulk action)."""

import json
from typing import Annotated

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from app.api.dependencies import CurrentUserFromCookie, DbSession
from app.api.rate_limit_config import limiter
from app.api.routes.web.web_helpers import logger, validate_csrf_token
from app.api.routes.web_helpers import _error_html
from app.services.download_service import DownloadService

router = APIRouter(tags=["web"])


@router.post("/downloads/bulk-delete", response_model=None)
@limiter.limit("20/minute")
async def bulk_delete_download_form(
    request: Request,
    current_user: CurrentUserFromCookie,
    db: DbSession,
    job_ids: Annotated[list[str], Form(default_factory=list)],
) -> HTMLResponse:
    """
    Delete multiple selected download jobs from an HTMX bulk action.

    Parameters:
        job_ids (list[str]): The identifiers of the download jobs to delete.

    Returns:
        HTMLResponse: An empty response that triggers client-side row removal, or an HTML error response when deletion fails.
    """
    if not await validate_csrf_token(request):
        return HTMLResponse(status_code=403, content=_error_html("Invalid CSRF token"))

    if not job_ids:
        return HTMLResponse(status_code=400, content=_error_html("No downloads selected"))

    try:
        result = await DownloadService(db, current_user.id).bulk_delete(
            job_ids,
            allowed_statuses={"completed", "failed", "cancelled"},
            fail_on_file_delete=False,
        )
    except Exception:
        logger.exception("failed_to_bulk_delete_downloads")
        return HTMLResponse(status_code=500, content=_error_html("Failed to delete downloads"))

    trigger = json.dumps(
        {
            "bulk-delete-complete": {
                "deleted": result.deleted_ids,
                "skipped": result.skipped_ids,
                "requested": result.requested,
            }
        }
    )
    resp = HTMLResponse(content="")
    resp.headers["HX-Trigger"] = trigger
    return resp
