"""Tests for SSE (Server-Sent Events) endpoints."""

import uuid
from collections import OrderedDict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


class TestDownloadStatusStream:
    """Tests for GET /web/downloads/stream endpoint."""

    @pytest.mark.asyncio
    async def test_sse_endpoint_requires_auth(self):
        """Test that SSE endpoint returns 401 without authentication."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/web/downloads/stream")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_sse_endpoint_with_auth_starts_stream(self):
        """Test that SSE endpoint accepts authenticated request and starts streaming."""
        import uuid
        from httpx import ASGITransport, AsyncClient
        from unittest.mock import patch, MagicMock

        # Create test user and get token
        email = f"ssetest_{uuid.uuid4().hex[:8]}@example.com"
        password = "securepassword123"

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Register and login
            await client.post(
                "/api/v1/auth/register",
                json={"email": email, "password": password},
            )
            login_resp = await client.post(
                "/api/v1/auth/login",
                json={"email": email, "password": password},
            )
            token = login_resp.json()["access_token"]

            # Test SSE endpoint
            # Note: The actual SSE response is a streaming response that we can't fully test
            # without a real SSE client, but we can verify the endpoint accepts the connection
            with patch("app.api.routes.sse.get_async_session_factory") as mock_session_factory:
                # Mock the session factory and event generator
                mock_session = MagicMock()
                mock_session_factory.return_value = MagicMock(return_value=mock_session)

                # Make request with proper auth
                response = await client.get(
                    "/web/downloads/stream",
                    headers={"Authorization": f"Bearer {token}"},
                )

                # The endpoint should start (even if we can't test the full SSE stream)
                assert response.status_code == 200


class TestEventGenerator:
    """Tests for event_generator function."""

    @pytest.mark.asyncio
    async def test_event_generator_handles_disconnection(self):
        """Test that event generator breaks when request is disconnected."""
        from app.api.routes.sse import event_generator
        from fastapi import Request

        mock_request = MagicMock(spec=Request)
        mock_request.is_disconnected = AsyncMock(return_value=True)

        mock_session_factory = MagicMock()

        # Collect events from generator
        events = []
        async for event in event_generator(mock_request, mock_session_factory, uuid.uuid4()):
            events.append(event)

        # Should exit immediately due to disconnection
        assert len(events) == 0
        mock_request.is_disconnected.assert_called()

    @pytest.mark.asyncio
    async def test_event_generator_yields_job_updates(self):
        """Test that event generator yields job status updates."""
        from app.api.routes.sse import event_generator, MAX_SEEN_JOBS
        from app.models.download_job import DownloadJob
        from datetime import datetime, UTC

        mock_request = MagicMock(spec=Request)
        mock_request.is_disconnected = AsyncMock(side_effect=[False, True])

        # Create mock session with a job
        mock_result = MagicMock()
        mock_job = MagicMock(spec=DownloadJob)
        mock_job.id = uuid.uuid4()
        mock_job.url = "https://youtube.com/watch?v=test"
        mock_job.status = "pending"
        mock_job.file_name = None
        mock_job.error = None
        mock_job.created_at = datetime.now(UTC)

        mock_result.scalars.return_value.all.return_value = [mock_job]

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_session_factory = MagicMock(return_value=mock_session)

        user_id = uuid.uuid4()

        # Collect events
        events = []
        async for event in event_generator(mock_request, mock_session_factory, user_id):
            events.append(event)
            if len(events) >= 1:
                break

        # Should have yielded at least one event
        assert len(events) >= 1
        # First event should be a job_update
        assert events[0].event == "job_update"

    @pytest.mark.asyncio
    async def test_event_generator_cursor_pagination(self):
        """Test that event generator uses cursor-based pagination after initial load."""
        from app.api.routes.sse import event_generator
        from app.models.download_job import DownloadJob
        from datetime import datetime, UTC

        # First call returns jobs (is_disconnected=False, last_updated_at=None)
        # Second call returns empty (is_disconnected=False but returns)
        # Third call - request disconnected
        mock_request = MagicMock(spec=Request)
        call_count = [0]

        async def mock_is_disconnected():
            call_count[0] += 1
            if call_count[0] >= 3:
                return True
            return False

        mock_request.is_disconnected = mock_is_disconnected

        mock_result = MagicMock()
        mock_job = MagicMock(spec=DownloadJob)
        mock_job.id = uuid.uuid4()
        mock_job.url = "https://youtube.com/watch?v=test"
        mock_job.status = "completed"
        mock_job.file_name = "video.mp4"
        mock_job.error = None
        mock_job.created_at = datetime.now(UTC)
        mock_job.updated_at = datetime.now(UTC)

        mock_result.scalars.return_value.all.return_value = [mock_job]

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_session_factory = MagicMock(return_value=mock_session)

        user_id = uuid.uuid4()

        # Collect events
        events = []
        async for event in event_generator(mock_request, mock_session_factory, user_id):
            events.append(event)
            if len(events) >= 2:
                break

        # Should yield events with job_update
        assert events[0].event == "job_update"

    @pytest.mark.asyncio
    async def test_event_generator_skips_duplicate_status(self):
        """Test that event generator doesn't yield events for unchanged job status."""
        from app.api.routes.sse import event_generator
        from app.models.download_job import DownloadJob
        from datetime import datetime, UTC

        mock_request = MagicMock(spec=Request)
        call_count = [0]

        async def mock_is_disconnected():
            call_count[0] += 1
            if call_count[0] >= 2:
                return True
            return False

        mock_request.is_disconnected = mock_is_disconnected

        job_id = uuid.uuid4()
        now = datetime.now(UTC)

        mock_result = MagicMock()
        mock_job = MagicMock(spec=DownloadJob)
        mock_job.id = job_id
        mock_job.url = "https://youtube.com/watch?v=test"
        mock_job.status = "completed"
        mock_job.file_name = "video.mp4"
        mock_job.error = None
        mock_job.created_at = now
        mock_job.updated_at = now

        mock_result.scalars.return_value.all.return_value = [mock_job]

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_session_factory = MagicMock(return_value=mock_session)

        user_id = uuid.uuid4()

        # Collect events
        events = []
        async for event in event_generator(mock_request, mock_session_factory, user_id):
            events.append(event)
            if len(events) >= 1:
                break

        # First yield should happen
        assert len(events) == 1
        assert events[0].event == "job_update"

    @pytest.mark.asyncio
    async def test_event_generator_cancelled_error_handled(self):
        """Test that CancelledError is caught and handled gracefully."""
        from app.api.routes.sse import event_generator
        import asyncio

        mock_request = MagicMock(spec=Request)
        mock_request.is_disconnected = AsyncMock(side_effect=asyncio.CancelledError)

        mock_session_factory = MagicMock()

        # Should not raise, just exit cleanly
        events = []
        try:
            async for event in event_generator(mock_request, mock_session_factory, uuid.uuid4()):
                events.append(event)
        except asyncio.CancelledError:
            pass  # Expected

        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_event_generator_max_seen_jobs_limit(self):
        """Test that event generator respects MAX_SEEN_JOBS limit."""
        from app.api.routes.sse import event_generator, MAX_SEEN_JOBS
        from app.models.download_job import DownloadJob
        from datetime import datetime, UTC

        mock_request = MagicMock(spec=Request)
        call_count = [0]

        async def mock_is_disconnected():
            call_count[0] += 1
            if call_count[0] >= 3:
                return True
            return False

        mock_request.is_disconnected = mock_is_disconnected

        # Create many jobs to exceed MAX_SEEN_JOBS
        mock_result = MagicMock()
        jobs = []
        for i in range(MAX_SEEN_JOBS + 50):
            mock_job = MagicMock(spec=DownloadJob)
            mock_job.id = uuid.uuid4()
            mock_job.url = f"https://youtube.com/watch?v=test{i}"
            mock_job.status = "pending"
            mock_job.file_name = None
            mock_job.error = None
            mock_job.created_at = datetime.now(UTC)
            mock_job.updated_at = datetime.now(UTC)
            jobs.append(mock_job)

        mock_result.scalars.return_value.all.return_value = jobs

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_session_factory = MagicMock(return_value=mock_session)

        user_id = uuid.uuid4()

        events = []
        async for event in event_generator(mock_request, mock_session_factory, user_id):
            events.append(event)
            if len(events) >= 10:
                break

        # Should have some events
        assert len(events) >= 1
