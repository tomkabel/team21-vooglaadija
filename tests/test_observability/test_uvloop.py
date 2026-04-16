"""Tests for uvloop event loop performance."""

import asyncio
import sys

import pytest

pytestmark = pytest.mark.skipif(
    sys.platform == "win32",
    reason="uvloop is not available on Windows",
)


class TestUvloopAvailability:
    """Test uvloop availability and configuration."""

    def test_uvloop_importable(self):
        """Test that uvloop can be imported."""
        import uvloop

        assert uvloop is not None

    def test_uvloop_install(self):
        """Test that uvloop can be installed as event loop policy."""
        import uvloop

        # Should not raise
        uvloop.install()

    def test_uvloop_new_event_loop(self):
        """Test that uvloop can create a new event loop."""
        import uvloop

        loop = uvloop.new_event_loop()
        assert loop is not None
        loop.close()


class TestUvloopAsyncPerformance:
    """Test uvloop performance with async operations."""

    @pytest.mark.asyncio
    async def test_rapid_async_tasks(self):
        """Test handling many rapid async tasks."""
        import uvloop

        uvloop.install()

        tasks = []
        for i in range(100):
            tasks.append(asyncio.create_task(asyncio.sleep(0.001)))

        await asyncio.gather(*tasks)

    @pytest.mark.asyncio
    async def test_async_queue_throughput(self):
        """Test async queue throughput with uvloop."""
        import uvloop

        uvloop.install()

        queue = asyncio.Queue()

        async def producer():
            for i in range(100):
                await queue.put(i)

        async def consumer():
            count = 0
            while count < 100:
                await queue.get()
                count += 1

        await asyncio.gather(producer(), consumer())
