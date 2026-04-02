"""Auth endpoint tests."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_register_creates_user():
    """Test that valid registration creates a user and returns 201."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "testpassword123"},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email_fails():
    """Test that registering with existing email returns 409.

    Under SQLite, the IntegrityError lacks a pgcode attribute, so the
    production code re-raises the exception. We monkey-patch the SQLite
    IntegrityError to add a pgcode attribute so the 409 path is exercised
    regardless of the test database backend.
    """
    import sqlite3

    # Save original and patch SQLite IntegrityError to have pgcode
    original_init = sqlite3.IntegrityError.__init__

    def patched_init(self, *args, **kwargs):
        original_init(self, *args, **kwargs)
        self.pgcode = "23505"

    sqlite3.IntegrityError.__init__ = patched_init
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # First registration
            await client.post(
                "/api/v1/auth/register",
                json={"email": "duplicate@example.com", "password": "testpassword123"},
            )
            # Second registration with same email — triggers IntegrityError
            # with pgcode="23505" → returns 409
            response = await client.post(
                "/api/v1/auth/register",
                json={"email": "duplicate@example.com", "password": "testpassword123"},
            )
    finally:
        sqlite3.IntegrityError.__init__ = original_init

    assert response.status_code == 409
    assert "Email already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_invalid_email_fails():
    """Test that invalid email format returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "testpassword123"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password_fails():
    """Test that password shorter than 8 chars returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com", "password": "short"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_missing_fields_fails():
    """Test that missing fields return 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "test@example.com"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_success_returns_tokens():
    """Test that valid credentials return access and refresh tokens."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register first
        await client.post(
            "/api/v1/auth/register",
            json={"email": "login@example.com", "password": "testpassword123"},
        )
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "login@example.com", "password": "testpassword123"},
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password_fails():
    """Test that wrong password returns 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register first
        await client.post(
            "/api/v1/auth/register",
            json={"email": "wrongpass@example.com", "password": "testpassword123"},
        )
        # Login with wrong password
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrongpass@example.com", "password": "wrongpassword"},
        )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user_fails():
    """Test that unknown email returns 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "testpassword123"},
        )
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_missing_fields_fails():
    """Test that missing fields return 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "test@example.com"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_refresh_valid_token_returns_new_access():
    """Test that valid refresh token returns new access token."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={"email": "refresh@example.com", "password": "testpassword123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@example.com", "password": "testpassword123"},
        )
        refresh_token = login_response.json()["refresh_token"]

        # Refresh
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_invalid_token_fails():
    """Test that invalid refresh token returns 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid-token"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_authenticated_returns_user():
    """Test that valid token returns user data."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Register and login
        await client.post(
            "/api/v1/auth/register",
            json={"email": "me@example.com", "password": "testpassword123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "me@example.com", "password": "testpassword123"},
        )
        access_token = login_response.json()["access_token"]

        # Get me
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"
    assert "id" in data


@pytest.mark.asyncio
async def test_me_no_token_fails():
    """Test that missing token returns 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_inactive_user_fails(db_session):
    """Test that inactive user cannot login (is_active=False check in login route)."""
    from sqlalchemy import update

    from app.models.user import User

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "inactive@example.com", "password": "testpassword123"},
        )

    # Deactivate the user directly in the database
    await db_session.execute(
        update(User).where(User.email == "inactive@example.com").values(is_active=False)
    )
    await db_session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "inactive@example.com", "password": "testpassword123"},
        )
    assert response.status_code == 401
    assert "inactive" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_me_inactive_user_returns_401(db_session):
    """Test that get_current_user rejects inactive users (is_active check in dependency)."""
    from sqlalchemy import update

    from app.models.user import User

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "inactive2@example.com", "password": "testpassword123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "inactive2@example.com", "password": "testpassword123"},
        )
        access_token = login_response.json()["access_token"]

    # Deactivate the user after obtaining a valid token
    await db_session.execute(
        update(User).where(User.email == "inactive2@example.com").values(is_active=False)
    )
    await db_session.commit()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    assert response.status_code == 401
    assert "inactive" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_refresh_with_access_token_fails():
    """Test that using an access token as a refresh token returns 401 (type mismatch)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "tokentype@example.com", "password": "testpassword123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "tokentype@example.com", "password": "testpassword123"},
        )
        access_token = login_response.json()["access_token"]

        # Use access token where refresh token is expected
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": access_token},
        )
    assert response.status_code == 401
    assert "Invalid token type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_exactly_8_char_password_succeeds():
    """Test that password of exactly 8 characters (boundary) is accepted."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={"email": "boundary@example.com", "password": "12345678"},
        )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_me_with_refresh_token_fails():
    """Test that get_current_user rejects refresh tokens."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={"email": "refreshtoken@example.com", "password": "testpassword123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "refreshtoken@example.com", "password": "testpassword123"},
        )
        refresh_token = login_response.json()["refresh_token"]

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {refresh_token}"},
        )
    assert response.status_code == 401
