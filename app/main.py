import logging
import os
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.middleware import PrometheusMiddleware
from app.api.rate_limit_config import limiter, rate_limit_exceeded_handler
from app.api.routes import auth, downloads, health
from app.api.routes.metrics import router as metrics_router
from app.api.routes.sse import router as sse_router
from app.api.routes.web import router as web_router
from app.auth import verify_token
from app.config import settings
from app.logging_config import setup_logging
from app.metrics import init_metrics
from app.schemas.error import ErrorCode, error_response_dict

setup_logging(log_level=os.environ.get("LOG_LEVEL", "INFO"))
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI, *args, **kwargs):
    """Lifespan context manager for startup/shutdown events."""
    logger.info("Starting YouTube Link Processor API")
    yield
    logger.info("Shutting down YouTube Link Processor API")


init_metrics()

app = FastAPI(title="YouTube Link Processor", lifespan=lifespan)

app.add_middleware(PrometheusMiddleware)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# Security headers middleware (CSP and other best practices)
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Add Content-Security-Policy and other security headers to all responses."""
    # Generate a secure nonce for inline script tags
    nonce = uuid.uuid4().hex
    request.state.nonce = nonce

    response = await call_next(request)

    # CSP: Allow same-origin scripts with nonce for inline scripts, allow Google Fonts CDN
    response.headers["Content-Security-Policy"] = (
        f"default-src 'self'; "
        f"script-src 'self' https://fonts.googleapis.com 'nonce-{nonce}'; "
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
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"

    return response


# Request ID middleware for debugging
@app.middleware("http")
async def add_request_id(request: Request, call_next):
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
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with standardized error response."""
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

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response_dict(code, str(exc.detail)),
        headers=exc.headers or None,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with standardized error response."""
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

    return JSONResponse(
        status_code=422,
        content=error_response_dict(
            ErrorCode.VALIDATION_ERROR,
            "Request validation failed",
            details={"validation_errors": errors},
        ),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions with standardized error response."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"Unhandled exception [{request_id}]: {exc}", exc_info=True)

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
async def root(request: Request):
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
