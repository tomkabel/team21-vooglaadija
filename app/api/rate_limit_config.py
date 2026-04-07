"""Rate limiting configuration using slowapi."""

import re

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse

from app.schemas.error import ErrorCode, error_response_dict

limiter = Limiter(key_func=get_remote_address)


def _parse_retry_after(detail: str) -> int:
    """Parse slowapi detail string to get retry-after seconds.

    Detail format: "X per Y <unit>" e.g., "5 per 1 minute"
    Returns integer seconds until retry is allowed.
    """
    match = re.match(r"(\d+)\s+per\s+(\d+)\s+(\w+)", detail)
    if not match:
        return 60  # Default to 60 seconds if parsing fails
    _, window, unit = match.groups()
    window = int(window)
    unit = unit.lower().rstrip("s")  # normalize "minutes" to "minute"
    multipliers = {
        "second": 1,
        "minute": 60,
        "hour": 3600,
        "day": 86400,
    }
    multiplier = multipliers.get(unit)
    if multiplier is None:
        raise ValueError(f"Unknown time unit in rate limit detail: {unit}")
    return window * multiplier


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Handle rate limit exceeded errors with standardized error response."""
    retry_after = _parse_retry_after(str(exc.detail))
    return JSONResponse(
        status_code=429,
        content=error_response_dict(ErrorCode.RATE_LIMIT_EXCEEDED, str(exc.detail)),
        headers={"Retry-After": str(retry_after)},
    )
