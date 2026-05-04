"""Rate limiting configuration using slowapi."""

import os
import re
import time  # Lisatud UNIX timestampi jaoks

from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from starlette.requests import Request
from starlette.responses import JSONResponse
from slowapi.storages import RedisStorage

from app.schemas.error import ErrorCode, error_response_dict

# Disable rate limiting in test mode
is_testing = os.environ.get("TESTING", "").lower() in ("1", "true", "yes", "on")


class NoOpLimiter:
    """A no-op limiter that doesn't enforce rate limits."""

    def limit(self, *args, **kwargs):
        """Return a no-op decorator."""

        def noop_decorator(func):
            return func

        return noop_decorator

    async def __call__(self, request, *args, **kwargs):
        """Allow all requests."""


if is_testing:
    limiter = NoOpLimiter()
else:
    # Use Redis storage for production/shared state across replicas
    # Eeldame, et REDIS_URL on kättesaadav (näiteks os.environ kaudu)
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")
    redis_storage = RedisStorage.from_url(REDIS_URL)
    limiter = Limiter(key_func=get_remote_address, storage=redis_storage)


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
        # Fall back to 60 seconds (minute) for unknown units
        multiplier = 60
    return window * multiplier


async def rate_limit_exceeded_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle rate limit exceeded errors with standardized error response."""
    if not isinstance(exc, RateLimitExceeded):
        raise exc
        
    retry_after = _parse_retry_after(str(exc.detail))
    # Arvutame hetke aja põhjal uue UNIX-i ajatempli
    unix_timestamp = int(time.time() + retry_after)

    return JSONResponse(
        status_code=429,
        content=error_response_dict(ErrorCode.RATE_LIMIT_EXCEEDED, str(exc.detail)),
        headers={
            "Retry-After": str(retry_after),
            "X-RateLimit-Limit": "60",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(unix_timestamp),
        },
    )
