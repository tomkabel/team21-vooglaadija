"""Authentication endpoints (REST API)."""

from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import CurrentUser, DbSession
from app.api.rate_limit_config import limiter
from app.auth import (
    clear_token_cookies,
    create_access_token,
    create_refresh_token,
    set_token_cookies,
    verify_token,
)
from app.config import settings
from app.models.user import User
from app.schemas.token import Token, TokenRefresh
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    user_data: UserCreate,
    db: DbSession,
) -> UserResponse:
    user = User(
        id=uuid4(),
        email=user_data.email,
        password_hash=hash_password(user_data.password),
    )
    db.add(user)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from None
    await db.refresh(user)

    return UserResponse(id=user.id, email=user.email)


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    user_data: UserCreate,
    db: DbSession,
) -> Token:
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    # Set JWT tokens as HttpOnly cookies for HTMX/browser auth
    set_token_cookies(response, access_token, refresh_token, secure=settings.cookie_secure)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=Token)
@limiter.limit("5/minute")
async def refresh(
    request: Request,
    token_refresh: TokenRefresh,
    db: DbSession,
) -> Token:
    payload = verify_token(token_refresh.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_type = payload.get("type")
    if token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == UUID(user_id)))
    user = result.scalar_one_or_none()

    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(user.id)

    return Token(
        access_token=access_token,
        refresh_token=token_refresh.refresh_token,
        token_type="bearer",
    )


@router.get("/me", response_model=UserResponse)
async def me(current_user: CurrentUser) -> UserResponse:
    return UserResponse(id=current_user.id, email=current_user.email)


@router.post("/logout")
async def logout(request: Request, response: Response):
    """Clear auth cookies and redirect to login.

    Logout is a POST action to prevent CSRF from logout links.
    """
    clear_token_cookies(response)
    return RedirectResponse(url="/web/login?logged_out=1", status_code=303)
