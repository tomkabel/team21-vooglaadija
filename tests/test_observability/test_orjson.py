"""Tests for ORJSON JSON serialization performance."""

import json
from typing import Any

import pytest

# ORJSON is installed as part of observability dependencies
orjson = pytest.importorskip("orjson", reason="orjson not installed")


class TestORJSONSerialization:
    """Test ORJSON serialization performance and correctness."""

    def test_orjson_dumps_bytes(self):
        """Test that orjson.dumps returns bytes."""
        data = {"key": "value", "number": 42}
        result = orjson.dumps(data)
        assert isinstance(result, bytes)

    def test_orjson_loads(self):
        """Test that orjson.loads works correctly."""
        data = {"key": "value", "number": 42}
        serialized = orjson.dumps(data)
        deserialized = orjson.loads(serialized)
        assert deserialized == data

    def test_orjson_dumps_none(self):
        """Test that orjson.dumps handles None."""
        result = orjson.dumps(None)
        assert result == b"null"

    def test_orjson_dumps_unicode(self):
        """Test that orjson.dumps handles unicode correctly."""
        data = {"emoji": "🎉", "unicode": "日本語"}
        result = orjson.dumps(data)
        deserialized = orjson.loads(result)
        assert deserialized == data

    def test_orjson_dumps_datetime(self):
        """Test that orjson.dumps handles datetime objects."""
        from datetime import datetime, timezone

        data = {"timestamp": datetime(2026, 4, 15, 12, 0, 0, tzinfo=timezone.utc)}
        result = orjson.dumps(data)
        # orjson serializes datetime to ISO format by default
        assert b"2026-04-15" in result

    def test_orjson_dumps_uuid(self):
        """Test that orjson.dumps handles UUID objects."""
        import uuid

        data = {"id": uuid.uuid4()}
        result = orjson.dumps(data)
        deserialized = orjson.loads(result)
        assert "id" in deserialized


class TestORJSONPerformance:
    """Test ORJSON performance compared to stdlib json."""

    def test_orjson_faster_than_stdlib(self):
        """Test that ORJSON is faster than stdlib json for large data."""
        import time

        # Create test data
        data = {
            "users": [
                {
                    "id": i,
                    "name": f"User {i}",
                    "email": f"user{i}@example.com",
                    "items": list(range(10)),
                }
                for i in range(100)
            ]
        }

        # Benchmark stdlib json
        start = time.perf_counter()
        for _ in range(100):
            json.dumps(data)
        stdlib_time = time.perf_counter() - start

        # Benchmark orjson
        start = time.perf_counter()
        for _ in range(100):
            orjson.dumps(data)
        orjson_time = time.perf_counter() - start

        # ORJSON should be significantly faster
        assert orjson_time < stdlib_time, "ORJSON should be faster than stdlib json"


class TestORJSONEdgeCases:
    """Test ORJSON edge cases and error handling."""

    def test_orjson_raises_on_invalid_data(self):
        """Test that orjson.dumps raises on non-serializable data."""
        # Objects that can't be serialized
        class CustomObject:
            pass

        with pytest.raises(TypeError):
            orjson.dumps(CustomObject())

    def test_orjson_default_option(self):
        """Test orjson default parameter for custom serialization."""
        from datetime import datetime, timezone

        def serialize_datetime(obj: Any) -> str:
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError()

        data = {"timestamp": datetime(2026, 4, 15, tzinfo=timezone.utc)}
        result = orjson.dumps(data, default=serialize_datetime)
        assert b"2026-04-15" in result
