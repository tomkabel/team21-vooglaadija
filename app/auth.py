from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any
from uuid import UUID

from jose import JWTError, jwt

from app.config import settings

if TYPE_CHECKING:
    from starlette.responses import Response

ALGORITHM = "HS256"


def create_access_token(subject: UUID | str) -> str:
    expire = datetime.now(UTC) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def create_refresh_token(subject: UUID | str) -> str:
    expire = datetime.now(UTC) + timedelta(days=settings.refresh_token_expire_days)
    payload = {"sub": str(subject), "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def verify_token(token: str) -> dict[str, Any] | None:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def set_token_cookies(
    response: "Response", access_token: str, refresh_token: str, secure: bool = True
) -> None:
    """Set JWT tokens as HttpOnly cookies on the response.

    Args:
        response: FastAPI Response object to set cookies on
        access_token: JWT access token string
        refresh_token: JWT refresh token string
        secure: If True, cookies are only sent over HTTPS. Set False for local development.
    """
    # Set access token cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
        max_age=settings.access_token_expire_minutes * 60,
    )
    # Set refresh token cookie (longer-lived)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
        max_age=settings.refresh_token_expire_days * 24 * 60 * 60,
    )


def clear_token_cookies(response: "Response") -> None:
    """Clear JWT tokens from cookies (for logout)."""
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
