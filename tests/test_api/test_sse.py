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
        mock_job.updated_at = datetime.now(UTC)

        mock_result.scalars.return_value.all.return_value = [mock_job]

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_session_factory = MagicMock(return_value=mock_session)

        mock_pubsub_service = MagicMock()

        async def mock_subscribe(user_id):
            return
            yield

        mock_pubsub_service.subscribe = mock_subscribe

        async def mock_polling(*args, **kwargs):
            yield

        with (
            patch("app.api.routes.sse.get_pubsub_service", return_value=mock_pubsub_service),
            patch("app.api.routes.sse.fallback_polling_generator", mock_polling),
        ):
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
            {
                "id": job_id,
                "status": "processing",
                "url": "https://youtube.com/watch?v=test",
                "updated_at": "2024-01-01T00:00:00",
            },
            {
                "id": job_id,
                "status": "completed",
                "url": "https://youtube.com/watch?v=test",
                "file_name": "video.mp4",
                "updated_at": "2024-01-01T00:00:01",
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
        # 1. initial DB query phase -> False
        # 2. pubsub buffer task -> False (for multiple attempts)
        # 3. fallback_polling_generator check -> False (to get at least one poll)
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
        # Return empty list for initial DB query to test fallback path
        mock_result.scalars.return_value.all.return_value = []

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

        # Should get at least one event from the fallback polling path
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


class TestJobToSseData:
    """Tests for _job_to_sse_data function."""

    @pytest.mark.asyncio
    async def test_job_to_sse_data_with_none_timestamps(self):
        """Test _job_to_sse_data handles None timestamps."""

        from app.api.routes.sse import _job_to_sse_data
        from app.models.download_job import DownloadJob

        mock_job = MagicMock(spec=DownloadJob)
        mock_job.id = uuid.uuid4()
        mock_job.url = "https://youtube.com/watch?v=test"
        mock_job.status = "pending"
        mock_job.file_name = None
        mock_job.error = None
        mock_job.created_at = None
        mock_job.updated_at = None

        result = await _job_to_sse_data(mock_job)

        assert result["id"] == str(mock_job.id)
        assert result["url"] == mock_job.url
        assert result["status"] == mock_job.status
        assert result["file_name"] is None
        assert result["error"] is None
        assert result["created_at"] is None
        assert result["updated_at"] is None

    @pytest.mark.asyncio
    async def test_job_to_sse_data_with_timestamps(self):
        """Test _job_to_sse_data formats timestamps correctly."""
        from datetime import UTC, datetime

        from app.api.routes.sse import _job_to_sse_data
        from app.models.download_job import DownloadJob

        created = datetime(2024, 1, 1, 12, 0, 0, tzinfo=UTC)
        updated = datetime(2024, 1, 1, 12, 1, 0, tzinfo=UTC)

        mock_job = MagicMock(spec=DownloadJob)
        mock_job.id = uuid.uuid4()
        mock_job.url = "https://youtube.com/watch?v=test"
        mock_job.status = "completed"
        mock_job.file_name = "video.mp4"
        mock_job.error = None
        mock_job.created_at = created
        mock_job.updated_at = updated

        result = await _job_to_sse_data(mock_job)

        assert result["created_at"] == created.isoformat()
        assert result["updated_at"] == updated.isoformat()


class TestSubscribeToPubsub:
    """Tests for _subscribe_to_pubsub function."""

    @pytest.mark.asyncio
    async def test_subscribe_to_pubsub_dedupes_with_updated_at(self):
        """Test that messages with same job_id but different updated_at are not deduplicated."""
        from collections import OrderedDict

        from app.api.routes.sse import _subscribe_to_pubsub

        job_id = str(uuid.uuid4())
        pubsub_messages = [
            {"id": job_id, "status": "processing", "updated_at": "2024-01-01T00:00:00"},
            {"id": job_id, "status": "processing", "updated_at": "2024-01-01T00:00:01"},
        ]

        async def mock_subscribe(user_id):
            for msg in pubsub_messages:
                yield msg

        mock_pubsub = MagicMock()
        mock_pubsub.subscribe = mock_subscribe

        last_seen = OrderedDict()
        events = []
        async for event in _subscribe_to_pubsub(mock_pubsub, uuid.uuid4(), last_seen):
            events.append(event)

        assert len(events) == 2

    @pytest.mark.asyncio
    async def test_subscribe_to_pubsub_dedupes_same_updated_at(self):
        """Test that messages with same job_id and updated_at are deduplicated."""
        from collections import OrderedDict

        from app.api.routes.sse import _subscribe_to_pubsub

        job_id = str(uuid.uuid4())
        pubsub_messages = [
            {"id": job_id, "status": "processing", "updated_at": "2024-01-01T00:00:00"},
            {"id": job_id, "status": "processing", "updated_at": "2024-01-01T00:00:00"},
        ]

        async def mock_subscribe(user_id):
            for msg in pubsub_messages:
                yield msg

        mock_pubsub = MagicMock()
        mock_pubsub.subscribe = mock_subscribe

        last_seen = OrderedDict()
        events = []
        async for event in _subscribe_to_pubsub(mock_pubsub, uuid.uuid4(), last_seen):
            events.append(event)

        assert len(events) == 1


class TestPubsubEventGenerator:
    """Tests for pubsub_event_generator function."""

    @pytest.mark.asyncio
    async def test_pubsub_event_generator_reconnects_on_exception(self):
        """Test that pubsub_event_generator reconnects on exception up to max attempts."""
        from app.api.routes.sse import (
            MAX_PUBSUB_RECONNECT_ATTEMPTS,
            pubsub_event_generator,
        )

        mock_request = MagicMock()
        call_count = [0]

        async def mock_is_disconnected():
            call_count[0] += 1
            return False

        mock_request.is_disconnected = mock_is_disconnected

        reconnect_count = [0]

        async def mock_subscribe(user_id):
            reconnect_count[0] += 1
            if reconnect_count[0] < MAX_PUBSUB_RECONNECT_ATTEMPTS:
                raise Exception("Connection lost")
            return
            yield

        mock_pubsub = MagicMock()
        mock_pubsub.subscribe = mock_subscribe

        with patch("app.api.routes.sse.get_pubsub_service", return_value=mock_pubsub):
            events = []
            async for event in pubsub_event_generator(mock_request, uuid.uuid4()):
                events.append(event)
                if len(events) >= 1:
                    break

    @pytest.mark.asyncio
    async def test_pubsub_event_generator_cancelled_error(self):
        """Test that pubsub_event_generator handles CancelledError."""
        import asyncio

        from app.api.routes.sse import pubsub_event_generator

        mock_request = MagicMock()

        async def mock_is_disconnected():
            raise asyncio.CancelledError

        mock_request.is_disconnected = mock_is_disconnected

        events = []
        try:
            async for event in pubsub_event_generator(mock_request, uuid.uuid4()):
                events.append(event)
        except asyncio.CancelledError:
            pass

        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_pubsub_event_generator_stops_after_max_reconnects(self):
        """Test that pubsub_event_generator stops after max reconnect attempts."""
        from app.api.routes.sse import (
            MAX_PUBSUB_RECONNECT_ATTEMPTS,
            pubsub_event_generator,
        )

        mock_request = MagicMock()
        mock_request.is_disconnected = AsyncMock(return_value=False)

        attempt_count = [0]

        class MockAsyncIterator:
            def __init__(self):
                pass

            def __aiter__(self):
                return self

            async def __anext__(self):
                attempt_count[0] += 1
                if attempt_count[0] < MAX_PUBSUB_RECONNECT_ATTEMPTS:
                    raise Exception("Connection failed")
                raise StopAsyncIteration

        mock_pubsub_service = MagicMock()
        mock_pubsub_service.subscribe = MagicMock(return_value=MockAsyncIterator())

        with patch("app.api.routes.sse.get_pubsub_service", return_value=mock_pubsub_service):
            events = []
            async for event in pubsub_event_generator(mock_request, uuid.uuid4()):
                events.append(event)

        assert attempt_count[0] == MAX_PUBSUB_RECONNECT_ATTEMPTS


class TestFallbackPollingGenerator:
    """Tests for fallback_polling_generator function."""

    @pytest.mark.asyncio
    async def test_fallback_polling_generator_yields_jobs(self):
        """Test that fallback_polling_generator yields job updates."""
        from datetime import UTC, datetime

        from app.api.routes.sse import fallback_polling_generator
        from app.models.download_job import DownloadJob

        mock_request = MagicMock()
        mock_request.is_disconnected = AsyncMock(side_effect=[False, True])

        mock_job = MagicMock(spec=DownloadJob)
        mock_job.id = uuid.uuid4()
        mock_job.url = "https://youtube.com/watch?v=test"
        mock_job.status = "pending"
        mock_job.file_name = None
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

        with patch("app.api.routes.sse.POLL_INTERVAL_SECONDS", 0):
            events = []
            async for event in fallback_polling_generator(
                mock_request, mock_session_factory, uuid.uuid4()
            ):
                events.append(event)
                if len(events) >= 1:
                    break

        assert len(events) == 1
        assert events[0].event == "job_update"

    @pytest.mark.asyncio
    async def test_fallback_polling_generator_cancelled_error(self):
        """Test that fallback_polling_generator handles CancelledError."""
        import asyncio

        from app.api.routes.sse import fallback_polling_generator

        mock_request = MagicMock()

        async def mock_is_disconnected():
            raise asyncio.CancelledError

        mock_request.is_disconnected = mock_is_disconnected

        mock_session_factory = MagicMock()

        events = []
        try:
            async for event in fallback_polling_generator(
                mock_request, mock_session_factory, uuid.uuid4()
            ):
                events.append(event)
        except asyncio.CancelledError:
            pass

        assert len(events) == 0


class TestEventGeneratorExtended:
    """Extended tests for event_generator function."""

    @pytest.mark.asyncio
    async def test_event_generator_initial_state_exception_falls_back_to_pubsub(self):
        """Test that event_generator falls back to pubsub when initial state query fails."""
        from fastapi import Request

        from app.api.routes.sse import event_generator

        mock_request = MagicMock(spec=Request)
        mock_request.is_disconnected = AsyncMock(side_effect=[False, False, True])

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(side_effect=Exception("DB error"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_session_factory = MagicMock(return_value=mock_session)

        job_id = str(uuid.uuid4())
        pubsub_messages = [
            {
                "id": job_id,
                "status": "processing",
                "url": "https://youtube.com/watch?v=test",
                "updated_at": "2024-01-01T00:00:00",
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
                if len(events) >= 1:
                    break

        assert len(events) == 1
        assert events[0].event == "job_update"

    @pytest.mark.asyncio
    async def test_event_generator_pubsub_generator_exception_falls_back_to_polling(self):
        """Test that event_generator falls back to polling when pubsub generator fails."""
        from datetime import UTC, datetime

        from fastapi import Request

        from app.api.routes.sse import event_generator
        from app.models.download_job import DownloadJob

        mock_request = MagicMock(spec=Request)
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
        mock_pubsub_service.subscribe = AsyncMock(side_effect=Exception("Redis error"))

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
    async def test_event_generator_pubsub_success_no_fallback(self):
        """Test that event_generator does not fall back to polling when pubsub succeeds."""
        from fastapi import Request

        from app.api.routes.sse import event_generator

        mock_request = MagicMock(spec=Request)
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
            {
                "id": job_id,
                "status": "processing",
                "url": "https://youtube.com/watch?v=test",
                "updated_at": "2024-01-01T00:00:00",
            },
        ]

        async def mock_subscribe(user_id):
            for msg in pubsub_messages:
                yield msg

        mock_pubsub_service = MagicMock()
        mock_pubsub_service.subscribe = mock_subscribe

        polling_called = [False]

        async def mock_polling(*args, **kwargs):
            polling_called[0] = True
            return
            yield

        with (
            patch("app.api.routes.sse.get_pubsub_service", return_value=mock_pubsub_service),
            patch("app.api.routes.sse.fallback_polling_generator", mock_polling),
        ):
            events = []
            async for event in event_generator(mock_request, mock_session_factory, uuid.uuid4()):
                events.append(event)
                if len(events) >= 1:
                    break

        assert len(events) == 1
        assert events[0].event == "job_update"


class TestEmitInitialSnapshot:
    """Tests for _emit_initial_snapshot function."""

    @pytest.mark.asyncio
    async def test_emit_initial_snapshot_returns_empty_on_no_jobs(self):
        """Test that _emit_initial_snapshot returns empty list when no jobs exist."""
        from collections import OrderedDict

        from app.api.routes.sse import _emit_initial_snapshot

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_session_factory = MagicMock(return_value=mock_session)
        seen_initial = OrderedDict()

        events = await _emit_initial_snapshot(mock_session_factory, uuid.uuid4(), seen_initial)

        assert events == []
        assert len(seen_initial) == 0

    @pytest.mark.asyncio
    async def test_emit_initial_snapshot_returns_events_for_jobs(self):
        """Test that _emit_initial_snapshot returns ServerSentEvents for each job."""
        from collections import OrderedDict
        from datetime import UTC, datetime

        from app.api.routes.sse import _emit_initial_snapshot
        from app.models.download_job import DownloadJob

        mock_job1 = MagicMock(spec=DownloadJob)
        mock_job1.id = uuid.uuid4()
        mock_job1.url = "https://youtube.com/watch?v=test1"
        mock_job1.status = "pending"
        mock_job1.file_name = None
        mock_job1.error = None
        mock_job1.created_at = datetime.now(UTC)
        mock_job1.updated_at = datetime.now(UTC)

        mock_job2 = MagicMock(spec=DownloadJob)
        mock_job2.id = uuid.uuid4()
        mock_job2.url = "https://youtube.com/watch?v=test2"
        mock_job2.status = "completed"
        mock_job2.file_name = "video.mp4"
        mock_job2.error = None
        mock_job2.created_at = datetime.now(UTC)
        mock_job2.updated_at = datetime.now(UTC)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_job1, mock_job2]

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_session_factory = MagicMock(return_value=mock_session)
        seen_initial = OrderedDict()

        events = await _emit_initial_snapshot(mock_session_factory, uuid.uuid4(), seen_initial)

        assert len(events) == 2
        assert events[0].event == "job_update"
        assert events[1].event == "job_update"
        # Both jobs should be in seen_initial
        assert len(seen_initial) == 2
        assert str(mock_job1.id) in seen_initial
        assert str(mock_job2.id) in seen_initial

    @pytest.mark.asyncio
    async def test_emit_initial_snapshot_handles_db_exception(self):
        """Test that _emit_initial_snapshot returns empty list on DB error."""
        from collections import OrderedDict

        from app.api.routes.sse import _emit_initial_snapshot

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(side_effect=Exception("DB connection error"))
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_session_factory = MagicMock(return_value=mock_session)
        seen_initial = OrderedDict()

        # Should not raise, should return empty list
        events = await _emit_initial_snapshot(mock_session_factory, uuid.uuid4(), seen_initial)

        assert events == []

    @pytest.mark.asyncio
    async def test_emit_initial_snapshot_populates_seen_initial_correctly(self):
        """Test that _emit_initial_snapshot populates seen_initial with job_id:updated_at keys."""
        from collections import OrderedDict
        from datetime import UTC, datetime

        from app.api.routes.sse import _emit_initial_snapshot
        from app.models.download_job import DownloadJob

        job_id = uuid.uuid4()
        updated_at = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)

        mock_job = MagicMock(spec=DownloadJob)
        mock_job.id = job_id
        mock_job.url = "https://youtube.com/watch?v=abc"
        mock_job.status = "processing"
        mock_job.file_name = None
        mock_job.error = None
        mock_job.created_at = datetime.now(UTC)
        mock_job.updated_at = updated_at

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_job]

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_session_factory = MagicMock(return_value=mock_session)
        seen_initial = OrderedDict()

        await _emit_initial_snapshot(mock_session_factory, uuid.uuid4(), seen_initial)

        # Key should be job_id_str, value should be "job_id:updated_at_iso"
        assert str(job_id) in seen_initial
        expected_status_key = f"{job_id}:{updated_at.isoformat()}"
        assert seen_initial[str(job_id)] == expected_status_key

    @pytest.mark.asyncio
    async def test_emit_initial_snapshot_job_with_none_updated_at(self):
        """Test that _emit_initial_snapshot handles jobs with None updated_at."""
        from collections import OrderedDict
        from datetime import UTC, datetime

        from app.api.routes.sse import _emit_initial_snapshot
        from app.models.download_job import DownloadJob

        job_id = uuid.uuid4()

        mock_job = MagicMock(spec=DownloadJob)
        mock_job.id = job_id
        mock_job.url = "https://youtube.com/watch?v=abc"
        mock_job.status = "pending"
        mock_job.file_name = None
        mock_job.error = None
        mock_job.created_at = datetime.now(UTC)
        mock_job.updated_at = None  # None updated_at

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_job]

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_session_factory = MagicMock(return_value=mock_session)
        seen_initial = OrderedDict()

        events = await _emit_initial_snapshot(mock_session_factory, uuid.uuid4(), seen_initial)

        assert len(events) == 1
        # Status key should use None for updated_at
        expected_key = f"{job_id}:None"
        assert seen_initial[str(job_id)] == expected_key


class TestReplayBufferedEvents:
    """Tests for _replay_buffered_events function."""

    @pytest.mark.asyncio
    async def test_replay_buffered_events_yields_new_events(self):
        """Test that _replay_buffered_events yields events not in seen_initial."""
        from collections import OrderedDict

        from app.api.routes.sse import _replay_buffered_events

        job_id = str(uuid.uuid4())
        buffered_events = [
            {
                "key": f"{job_id}:2024-01-01T00:00:00",
                "data": {"id": job_id, "status": "processing", "updated_at": "2024-01-01T00:00:00"},
            }
        ]
        seen_initial = OrderedDict()

        events = []
        async for event in _replay_buffered_events(buffered_events, seen_initial):
            events.append(event)

        assert len(events) == 1
        assert events[0].event == "job_update"

    @pytest.mark.asyncio
    async def test_replay_buffered_events_skips_already_seen(self):
        """Test that _replay_buffered_events skips events already in seen_initial."""
        from collections import OrderedDict

        from app.api.routes.sse import _replay_buffered_events

        job_id = str(uuid.uuid4())
        status_key = f"{job_id}:2024-01-01T00:00:00"

        buffered_events = [
            {"key": status_key, "data": {"id": job_id, "status": "processing"}},
        ]

        # Already in seen_initial
        seen_initial = OrderedDict()
        seen_initial[job_id] = status_key

        events = []
        async for event in _replay_buffered_events(buffered_events, seen_initial):
            events.append(event)

        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_replay_buffered_events_skips_missing_job_id(self):
        """Test that _replay_buffered_events skips events with no job_id."""
        from collections import OrderedDict

        from app.api.routes.sse import _replay_buffered_events

        buffered_events = [
            {
                "key": "some-key",
                "data": {"status": "processing"},  # No "id" field
            }
        ]
        seen_initial = OrderedDict()

        events = []
        async for event in _replay_buffered_events(buffered_events, seen_initial):
            events.append(event)

        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_replay_buffered_events_respects_max_seen_jobs(self):
        """Test that _replay_buffered_events trims seen_initial to MAX_SEEN_JOBS."""
        from collections import OrderedDict

        from app.api.routes.sse import MAX_SEEN_JOBS, _replay_buffered_events

        # Pre-fill seen_initial to just below max
        seen_initial = OrderedDict()
        for i in range(MAX_SEEN_JOBS):
            seen_initial[str(uuid.uuid4())] = f"key:{i}"

        # Add one more buffered event that should trigger trim
        new_job_id = str(uuid.uuid4())
        buffered_events = [
            {
                "key": f"{new_job_id}:2024-01-01T00:00:00",
                "data": {"id": new_job_id, "status": "pending"},
            }
        ]

        events = []
        async for event in _replay_buffered_events(buffered_events, seen_initial):
            events.append(event)

        # Should still yield the event
        assert len(events) == 1
        # seen_initial should not exceed MAX_SEEN_JOBS
        assert len(seen_initial) <= MAX_SEEN_JOBS

    @pytest.mark.asyncio
    async def test_replay_buffered_events_empty_buffer(self):
        """Test that _replay_buffered_events handles empty buffered events."""
        from collections import OrderedDict

        from app.api.routes.sse import _replay_buffered_events

        buffered_events = []
        seen_initial = OrderedDict()

        events = []
        async for event in _replay_buffered_events(buffered_events, seen_initial):
            events.append(event)

        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_replay_buffered_events_adds_to_seen_initial(self):
        """Test that _replay_buffered_events updates seen_initial for yielded events."""
        from collections import OrderedDict

        from app.api.routes.sse import _replay_buffered_events

        job_id = str(uuid.uuid4())
        status_key = f"{job_id}:2024-01-01T00:00:00"
        buffered_events = [
            {"key": status_key, "data": {"id": job_id, "status": "processing"}},
        ]
        seen_initial = OrderedDict()

        async for _ in _replay_buffered_events(buffered_events, seen_initial):
            pass

        # The job_id should now be in seen_initial
        assert job_id in seen_initial
        assert seen_initial[job_id] == status_key


class TestSubscribeToPubsubEdgeCases:
    """Additional edge case tests for _subscribe_to_pubsub."""

    @pytest.mark.asyncio
    async def test_subscribe_to_pubsub_skips_messages_without_job_id(self):
        """Test that _subscribe_to_pubsub skips messages missing the id field."""
        from collections import OrderedDict

        from app.api.routes.sse import _subscribe_to_pubsub

        pubsub_messages = [
            {"status": "processing"},  # No "id" field
            {"id": None, "status": "completed"},  # id is None
        ]

        async def mock_subscribe(user_id):
            for msg in pubsub_messages:
                yield msg

        mock_pubsub = MagicMock()
        mock_pubsub.subscribe = mock_subscribe

        last_seen = OrderedDict()
        events = []
        async for event in _subscribe_to_pubsub(mock_pubsub, uuid.uuid4(), last_seen):
            events.append(event)

        # Both should be skipped (no valid id)
        assert len(events) == 0

    @pytest.mark.asyncio
    async def test_subscribe_to_pubsub_respects_max_seen_jobs(self):
        """Test that _subscribe_to_pubsub trims last_seen to MAX_SEEN_JOBS."""
        from collections import OrderedDict

        from app.api.routes.sse import MAX_SEEN_JOBS, _subscribe_to_pubsub

        # Pre-fill last_seen to the max
        last_seen = OrderedDict()
        for i in range(MAX_SEEN_JOBS):
            last_seen[str(uuid.uuid4())] = f"key:{i}"

        new_job_id = str(uuid.uuid4())
        pubsub_messages = [
            {"id": new_job_id, "status": "pending", "updated_at": "2024-01-01T00:00:00"},
        ]

        async def mock_subscribe(user_id):
            for msg in pubsub_messages:
                yield msg

        mock_pubsub = MagicMock()
        mock_pubsub.subscribe = mock_subscribe

        events = []
        async for event in _subscribe_to_pubsub(mock_pubsub, uuid.uuid4(), last_seen):
            events.append(event)

        # Should yield the event and trim last_seen
        assert len(events) == 1
        assert len(last_seen) <= MAX_SEEN_JOBS


class TestFallbackPollingGeneratorEdgeCases:
    """Additional edge case tests for fallback_polling_generator."""

    @pytest.mark.asyncio
    async def test_fallback_polling_reuses_request_state_seen_jobs(self):
        """Test that fallback_polling_generator reuses existing request.state.seen_jobs."""
        from collections import OrderedDict
        from datetime import UTC, datetime

        from app.api.routes.sse import fallback_polling_generator
        from app.models.download_job import DownloadJob

        mock_request = MagicMock()
        mock_request.is_disconnected = AsyncMock(side_effect=[False, True])

        # Pre-existing seen_jobs in request.state
        existing_seen_jobs = OrderedDict()
        mock_request.state.seen_jobs = existing_seen_jobs

        job_id = uuid.uuid4()
        mock_job = MagicMock(spec=DownloadJob)
        mock_job.id = job_id
        mock_job.url = "https://youtube.com/watch?v=test"
        mock_job.status = "pending"
        mock_job.file_name = None
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

        with patch("app.api.routes.sse.POLL_INTERVAL_SECONDS", 0):
            events = []
            async for event in fallback_polling_generator(
                mock_request, mock_session_factory, uuid.uuid4()
            ):
                events.append(event)
                if len(events) >= 1:
                    break

        # The same existing_seen_jobs dict should have been used and populated
        assert len(existing_seen_jobs) >= 1

    @pytest.mark.asyncio
    async def test_fallback_polling_deduplicates_same_status(self):
        """Test that fallback_polling_generator deduplicates jobs with unchanged status."""
        from collections import OrderedDict
        from datetime import UTC, datetime

        from app.api.routes.sse import fallback_polling_generator
        from app.models.download_job import DownloadJob

        mock_request = MagicMock()
        mock_request.is_disconnected = AsyncMock(side_effect=[False, False, True])
        mock_request.state = MagicMock()
        mock_request.state.seen_jobs = None
        mock_request.state.__bool__ = lambda self: False

        fixed_time = datetime.now(UTC)
        job_id = uuid.uuid4()
        mock_job = MagicMock(spec=DownloadJob)
        mock_job.id = job_id
        mock_job.url = "https://youtube.com/watch?v=test"
        mock_job.status = "pending"
        mock_job.file_name = None
        mock_job.error = None
        mock_job.created_at = fixed_time
        mock_job.updated_at = fixed_time

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_job]

        mock_session = MagicMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock()

        mock_session_factory = MagicMock(return_value=mock_session)

        with patch("app.api.routes.sse.POLL_INTERVAL_SECONDS", 0):
            events = []
            async for event in fallback_polling_generator(
                mock_request, mock_session_factory, uuid.uuid4()
            ):
                events.append(event)

        # Despite 2 poll cycles, only 1 event since status didn't change
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_fallback_polling_generator_exit_handled(self):
        """Test that fallback_polling_generator handles GeneratorExit gracefully."""
        from app.api.routes.sse import fallback_polling_generator

        mock_request = MagicMock()

        async def is_disconnected_raise():
            raise GeneratorExit

        mock_request.is_disconnected = is_disconnected_raise
        mock_request.state = MagicMock()
        mock_request.state.seen_jobs = None

        mock_session_factory = MagicMock()

        events = []
        try:
            async for event in fallback_polling_generator(
                mock_request, mock_session_factory, uuid.uuid4()
            ):
                events.append(event)
        except GeneratorExit:
            pass  # May propagate depending on where GeneratorExit is raised

        # No events should be yielded
        assert len(events) == 0


class TestPubsubEventGeneratorWithExistingSeenIds:
    """Tests for pubsub_event_generator with pre-populated last_seen_job_ids."""

    @pytest.mark.asyncio
    async def test_pubsub_event_generator_with_initial_seen_ids(self):
        """Test that pubsub_event_generator uses passed-in last_seen_job_ids dict."""
        from collections import OrderedDict

        from app.api.routes.sse import pubsub_event_generator

        mock_request = MagicMock()
        mock_request.is_disconnected = AsyncMock(return_value=False)

        job_id = str(uuid.uuid4())
        # Pre-populate with a different version of the job (old timestamp)
        existing_seen_ids = OrderedDict()
        existing_seen_ids[job_id] = f"{job_id}:2024-01-01T00:00:00"

        # New message with a newer timestamp
        pubsub_messages = [
            {"id": job_id, "status": "completed", "updated_at": "2024-01-02T00:00:00"},
        ]

        async def mock_subscribe(user_id):
            for msg in pubsub_messages:
                yield msg

        mock_pubsub_service = MagicMock()
        mock_pubsub_service.subscribe = mock_subscribe

        with patch("app.api.routes.sse.get_pubsub_service", return_value=mock_pubsub_service):
            events = []
            async for event in pubsub_event_generator(mock_request, uuid.uuid4(), existing_seen_ids):
                events.append(event)

        # Should yield the new event since the timestamp changed
        assert len(events) == 1

    @pytest.mark.asyncio
    async def test_pubsub_event_generator_skips_already_seen_ids(self):
        """Test that pubsub_event_generator skips events already in last_seen_job_ids."""
        from collections import OrderedDict

        from app.api.routes.sse import pubsub_event_generator

        mock_request = MagicMock()
        mock_request.is_disconnected = AsyncMock(return_value=False)

        job_id = str(uuid.uuid4())
        timestamp = "2024-01-01T00:00:00"
        # Pre-populate with exactly the same version
        existing_seen_ids = OrderedDict()
        existing_seen_ids[job_id] = f"{job_id}:{timestamp}"

        # Same message - should be deduplicated
        pubsub_messages = [
            {"id": job_id, "status": "completed", "updated_at": timestamp},
        ]

        async def mock_subscribe(user_id):
            for msg in pubsub_messages:
                yield msg

        mock_pubsub_service = MagicMock()
        mock_pubsub_service.subscribe = mock_subscribe

        with patch("app.api.routes.sse.get_pubsub_service", return_value=mock_pubsub_service):
            events = []
            async for event in pubsub_event_generator(mock_request, uuid.uuid4(), existing_seen_ids):
                events.append(event)

        # Should be skipped since it's already in seen_ids
        assert len(events) == 0
