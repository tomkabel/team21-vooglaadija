import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.api.dependencies import CurrentUser, DbSession
from app.auth import create_access_token, create_refresh_token, verify_token
from app.middleware.rate_limit import RateLimiter
from app.models.user import User
from app.schemas.token import Token, TokenRefresh
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import hash_password, verify_password
from worker.queue import redis_client

router = APIRouter(prefix="/auth", tags=["auth"])

# Initialize rate limiter for auth endpoints (5 requests per minute)
auth_rate_limiter = RateLimiter(
    redis_client=redis_client,
    max_requests=5,
    window_seconds=60,
)


async def check_auth_rate_limit(request: Request) -> None:
    """Dependency to check rate limit for auth endpoints."""
    client_ip = request.client.host if request.client else "unknown"
    endpoint = request.url.path
    key = f"auth:{endpoint}:{client_ip}"

    if not await auth_rate_limiter.is_allowed(key):
        retry_after = await auth_rate_limiter.get_retry_after(key)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_data: UserCreate,
    db: DbSession,
    _: Annotated[None, Depends(check_auth_rate_limit)],
) -> UserResponse:
    user = User(
        id=str(uuid.uuid4()),
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
async def login(
    request: Request,
    user_data: UserCreate,
    db: DbSession,
    _: Annotated[None, Depends(check_auth_rate_limit)],
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

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
    )


@router.post("/refresh", response_model=Token)
async def refresh(
    request: Request,
    token_refresh: TokenRefresh,
    db: DbSession,
    _: Annotated[None, Depends(check_auth_rate_limit)],
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

    result = await db.execute(select(User).where(User.id == user_id))
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
