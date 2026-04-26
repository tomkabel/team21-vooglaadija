"""FastAPI application entry point with structured logging and performance optimizations.

Features:
- structlog for structured JSON logging in production
- orjson for fast JSON serialization
- uvloop for improved async performance
- Sentry for error tracking (production only)
"""

import os
import signal
import threading
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

# Optional: uvloop for better async performance (installed separately)
try:
    import uvloop

    uvloop.install()
    UVLOOP_AVAILABLE = True
except ImportError:
    UVLOOP_AVAILABLE = False

from app.api.middleware import PrometheusMiddleware
from app.api.rate_limit_config import limiter, rate_limit_exceeded_handler
from app.api.routes import auth, downloads, health
from app.api.routes.metrics import router as metrics_router
from app.api.routes.sse import router as sse_router
from app.api.routes.web import router as web_router
from app.auth import verify_token
from app.config import settings
from app.logging_config import configure_logging, get_logger
from app.metrics import init_metrics
from app.schemas.error import ErrorCode, error_response_dict

# Initialize structlog - must happen before any logging
configure_logging(log_level=os.environ.get("LOG_LEVEL", "INFO"))
logger = get_logger(__name__)

APP_VERSION = "0.1.0"


class _ShutdownState:
    """Thread-safe shutdown state tracker."""

    def __init__(self) -> None:
        self._received: int = 0
        self._lock = threading.Lock()

    @property
    def received(self) -> int:
        with self._lock:
            return self._received

    def set(self, signum: int) -> None:
        with self._lock:
            self._received = signum


_shutdown_state = _ShutdownState()


def _sigterm_handler(signum: int, frame: Any) -> None:
    """Handle SIGTERM/SIGINT for shutdown diagnostics."""
    _shutdown_state.set(signum)
    signal_name = signal.Signals(signum).name if hasattr(signal, "Signals") else str(signum)
    logger.warning(
        "shutdown_signal_received",
        signal=signal_name,
        signal_number=signum,
    )


def _install_shutdown_diagnostics() -> None:
    """Install shutdown signal handlers safely from main thread.

    This function should be called from inside the lifespan() startup routine
    after Uvicorn has installed its handlers. It handles:
    - Only registering from the main thread to avoid ValueError
    - Chaining to any existing handlers instead of replacing them
    """

    def _chained_sigterm_handler(signum: int, frame: Any) -> None:
        """Handler that calls previous handler and our diagnostics."""
        _shutdown_state.set(signum)
        signal_name = signal.Signals(signum).name if hasattr(signal, "Signals") else str(signum)
        logger.warning(
            "shutdown_signal_received",
            signal=signal_name,
            signal_number=signum,
        )
        previous_handler = signal.getsignal(signal.SIGTERM)
        if callable(previous_handler) and previous_handler is not _chained_sigterm_handler:
            try:
                previous_handler(signum, frame)
            except Exception:
                pass

    try:
        # Only install from main thread to avoid ValueError
        if threading.current_thread() is threading.main_thread():
            # Get current handler to potentially chain to it
            current_handler = signal.getsignal(signal.SIGTERM)
            # Only install if not already our chained handler
            if current_handler is not _chained_sigterm_handler:
                signal.signal(signal.SIGTERM, _chained_sigterm_handler)
            # Also register SIGINT
            current_int_handler = signal.getsignal(signal.SIGINT)
            if current_int_handler is not _chained_sigterm_handler:
                signal.signal(signal.SIGINT, _chained_sigterm_handler)
            logger.info("shutdown_diagnostics_installed")
    except ValueError:
        # Not running in main thread, skip signal handler installation
        logger.warning("shutdown_diagnostics_skipped_not_main_thread")


# Sentry initialization (production only)
if settings.environment == "production" and os.environ.get("SENTRY_DSN"):
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.redis import RedisIntegration
    from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

    sentry_sdk.init(
        dsn=os.environ["SENTRY_DSN"],
        integrations=[
            FastApiIntegration(transaction_style="endpoint"),
            SqlalchemyIntegration(),
            RedisIntegration(),
        ],
        traces_sample_rate=0.1,  # 10% of transactions for performance monitoring
        profiles_sample_rate=0.1,
        environment=settings.environment,
        release=f"vooglaadija@{APP_VERSION}",
    )
    logger.info("sentry_initialized", dsn_masked="***")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Lifespan context manager for startup/shutdown events."""
    logger.info(
        "application_starting",
        version=APP_VERSION,
        environment=settings.environment,
        uvloop_available=UVLOOP_AVAILABLE,
    )
    init_metrics()

    # Validate critical assets exist at startup to fail fast with clear errors
    _template_dir = Path(__file__).resolve().parent / "templates"
    _static_dir = Path(__file__).resolve().parent / "static"
    if not _template_dir.exists():
        logger.error("templates_directory_missing", path=str(_template_dir))
    else:
        required_templates = ["base.html", "login.html", "register.html", "dashboard.html"]
        missing = [t for t in required_templates if not (_template_dir / t).exists()]
        if missing:
            logger.error("missing_templates", templates=missing, path=str(_template_dir))
        else:
            logger.info("templates_verified", count=len(required_templates), path=str(_template_dir))
    if not _static_dir.exists():
        logger.error("static_directory_missing", path=str(_static_dir))
    else:
        logger.info("static_directory_verified", path=str(_static_dir))

    # Install shutdown diagnostics after Uvicorn handlers are in place
    # This must happen after uvicorn imports the module but before handling requests
    _install_shutdown_diagnostics()

    yield
    logger.info(
        "application_shutting_down",
        shutdown_signal=_shutdown_state.received,
    )


app = FastAPI(
    title="YouTube Link Processor API",
    summary="Asynchronous API for authenticated YouTube download jobs.",
    description=(
        "REST API for user authentication, creating download jobs, tracking job status, "
        "and retrieving processed files. Authentication uses bearer JWT access tokens."
    ),
    version=APP_VERSION,
    # Use ORJSONResponse for faster JSON serialization
    default_response_class=ORJSONResponse,
    contact={
        "name": "Team 21",
        "url": "https://github.com/tomkabel/team21-vooglaadija",
    },
    license_info={
        "name": "GPLv3",
        "url": "https://www.gnu.org/licenses/gpl-3.0.html",
    },
    openapi_tags=[
        {
            "name": "auth",
            "description": "User registration, user authentication, token refresh, and current user profile.",
        },
        {
            "name": "downloads",
            "description": "Create, query, download, and delete media extraction jobs.",
        },
        {
            "name": "health",
            "description": "Service health and readiness checks.",
        },
    ],
    lifespan=lifespan,
)

app.add_middleware(PrometheusMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# Security headers middleware (CSP and other best practices)
@app.middleware("http")
async def add_security_headers(request: Request, call_next: Any) -> Any:
    """Add Content-Security-Policy and other security headers to all responses."""
    # Generate a secure nonce for inline script tags
    nonce = uuid.uuid4().hex
    request.state.nonce = nonce

    response = await call_next(request)

    # CSP: Allow same-origin scripts with nonce for inline scripts, allow Google Fonts CDN
    response.headers["Content-Security-Policy"] = (
        f"default-src 'self'; "
        f"script-src 'self' 'nonce-{nonce}'; "
        f"style-src 'self' https://fonts.googleapis.com 'unsafe-inline'; "
        f"font-src 'self' https://fonts.gstatic.com; "
        f"img-src 'self' data: blob:; "
        f"connect-src 'self'; "
        f"frame-ancestors 'none'; "
        f"base-uri 'self'; "
        f"form-action 'self'"
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    return response


# Request ID middleware for debugging
@app.middleware("http")
async def add_request_id(request: Request, call_next: Any) -> Any:
    """Add a unique request ID to each request for debugging."""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# Configure CORS
origins = settings.cors_origins.split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

app.mount(
    "/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static"
)


# Global exception handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle HTTP exceptions with standardized error response."""
    # Get request_id if available
    request_id = getattr(request.state, "request_id", "unknown")

    # Map status codes to error codes
    error_code_map = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.UNAUTHORIZED,
        403: ErrorCode.FORBIDDEN,
        404: ErrorCode.NOT_FOUND,
        405: ErrorCode.VALIDATION_ERROR,
        406: ErrorCode.VALIDATION_ERROR,
        409: ErrorCode.RESOURCE_CONFLICT,
        415: ErrorCode.VALIDATION_ERROR,
        422: ErrorCode.VALIDATION_ERROR,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE,
    }

    # Default to VALIDATION_ERROR for unmapped 4xx, INTERNAL_ERROR for 5xx
    code = error_code_map.get(
        exc.status_code,
        ErrorCode.VALIDATION_ERROR if 400 <= exc.status_code < 500 else ErrorCode.INTERNAL_ERROR,
    )

    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        error_code=code.value,
        detail=str(exc.detail),
        request_id=request_id,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response_dict(code, str(exc.detail)),
        headers=exc.headers or None,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors with standardized error response."""
    request_id = getattr(request.state, "request_id", "unknown")

    # Extract validation errors details
    errors = []
    for error in exc.errors():
        errors.append(
            {
                "field": ".".join(str(loc) for loc in error["loc"] if loc != "body"),
                "message": error["msg"],
                "type": error["type"],
            },
        )

    logger.warning(
        "validation_error",
        error_count=len(errors),
        request_id=request_id,
    )

    return JSONResponse(
        status_code=422,
        content=error_response_dict(
            ErrorCode.VALIDATION_ERROR,
            "Request validation failed",
            details={"validation_errors": errors},
        ),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unexpected exceptions with standardized error response."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        "unhandled_exception",
        exception_type=type(exc).__name__,
        exception_message=str(exc),
        request_id=request_id,
        exc_info=True,
    )

    # Sentry will automatically capture the exception if configured
    return JSONResponse(
        status_code=500,
        content=error_response_dict(ErrorCode.INTERNAL_ERROR, "An internal error occurred"),
        headers={"X-Request-ID": request_id},
    )


app.include_router(auth.router, prefix="/api/v1")
app.include_router(downloads.router, prefix="/api/v1")
app.include_router(health.router, prefix="/api/v1")
app.include_router(metrics_router)

# Web/HTMX routes - SSE mounted FIRST so /web/downloads/stream is matched before /web/downloads
# Both routers have their own prefix="/web" defined, so include without additional prefix
app.include_router(sse_router)  # prefix="/web", routes: /web/downloads/stream
app.include_router(web_router)  # prefix="/web", routes: /web/login, /web/downloads, etc.


@app.get("/")
async def root(request: Request) -> RedirectResponse:
    """Redirect root to login or dashboard based on auth status."""
    # Check if user has a valid token in cookies
    token = request.cookies.get("access_token")
    if token:
        payload = verify_token(token)
        if payload is not None:
            # User is authenticated, redirect to dashboard
            return RedirectResponse(url="/web/downloads", status_code=303)

    # Not authenticated, redirect to login
    return RedirectResponse(url="/web/login", status_code=303)
