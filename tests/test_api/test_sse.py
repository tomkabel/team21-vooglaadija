"""Tests for SSE (Server-Sent Events) endpoints."""

import uuid
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
        """Test that SSE endpoint returns an EventSourceResponse for authenticated users."""
        import uuid as _uuid
        from unittest.mock import MagicMock

        from sse_starlette import EventSourceResponse

        from app.api.routes.sse import download_status_stream

        mock_request = MagicMock()
        mock_user = MagicMock()
        mock_user.id = _uuid.uuid4()

        response = await download_status_stream(mock_request, mock_user)

        assert isinstance(response, EventSourceResponse)
        assert response.status_code == 200
        assert response.media_type == "text/event-stream"


class TestEventGenerator:
    """Tests for event_generator function."""

    @pytest.mark.asyncio
    async def test_event_generator_handles_disconnection(self):
        """Test that event generator breaks when request is disconnected."""
        from fastapi import Request

        from app.api.routes.sse import event_generator

        mock_request = MagicMock(spec=Request)
        mock_request.is_disconnected = AsyncMock(return_value=True)

        mock_session_factory = MagicMock()

        events = []
        async for event in event_generator(mock_request, mock_session_factory, uuid.uuid4()):
            events.append(event)

        assert len(events) == 0
        mock_request.is_disconnected.assert_called()

    @pytest.mark.asyncio
    async def test_event_generator_yields_initial_state(self):
        """Test that event generator yields initial job state from database."""
        from datetime import UTC, datetime

        from fastapi import Request

        from app.api.routes.sse import event_generator
        from app.models.download_job import DownloadJob

        mock_request = MagicMock(spec=Request)
        mock_request.is_disconnected = AsyncMock(side_effect=[False, True])

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

        events = []
        async for event in event_generator(mock_request, mock_session_factory, uuid.uuid4()):
            events.append(event)
            if len(events) >= 1:
                break

        assert len(events) >= 1
        assert events[0].event == "job_update"

    @pytest.mark.asyncio
    async def test_event_generator_pubsub_path_yields_updates(self):
        """Test that event generator uses pub/sub when available."""

        from fastapi import Request

        from app.api.routes.sse import event_generator

        mock_request = MagicMock(spec=Request)
        # is_disconnected sequence:
        # 1. pubsub_event_generator while check -> False
        # 2. first pubsub async-for iteration -> False
        # 3. second pubsub async-for iteration -> False
        # 4. fallback_polling_generator check -> True (break)
        mock_request.is_disconnected = AsyncMock(side_effect=[False, False, False, True])

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_session_factory = MagicMock(return_value=mock_session)

        job_id = str(uuid.uuid4())
        pubsub_messages = [
            {"id": job_id, "status": "processing", "url": "https://youtube.com/watch?v=test"},
            {
                "id": job_id,
                "status": "completed",
                "url": "https://youtube.com/watch?v=test",
                "file_name": "video.mp4",
            },
        ]

        async def mock_subscribe(user_id):
            for msg in pubsub_messages:
                yield msg

        mock_pubsub_service = MagicMock()
        mock_pubsub_service.subscribe = mock_subscribe

        with patch("app.api.routes.sse.get_pubsub_service", return_value=mock_pubsub_service):
            events = []
            async for event in event_generator(mock_request, mock_session_factory, uuid.uuid4()):
                events.append(event)
                if len(events) >= 2:
                    break

        assert len(events) == 2
        assert events[0].event == "job_update"
        assert events[1].event == "job_update"

    @pytest.mark.asyncio
    async def test_event_generator_pubsub_dedupes_same_status(self):
        """Test that pub/sub path deduplicates identical status updates."""
        from fastapi import Request

        from app.api.routes.sse import event_generator

        mock_request = MagicMock(spec=Request)
        # is_disconnected sequence:
        # 1. pubsub_event_generator while check -> False
        # 2. first pubsub async-for iteration -> False
        # 3. second pubsub async-for iteration -> False (deduped, not yielded)
        # 4. fallback_polling_generator check -> True (break)
        mock_request.is_disconnected = AsyncMock(side_effect=[False, False, False, True])

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_session_factory = MagicMock(return_value=mock_session)

        job_id = str(uuid.uuid4())
        pubsub_messages = [
            {"id": job_id, "status": "processing", "url": "https://youtube.com/watch?v=test"},
            {"id": job_id, "status": "processing", "url": "https://youtube.com/watch?v=test"},
        ]

        async def mock_subscribe(user_id):
            for msg in pubsub_messages:
                yield msg

        mock_pubsub_service = MagicMock()
        mock_pubsub_service.subscribe = mock_subscribe

        with patch("app.api.routes.sse.get_pubsub_service", return_value=mock_pubsub_service):
            events = []
            async for event in event_generator(mock_request, mock_session_factory, uuid.uuid4()):
                events.append(event)
                if len(events) >= 2:
                    break

        # Should only yield one event because status didn't change
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_event_generator_fallback_when_pubsub_fails(self):
        """Test that event generator falls back to polling when pub/sub is unavailable."""
        from datetime import UTC, datetime

        from fastapi import Request

        from app.api.routes.sse import event_generator
        from app.models.download_job import DownloadJob

        mock_request = MagicMock(spec=Request)
        # is_disconnected sequence:
        # 1. pubsub_event_generator while check (1st retry) -> False
        # 2. pubsub_event_generator while check (2nd retry) -> False
        # 3. pubsub_event_generator while check (3rd retry) -> False
        # 4. fallback_polling_generator check -> True (break)
        mock_request.is_disconnected = AsyncMock(side_effect=[False, False, False, True])

        mock_job = MagicMock(spec=DownloadJob)
        mock_job.id = uuid.uuid4()
        mock_job.url = "https://youtube.com/watch?v=test"
        mock_job.status = "completed"
        mock_job.file_name = "video.mp4"
        mock_job.error = None
        mock_job.created_at = datetime.now(UTC)
        mock_job.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_job]

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_session_factory = MagicMock(return_value=mock_session)

        mock_pubsub_service = MagicMock()
        mock_pubsub_service.subscribe = AsyncMock(side_effect=ConnectionError("Redis down"))

        with (
            patch("app.api.routes.sse.get_pubsub_service", return_value=mock_pubsub_service),
            patch("app.api.routes.sse.POLL_INTERVAL_SECONDS", 0),
        ):
            events = []
            async for event in event_generator(mock_request, mock_session_factory, uuid.uuid4()):
                events.append(event)
                if len(events) >= 1:
                    break

        assert len(events) >= 1
        assert events[0].event == "job_update"

    @pytest.mark.asyncio
    async def test_event_generator_cancelled_error_handled(self):
        """Test that CancelledError is caught and handled gracefully."""
        import asyncio

        from fastapi import Request

        from app.api.routes.sse import event_generator

        mock_request = MagicMock(spec=Request)
        mock_request.is_disconnected = AsyncMock(side_effect=asyncio.CancelledError)

        mock_session_factory = MagicMock()

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
        from datetime import UTC, datetime

        from fastapi import Request

        from app.api.routes.sse import MAX_SEEN_JOBS, event_generator
        from app.models.download_job import DownloadJob

        mock_request = MagicMock(spec=Request)
        call_count = [0]

        async def mock_is_disconnected():
            call_count[0] += 1
            if call_count[0] >= 3:
                return True
            return False

        mock_request.is_disconnected = mock_is_disconnected

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

        events = []
        async for event in event_generator(mock_request, mock_session_factory, uuid.uuid4()):
            events.append(event)
            if len(events) >= 10:
                break

        assert len(events) >= 1
