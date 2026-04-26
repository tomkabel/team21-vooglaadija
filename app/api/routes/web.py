import html
import os
import posixpath
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse

from fastapi import APIRouter, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import CurrentUserFromCookie, DbSession
from app.api.rate_limit_config import limiter
from app.auth import (
    clear_token_cookies,
    create_access_token,
    create_refresh_token,
    set_token_cookies,
)
from app.config import settings
from app.logging_config import get_logger
from app.models.download_job import DownloadJob
from app.models.outbox import Outbox
from app.models.user import User, not_deleted
from app.services.auth_service import hash_password, verify_password
from app.services.outbox_service import write_job_to_outbox
from app.utils.username import default_username_from_email as _default_username_from_email
from app.utils.validators import is_youtube_url
from worker.queue import enqueue_job

logger = get_logger(__name__)

router = APIRouter(prefix="/web", tags=["web"])

# Resolve templates relative to this file so it works regardless of CWD.
# web.py -> app/api/routes/web.py, so parent^3 = app/
_TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(_TEMPLATE_DIR))

# Allowed redirect targets — only internal paths
_ALLOWED_REDIRECT_HOSTS: tuple[str, ...] = ("/web/",)


def _validate_redirect_url(url: str | None, default: str) -> str:
    """Validate a redirect URL to prevent open redirect attacks.

    Only allows relative URLs starting with known safe prefixes.
    """
    if not url:
        return default

    # Normalize and strip whitespace / backslashes
    normalized = url.strip().replace("\\", "/")

    # Parse the URL to detect schemes and hosts robustly
    parsed = urlparse(normalized)

    # Reject any URL with a scheme or network location (host)
    if parsed.scheme or parsed.netloc:
        return default

    # Reject protocol-relative URLs like //example.com
    if normalized.startswith("//"):
        return default

    # Only allow absolute paths that start with known safe prefixes
    if not normalized.startswith("/"):
        return default

    # Normalize path to resolve . and .. components
    had_trailing_slash = normalized.endswith("/")
    normalized = posixpath.normpath(normalized)
    if had_trailing_slash and normalized != "/":
        normalized += "/"

    if any(normalized.startswith(prefix) for prefix in _ALLOWED_REDIRECT_HOSTS):
        return normalized

    return default


# ========================
# Helpers
# ========================


def get_csrf_token(request: Request) -> str:
    """Get or create CSRF token for the request."""
    token = request.cookies.get("csrf_token")
    if not token:
        token = uuid.uuid4().hex
    return token


def set_csrf_token_cookie(response: Response, token: str) -> None:
    """Set CSRF token in response cookie with security hardening.

    httponly=True prevents JavaScript access (XSS theft protection).
    secure=True ensures cookie only sent over HTTPS.
    samesite="Strict" prevents CSRF attacks via cross-site requests.
    max_age=86400 sets 24-hour expiry matching session lifetime.
    """
    response.set_cookie(
        key="csrf_token",
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="strict",
        path="/",
        max_age=86400,  # 24 hours in seconds
    )


def get_template_context(request: Request, csrf_token: str | None = None, **extra_context):
    """Get common template context including current year, CSRF token, and CSP nonce.

    Args:
        request: The FastAPI request object
        csrf_token: Optional pre-generated CSRF token. If not provided,
                    a new one will be generated via get_csrf_token(request).
                    Use this to ensure the same token is used for both
                    the cookie and the template context.
    """
    token = csrf_token if csrf_token is not None else get_csrf_token(request)
    # Get nonce from request.state (set by security headers middleware)
    nonce = getattr(request.state, "nonce", "")
    context = {
        "request": request,
        "current_year": datetime.now(UTC).year,
        "csrf_token": token,
        "nonce": nonce,
    }
    context.update(extra_context)
    return context


def is_htmx_request(request: Request) -> bool:
    """Check if request is from HTMX."""
    return request.headers.get("HX-Request") == "true"


async def validate_csrf_token(request: Request) -> bool:
    """Validate CSRF token from HTMX header or form data.

    Returns True if token is valid or if this is not a state-changing request.

    Validation strategies (in order of preference):
    1. Header token matches cookie token (standard double-submit)
    2. Form token matches cookie token (fallback for non-HTML forms)
    3. Header token matches form token (validates both are present and match,
       useful when cookie wasn't preserved but both client-side tokens are synced)
    """
    # Only validate state-changing methods
    if request.method in ("GET", "HEAD", "OPTIONS"):
        return True

    cookie_token = request.cookies.get("csrf_token")
    header_token = request.headers.get("X-CSRF-Token")

    # Strategy 1: Standard double-submit (header matches cookie)
    # This is the preferred method when cookie is preserved
    if cookie_token and header_token == cookie_token:
        return True

    # Strategy 2: Cookie present but header missing - check form data
    if cookie_token and not header_token:
        try:
            form_data = await request.form()
            form_token = form_data.get("csrf_token")
            if form_token and str(form_token) == cookie_token:
                return True
        except Exception:
            pass

    # Strategy 3: No cookie but header matches form (both client-side tokens agree)
    # This handles cases where the cookie was lost but the page tokens are still in sync
    if not cookie_token and header_token:
        try:
            form_data = await request.form()
            form_token = form_data.get("csrf_token")
            if form_token and str(form_token) == header_token:
                return True
        except Exception:
            pass

    return False


def _error_html(message: str) -> str:
    """Render a standardized error HTML fragment."""
    return (
        f"<div class='error bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded'>"
        f"{html.escape(message)}</div>"
    )


def _success_html(message: str) -> str:
    """Render a standardized success HTML fragment."""
    return (
        f"<div class='success bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded'>"
        f"{html.escape(message)}</div>"
    )


def _htmx_or_redirect(
    request: Request,
    htmx_status: int,
    htmx_content: str,
    redirect_url: str,
    redirect_status: int = 303,
) -> HTMLResponse | RedirectResponse:
    """Return HTMX response or redirect based on request type."""
    if is_htmx_request(request):
        return HTMLResponse(status_code=htmx_status, content=htmx_content)
    return RedirectResponse(url=redirect_url, status_code=redirect_status)


def _login_success_response(
    request: Request,
    access_token: str,
    refresh_token: str,
    safe_redirect: str,
    response: Response,
) -> HTMLResponse | RedirectResponse:
    """Handle successful login response for both HTMX and regular requests."""
    if is_htmx_request(request):
        resp = HTMLResponse(status_code=200, content="")
        resp.headers["HX-Redirect"] = safe_redirect
        set_token_cookies(resp, access_token, refresh_token, secure=settings.cookie_secure)
        return resp
    redirect = RedirectResponse(url=safe_redirect, status_code=303)
    set_token_cookies(redirect, access_token, refresh_token, secure=settings.cookie_secure)
    return redirect


def _register_success_response(
    request: Request,
    access_token: str,
    refresh_token: str,
) -> HTMLResponse | RedirectResponse:
    """Handle successful registration response for both HTMX and regular requests."""
    if is_htmx_request(request):
        resp = HTMLResponse(status_code=200, content="")
        resp.headers["HX-Redirect"] = "/web/downloads"
        set_token_cookies(resp, access_token, refresh_token, secure=settings.cookie_secure)
        return resp
    redirect = RedirectResponse(url="/web/downloads", status_code=303)
    set_token_cookies(redirect, access_token, refresh_token, secure=settings.cookie_secure)
    return redirect


def _validate_file_path(file_path: str) -> str:
    """Validate that file_path resolves within the downloads directory."""
    downloads_dir = os.path.realpath(os.path.join(settings.storage_path, "downloads"))
    resolved = os.path.realpath(file_path)
    safe_dir = downloads_dir if downloads_dir.endswith(os.sep) else downloads_dir + os.sep
    if not resolved.startswith(safe_dir):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: invalid file path",
        )
    return resolved


# ========================
# PUBLIC ROUTES (no auth)
# ========================


@router.get("/login")
async def login_page(request: Request, return_url: str = "/web/downloads"):
    """Render login page."""
    token = get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "login.html",
        get_template_context(request, csrf_token=token, return_url=return_url),
    )
    set_csrf_token_cookie(response, token)
    return response


@router.post("/login")
@limiter.limit("5/minute")
async def login_form(
    request: Request,
    response: Response,
    db: DbSession,
    email: Annotated[str, Form(max_length=255)],
    password: Annotated[str, Form(max_length=255)],
    return_url: Annotated[str | None, Form(max_length=500)] = None,
):
    """Handle login form submission via HTMX or regular POST."""
    # CSRF validation
    if not await validate_csrf_token(request):
        return _htmx_or_redirect(
            request, 403, _error_html("Invalid CSRF token"), "/web/login?error=csrf"
        )

    result = await db.execute(select(User).where(User.email == email, not_deleted()))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(password, user.password_hash):
        return _htmx_or_redirect(
            request, 401, _error_html("Invalid email or password"), "/web/login?error=1"
        )

    if not user.is_active:
        return _htmx_or_redirect(
            request, 401, _error_html("Account is inactive"), "/web/login?error=1"
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    safe_redirect = _validate_redirect_url(return_url, "/web/downloads")

    return _login_success_response(request, access_token, refresh_token, safe_redirect, response)


@router.get("/register")
async def register_page(request: Request):
    """Render register page."""
    token = get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "register.html",
        get_template_context(request, csrf_token=token),
    )
    set_csrf_token_cookie(response, token)
    return response


@router.post("/register")
@limiter.limit("5/minute")
async def register_form(
    request: Request,
    email: Annotated[str, Form(max_length=255)],
    password: Annotated[str, Form(max_length=255)],
    password_confirm: Annotated[str, Form(max_length=255)],
    db: DbSession,
):
    """Handle registration form submission via HTMX or regular POST."""
    if not await validate_csrf_token(request):
        return _htmx_or_redirect(
            request, 403, _error_html("Invalid CSRF token"), "/web/register?error=csrf"
        )

    if password != password_confirm:
        return _htmx_or_redirect(
            request,
            400,
            _error_html("Passwords do not match"),
            "/web/register?error=password_mismatch",
        )

    if len(password) < 8:
        return _htmx_or_redirect(
            request,
            400,
            _error_html("Password must be at least 8 characters"),
            "/web/register?error=password_too_short",
        )

    result = await db.execute(select(User).where(User.email == email, not_deleted()))
    existing = result.scalar_one_or_none()
    if existing:
        return _htmx_or_redirect(
            request,
            409,
            _error_html("Email already registered"),
            "/web/register?error=email_exists",
        )

    user = User(
        id=uuid.uuid4(),
        username=_default_username_from_email(email),
        email=email,
        password_hash=hash_password(password),
    )
    db.add(user)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return _htmx_or_redirect(
            request,
            409,
            _error_html("Email already registered"),
            "/web/register?error=email_exists",
        )

    await db.refresh(user)

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return _register_success_response(request, access_token, refresh_token)


@router.post("/logout")
async def logout(request: Request):
    """Clear auth cookies and redirect to login."""
    # CSRF validation - logout should be protected against CSRF
    if not await validate_csrf_token(request):
        return _htmx_or_redirect(
            request, 403, _error_html("Invalid CSRF token"), "/web/downloads?error=csrf"
        )
    redirect = RedirectResponse(url="/web/login?logged_out=1", status_code=303)
    clear_token_cookies(redirect)
    return redirect


@router.get("/terms")
async def terms_page(request: Request):
    """Render terms of service page with copyright disclaimers and lawful-use requirements."""
    return templates.TemplateResponse(
        request,
        "terms.html",
        get_template_context(request),
    )


# ========================
# PROTECTED ROUTES
# ========================


@router.get("/downloads")
async def dashboard_page(
    request: Request,
    current_user: CurrentUserFromCookie,
    db: DbSession,
):
    """Render main dashboard page with download list."""
    result = await db.execute(
        select(DownloadJob)
        .where(DownloadJob.user_id == current_user.id)
        .order_by(DownloadJob.created_at.desc())
        .limit(50)
    )
    jobs = result.scalars().all()

    token = get_csrf_token(request)
    response = templates.TemplateResponse(
        request,
        "dashboard.html",
        get_template_context(request, csrf_token=token, current_user=current_user, jobs=jobs),
    )
    set_csrf_token_cookie(response, token)
    return response


@router.get("/settings")
async def settings_page(
    request: Request,
    current_user: CurrentUserFromCookie,
):
    """Render settings page for the current user."""
    token = get_csrf_token(request)
    username = current_user.username or _default_username_from_email(current_user.email)
    response = templates.TemplateResponse(
        request,
        "settings.html",
        get_template_context(
            request,
            csrf_token=token,
            current_user=current_user,
            username=username,
        ),
    )
    set_csrf_token_cookie(response, token)
    return response


@router.post("/settings/username")
@limiter.limit("10/minute")
async def update_username(
    request: Request,
    username: Annotated[str, Form(max_length=64)],
    current_user: CurrentUserFromCookie,
    db: DbSession,
):
    """Update current user's username."""
    if not await validate_csrf_token(request):
        return _htmx_or_redirect(
            request, 403, _error_html("Invalid CSRF token"), "/web/settings?error=csrf"
        )

    clean_username = username.strip()
    if len(clean_username) < 3:
        return _htmx_or_redirect(
            request,
            400,
            _error_html("Username must be at least 3 characters"),
            "/web/settings?error=username_too_short",
        )

    current_user.username = clean_username
    await db.commit()

    return _htmx_or_redirect(
        request,
        200,
        _success_html("Username updated successfully"),
        "/web/settings?updated=username",
    )


@router.post("/settings/password")
@limiter.limit("10/minute")
async def change_password(
    request: Request,
    current_password: Annotated[str, Form(max_length=255)],
    new_password: Annotated[str, Form(max_length=255)],
    new_password_confirm: Annotated[str, Form(max_length=255)],
    current_user: CurrentUserFromCookie,
    db: DbSession,
):
    """Change current user's password."""
    if not await validate_csrf_token(request):
        return _htmx_or_redirect(
            request, 403, _error_html("Invalid CSRF token"), "/web/settings?error=csrf"
        )

    if not verify_password(current_password, current_user.password_hash):
        return _htmx_or_redirect(
            request,
            401,
            _error_html("Current password is incorrect"),
            "/web/settings?error=bad_password",
        )

    if new_password != new_password_confirm:
        return _htmx_or_redirect(
            request,
            400,
            _error_html("New passwords do not match"),
            "/web/settings?error=password_mismatch",
        )

    if len(new_password) < 8:
        return _htmx_or_redirect(
            request,
            400,
            _error_html("New password must be at least 8 characters"),
            "/web/settings?error=password_too_short",
        )

    current_user.password_hash = hash_password(new_password)
    await db.commit()

    return _htmx_or_redirect(
        request,
        200,
        _success_html("Password changed successfully"),
        "/web/settings?updated=password",
    )


def _cleanup_job_files(jobs: list, logger) -> tuple[bool, list[str]]:
    """Clean up files for a list of download jobs. Returns (all_cleaned, failures)."""
    file_cleanup_failures: list[str] = []
    for job in jobs:
        if not job.file_path:
            continue
        try:
            safe_path = _validate_file_path(job.file_path)
            if os.path.isfile(safe_path):
                os.remove(safe_path)
        except HTTPException:
            logger.warning(
                "Account deletion aborted: invalid download file path for job %s: %s",
                job.id,
                job.file_path,
            )
            file_cleanup_failures.append(job.file_path)
        except OSError as e:
            logger.warning(
                "Account deletion aborted: failed to remove file for job %s (%s): %s",
                job.id,
                job.file_path,
                e,
            )
            file_cleanup_failures.append(job.file_path)
        except Exception:
            logger.exception(
                "Account deletion aborted: unexpected error cleaning file for job %s (%s)",
                job.id,
                job.file_path,
            )
            file_cleanup_failures.append(job.file_path)
    return (not file_cleanup_failures, file_cleanup_failures)


@router.post("/settings/delete-account")
@limiter.limit("3/minute")
async def delete_account(
    request: Request,
    password: Annotated[str, Form(max_length=255)],
    confirm_text: Annotated[str, Form(max_length=16)],
    current_user: CurrentUserFromCookie,
    db: DbSession,
):
    """Delete current user's account and associated downloads."""
    if not await validate_csrf_token(request):
        return _htmx_or_redirect(
            request, 403, _error_html("Invalid CSRF token"), "/web/settings?error=csrf"
        )

    if confirm_text.strip().upper() != "DELETE":
        return _htmx_or_redirect(
            request,
            400,
            _error_html("Please type DELETE to confirm account deletion"),
            "/web/settings?error=delete_confirmation",
        )

    if not verify_password(password, current_user.password_hash):
        return _htmx_or_redirect(
            request,
            401,
            _error_html("Password is incorrect"),
            "/web/settings?error=bad_password",
        )

    result = await db.execute(select(DownloadJob).where(DownloadJob.user_id == current_user.id))
    jobs = result.scalars().all()

    all_cleaned, _file_cleanup_failures = _cleanup_job_files(list(jobs), logger)

    if not all_cleaned:
        return _htmx_or_redirect(
            request,
            500,
            _error_html(
                "Could not remove all downloaded files. Your account was not deleted. "
                "Please try again or contact support."
            ),
            "/web/settings?error=file_cleanup",
        )

    for job in jobs:
        await db.delete(job)

    await db.delete(current_user)
    await db.commit()

    if is_htmx_request(request):
        resp = HTMLResponse(status_code=200, content="")
        resp.headers["HX-Redirect"] = "/web/login?account_deleted=1"
        clear_token_cookies(resp)
        return resp

    redirect = RedirectResponse(url="/web/login?account_deleted=1", status_code=303)
    clear_token_cookies(redirect)
    return redirect


@router.post("/downloads")
@limiter.limit("10/minute")
async def create_download_form(
    request: Request,
    url: Annotated[str, Form(max_length=2000)],
    current_user: CurrentUserFromCookie,
    db: DbSession,
):
    """HTMX endpoint for form submissions. Returns HTML fragment."""
    # CSRF validation
    if not await validate_csrf_token(request):
        return HTMLResponse(status_code=403, content=_error_html("Invalid CSRF token"))

    # Validate URL
    if not is_youtube_url(url):
        return HTMLResponse(status_code=422, content=_error_html("Invalid YouTube URL"))

    # Create job with transactional outbox pattern (same as REST API)
    job_id = uuid.uuid4()
    job = DownloadJob(id=job_id, user_id=current_user.id, url=url, status="pending")
    db.add(job)
    try:
        await write_job_to_outbox(db, job_id)
        await db.commit()
        await db.refresh(job)
    except Exception:
        await db.rollback()
        logger.exception("failed_to_create_download_job")
        return HTMLResponse(status_code=500, content=_error_html("Failed to create download"))

    # Enqueue job for processing (best-effort; outbox handles recovery)
    try:
        await enqueue_job(job_id)
        # Mark outbox as enqueued to prevent sync_outbox_to_queue from re-publishing
        await db.execute(
            update(Outbox)
            .where(Outbox.job_id == job_id, Outbox.status == "pending")
            .values(status="enqueued")
        )
        await db.commit()
    except Exception:
        logger.warning("failed_to_enqueue_job_outbox_recovery", job_id=str(job_id))

    # Return HTML fragment for HTMX swap
    return templates.TemplateResponse(
        request, "partials/_download_item.html", get_template_context(request, job=job)
    )


@router.post("/downloads/full")
@limiter.limit("10/minute")
async def create_download_full_page(
    request: Request,
    url: Annotated[str, Form(max_length=2000)],
    current_user: CurrentUserFromCookie,
    db: DbSession,
):
    """Full-page handler for form submissions (non-HTMX fallback)."""
    # CSRF validation
    if not await validate_csrf_token(request):
        return _htmx_or_redirect(
            request, 403, _error_html("Invalid CSRF token"), "/web/downloads?error=csrf"
        )

    # Validate URL
    if not is_youtube_url(url):
        return _htmx_or_redirect(
            request, 422, _error_html("Invalid YouTube URL"), "/web/downloads?error=invalid_url"
        )

    # Create job with transactional outbox pattern (same as REST API)
    job_id = uuid.uuid4()
    job = DownloadJob(id=job_id, user_id=current_user.id, url=url, status="pending")
    db.add(job)
    try:
        await write_job_to_outbox(db, job_id)
        await db.commit()
        await db.refresh(job)
    except Exception:
        await db.rollback()
        logger.exception("failed_to_create_download_job_full_page")
        return _htmx_or_redirect(
            request,
            500,
            _error_html("Failed to create download"),
            "/web/downloads?error=creation_failed",
        )

    # Enqueue job for processing (best-effort; outbox handles recovery)
    try:
        await enqueue_job(job_id)
        # Mark outbox as enqueued to prevent sync_outbox_to_queue from re-publishing
        await db.execute(
            update(Outbox)
            .where(Outbox.job_id == job_id, Outbox.status == "pending")
            .values(status="enqueued")
        )
        await db.commit()
    except Exception:
        logger.warning("failed_to_enqueue_job_outbox_recovery", job_id=str(job_id))

    # Redirect to dashboard for full-page non-HTMX fallback
    return RedirectResponse(url="/web/downloads", status_code=303)


@router.delete("/downloads/{job_id}")
async def delete_download_form(
    request: Request,
    job_id: str,
    current_user: CurrentUserFromCookie,
    db: DbSession,
):
    """HTMX endpoint for deleting a download."""
    # CSRF validation
    if not await validate_csrf_token(request):
        return HTMLResponse(status_code=403, content=_error_html("Invalid CSRF token"))

    # Validate job_id is a valid UUID
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        return HTMLResponse(status_code=400, content=_error_html("Invalid job ID"))

    result = await db.execute(
        select(DownloadJob).where(
            DownloadJob.id == job_uuid,
            DownloadJob.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()

    if job is None:
        return HTMLResponse(status_code=404, content="")

    # Only allow deletion of terminal jobs (completed, failed, cancelled)
    # Reject deletes for jobs that are still processing to avoid races with worker
    if job.status not in ("completed", "failed", "cancelled"):
        return HTMLResponse(
            status_code=409,
            content=_error_html(
                f"Cannot delete job with status '{job.status}'. Only completed, failed, or cancelled jobs can be deleted."
            ),
        )

    # Delete file from disk before removing DB record
    if job.file_path:
        try:
            safe_path = _validate_file_path(job.file_path)
            if os.path.isfile(safe_path):
                os.remove(safe_path)
                logger.info("file_deleted", file_path=safe_path)
        except HTTPException:
            raise
        except OSError as e:
            logger.warning("failed_to_delete_file", file_path=job.file_path, error=str(e))

    await db.delete(job)
    await db.commit()

    # Return empty response for hx-swap="outerHTML" (removes element)
    return HTMLResponse(content="")


@router.get("/downloads/{job_id}/file")
async def download_file(
    request: Request,
    job_id: str,
    current_user: CurrentUserFromCookie,
    db: DbSession,
):
    """Download the file for a completed job using cookie authentication.

    This endpoint mirrors the API endpoint /api/v1/downloads/{job_id}/file
    but uses cookie-based authentication instead of bearer tokens.
    """
    from fastapi.responses import FileResponse

    # Validate job_id is a valid UUID
    try:
        job_uuid = uuid.UUID(job_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid job ID format",
        ) from None

    result = await db.execute(
        select(DownloadJob).where(
            DownloadJob.id == job_uuid,
            DownloadJob.user_id == current_user.id,
        )
    )
    job = result.scalar_one_or_none()
    if job is None:
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

    # Check if download has expired
    if job.expires_at:
        # Normalize both timestamps to UTC for comparison
        now_utc = datetime.now(UTC)
        expires_at = job.expires_at
        # Ensure expires_at is timezone-aware (convert naive to UTC)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        else:
            expires_at = expires_at.astimezone(UTC)
        if expires_at < now_utc:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Download link has expired",
            )

    # Validate path is within storage directory (prevents path traversal)
    safe_path = _validate_file_path(job.file_path)

    # Check file exists on disk
    if not os.path.isfile(safe_path):
        safe_job_id = str(job_id).replace("\r", "").replace("\n", "")
        logger.error("file_missing_from_disk", job_id=safe_job_id, file_path=safe_path)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on disk",
        )

    return FileResponse(
        path=safe_path,
        filename=job.file_name,
        media_type="application/octet-stream",
    )
