"""Downloads API endpoint tests."""

import uuid
from datetime import UTC, datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.models.download_job import DownloadJob


async def create_test_user_and_login(
    client: AsyncClient, email: str = "downloads@example.com"
) -> str:
    """Helper: register a user and return access token."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "testpassword123"},
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "testpassword123"},
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
    assert data["pagination"]["total"] == 0
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["per_page"] == 20


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
    assert data["pagination"]["total"] == 2


@pytest.mark.asyncio
async def test_list_downloads_pagination():
    """Test pagination parameters work."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await create_test_user_and_login(client)
        # Create 3 downloads
        for _ in range(3):
            await client.post(
                "/api/v1/downloads",
                json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
                headers={"Authorization": f"Bearer {token}"},
            )
        # Get page 1 with per_page=2
        response = await client.get(
            "/api/v1/downloads?page=1&per_page=2",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    data = response.json()
    assert len(data["downloads"]) == 2
    assert data["pagination"]["total"] == 3
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["per_page"] == 2


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


@pytest.mark.asyncio
async def test_get_download_file_expired_returns_410(db_session: AsyncSession):
    """Test that downloading an expired file returns 410 Gone.

    Uses a past datetime stored as naive (SQLite strips timezone info).
    Mocks datetime.now in the route to return a naive datetime well in the future
    so that the stored (naive) past datetime is considered expired.
    """
    from unittest.mock import MagicMock, patch  # noqa: PLC0415

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await create_test_user_and_login(client)
        create_response = await client.post(
            "/api/v1/downloads",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            headers={"Authorization": f"Bearer {token}"},
        )
        job_id = create_response.json()["id"]

        # Store a datetime in the past (SQLite loses tz info on retrieval)
        past_naive = datetime(2000, 1, 1, 0, 0, 0, tzinfo=UTC)
        await db_session.execute(
            update(DownloadJob)
            .where(DownloadJob.id == job_id)
            .values(
                status="completed",
                file_path="/tmp/fake_file.mp4",
                expires_at=past_naive,
            )
        )
        await db_session.commit()

        # Mock datetime.now to return a datetime in the future
        future_naive = datetime(2099, 1, 1, 0, 0, 0, tzinfo=UTC)
        mock_dt = MagicMock()
        mock_dt.now.return_value = future_naive

        with patch("app.api.routes.downloads.datetime", mock_dt):
            response = await client.get(
                f"/api/v1/downloads/{job_id}/file",
                headers={"Authorization": f"Bearer {token}"},
            )
    assert response.status_code == 410
    assert "expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_download_file_path_traversal_returns_403(db_session: AsyncSession):
    """Test that a file_path outside storage directory returns 403 (path traversal prevention).

    Uses None for expires_at so the expiry check is bypassed (not yet expired).
    The path traversal check should trigger before any file existence check.
    """
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await create_test_user_and_login(client)
        create_response = await client.post(
            "/api/v1/downloads",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            headers={"Authorization": f"Bearer {token}"},
        )
        job_id = create_response.json()["id"]

        # Simulate a malicious file_path stored in DB; expires_at=None means not expired
        await db_session.execute(
            update(DownloadJob)
            .where(DownloadJob.id == job_id)
            .values(
                status="completed",
                file_path="/etc/passwd",
                expires_at=None,
            )
        )
        await db_session.commit()

        response = await client.get(
            f"/api/v1/downloads/{job_id}/file",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_download_file_not_on_disk(db_session: AsyncSession):
    """Test that a completed job whose file is missing from disk returns 404.

    Uses expires_at=None so the expiry check is skipped.
    The file_path is within storage dir but doesn't exist on disk.
    """
    import os  # noqa: PLC0415

    from app.config import settings  # noqa: PLC0415

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await create_test_user_and_login(client)
        create_response = await client.post(
            "/api/v1/downloads",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            headers={"Authorization": f"Bearer {token}"},
        )
        job_id = create_response.json()["id"]

        # Use a path inside storage dir that doesn't actually exist on disk
        storage_downloads = os.path.join(settings.storage_path, "downloads")
        os.makedirs(storage_downloads, exist_ok=True)
        nonexistent_path = os.path.join(storage_downloads, f"{uuid.uuid4()}.mp4")

        await db_session.execute(
            update(DownloadJob)
            .where(DownloadJob.id == job_id)
            .values(
                status="completed",
                file_path=nonexistent_path,
                expires_at=None,
            )
        )
        await db_session.commit()

        response = await client.get(
            f"/api/v1/downloads/{job_id}/file",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_list_downloads_page_2(db_session: AsyncSession):
    """Test that page 2 returns the second set of results."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token = await create_test_user_and_login(client)
        for _ in range(3):
            await client.post(
                "/api/v1/downloads",
                json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
                headers={"Authorization": f"Bearer {token}"},
            )
        response = await client.get(
            "/api/v1/downloads?page=2&per_page=2",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert response.status_code == 200
    data = response.json()
    assert len(data["downloads"]) == 1
    assert data["pagination"]["total"] == 3
    assert data["pagination"]["page"] == 2
    assert data["pagination"]["per_page"] == 2


@pytest.mark.asyncio
async def test_list_downloads_user_isolation():
    """Test that user A cannot see user B's download jobs."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        token_a = await create_test_user_and_login(client, "isolation_a@example.com")
        token_b = await create_test_user_and_login(client, "isolation_b@example.com")

        # User A creates a download
        create_resp = await client.post(
            "/api/v1/downloads",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"},
            headers={"Authorization": f"Bearer {token_a}"},
        )
        job_id_a = create_resp.json()["id"]

        # User B should not be able to fetch user A's specific job
        response = await client.get(
            f"/api/v1/downloads/{job_id_a}",
            headers={"Authorization": f"Bearer {token_b}"},
        )
    assert response.status_code == 404
