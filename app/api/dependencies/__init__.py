from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import verify_token
from app.database import get_db
from app.models.user import User, not_deleted

security = HTTPBearer(auto_error=False)  # auto_error=False allows None


DbSession = Annotated[AsyncSession, Depends(get_db)]


async def get_current_user_from_cookie(
    db: DbSession,
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)] = None,
) -> User:
    """Get current user from JWT cookie (HTMX) or Bearer token (API clients).

    Tries in order:
    1. Authorization: Bearer <token> header (for API clients)
    2. access_token cookie (for HTMX/browser requests)
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Try Bearer token first (API clients)
    token = None
    if credentials is not None:
        token = credentials.credentials
    else:
        # Fall back to cookie (HTMX/browser)
        token = request.cookies.get("access_token")

    if not token:
        raise credentials_exception

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None or not isinstance(user_id, str):
        raise credentials_exception

    try:
        user_uuid = UUID(user_id)
    except (ValueError, TypeError):
        raise credentials_exception from None

    result = await db.execute(select(User).where(User.id == user_uuid, not_deleted()))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception from None

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
    db: DbSession,
) -> User:
    """Get the current authenticated user from JWT token (Bearer only)."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token = credentials.credentials
    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    user_id = payload.get("sub")
    if user_id is None or not isinstance(user_id, str):
        raise credentials_exception

    try:
        user_uuid = UUID(user_id)
    except (ValueError, TypeError):
        raise credentials_exception from None

    result = await db.execute(select(User).where(User.id == user_uuid, not_deleted()))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    # Check that the user account is still active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserFromCookie = Annotated[User, Depends(get_current_user_from_cookie)]
