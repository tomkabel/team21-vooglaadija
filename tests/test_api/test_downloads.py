"""Downloads API endpoint tests."""

import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.download_job import DownloadJob


async def create_test_user_and_login(client: AsyncClient) -> tuple[str, str]:
    """Helper: register a user and return access token."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "downloads@example.com", "password": "testpassword123"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "downloads@example.com", "password": "testpassword123"},
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_download_success():
    """Test creating a download job with valid YouTube URL."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await create_test_user_and_login(client)
        response = await client.post(
            "/api/v1/downloads",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 201
    data = response.json()
    assert data["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert data["status"] == "pending"
    assert "id" in data
    assert "created_at" in data


@pytest.mark.asyncio
async def test_create_download_requires_auth():
    """Test that creating a download requires authentication."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/downloads",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_download_invalid_url():
    """Test that invalid URL returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await create_test_user_and_login(client)
        response = await client.post(
            "/api/v1/downloads",
            json={"url": "https://www.google.com"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_download_missing_url():
    """Test that missing URL returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await create_test_user_and_login(client)
        response = await client.post(
            "/api/v1/downloads",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_download_empty_url():
    """Test that empty URL returns 422."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await create_test_user_and_login(client)
        response = await client.post(
            "/api/v1/downloads",
            json={"url": ""},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_list_downloads_empty():
    """Test listing downloads when user has none."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await create_test_user_and_login(client)
        response = await client.get(
            "/api/v1/downloads",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["downloads"] == []


@pytest.mark.asyncio
async def test_list_downloads_with_jobs():
    """Test listing downloads returns user's jobs."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await create_test_user_and_login(client)
        # Create two downloads
        await client.post(
            "/api/v1/downloads",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            "/api/v1/downloads",
            json={"url": "https://www.youtube.com/watch?v=jNQXAC9IVRw"},
            headers={"Authorization": f"Bearer {token}"},
        )
        response = await client.get(
            "/api/v1/downloads",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    data = response.json()
    assert len(data["downloads"]) == 2


@pytest.mark.asyncio
async def test_list_downloads_requires_auth():
    """Test that listing downloads requires authentication."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/downloads")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_downloads_only_own_jobs():
    """Test that users only see their own downloads."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Create user 1 and download
        token1 = await create_test_user_and_login(client)
        await client.post(
            "/api/v1/downloads",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            headers={"Authorization": f"Bearer {token1}"},
        )
        # Create user 2 and check they don't see user 1's downloads
        await client.post(
            "/api/v1/auth/register",
            json={"email": "user2@example.com", "password": "testpassword123"},
        )
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "user2@example.com", "password": "testpassword123"},
        )
        token2 = login_response.json()["access_token"]
        response = await client.get(
            "/api/v1/downloads",
            headers={"Authorization": f"Bearer {token2}"},
        )
    assert response.status_code == 200
    data = response.json()
    assert len(data["downloads"]) == 0


@pytest.mark.asyncio
async def test_get_download_success():
    """Test getting a specific download job."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await create_test_user_and_login(client)
        # Create download
        create_response = await client.post(
            "/api/v1/downloads",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            headers={"Authorization": f"Bearer {token}"},
        )
        job_id = create_response.json()["id"]
        # Get download
        response = await client.get(
            f"/api/v1/downloads/{job_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == job_id
    assert data["url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@pytest.mark.asyncio
async def test_get_download_not_found():
    """Test getting non-existent download returns 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await create_test_user_and_login(client)
        response = await client.get(
            f"/api/v1/downloads/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_download_requires_auth():
    """Test that getting a download requires authentication."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/downloads/{uuid.uuid4()}",
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_download_file_not_completed():
    """Test that downloading a non-completed file returns 400."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await create_test_user_and_login(client)
        # Create download (status=pending)
        create_response = await client.post(
            "/api/v1/downloads",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            headers={"Authorization": f"Bearer {token}"},
        )
        job_id = create_response.json()["id"]
        # Try to get file
        response = await client.get(
            f"/api/v1/downloads/{job_id}/file",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 400
    assert "not completed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_download_file_not_found(db_session: AsyncSession):
    """Test that file with no path returns 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await create_test_user_and_login(client)
        # Create download
        create_response = await client.post(
            "/api/v1/downloads",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            headers={"Authorization": f"Bearer {token}"},
        )
        job_id = create_response.json()["id"]
        # Manually mark as completed but no file_path
        await db_session.execute(
            update(DownloadJob).where(DownloadJob.id == job_id).values(status="completed")
        )
        await db_session.commit()
        # Try to get file
        response = await client.get(
            f"/api/v1/downloads/{job_id}/file",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 404
    assert "File not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_download_success():
    """Test deleting a download job."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await create_test_user_and_login(client)
        # Create download
        create_response = await client.post(
            "/api/v1/downloads",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            headers={"Authorization": f"Bearer {token}"},
        )
        job_id = create_response.json()["id"]
        # Delete
        response = await client.delete(
            f"/api/v1/downloads/{job_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 204
        # Verify deleted
        get_response = await client.get(
            f"/api/v1/downloads/{job_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_delete_download_not_found():
    """Test deleting non-existent download returns 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await create_test_user_and_login(client)
        response = await client.delete(
            f"/api/v1/downloads/{uuid.uuid4()}",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_download_requires_auth():
    """Test that deleting a download requires authentication."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.delete(
            f"/api/v1/downloads/{uuid.uuid4()}",
        )
    assert response.status_code == 401
