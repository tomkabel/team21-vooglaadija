"""Worker health monitoring via Redis heartbeat and HTTP health endpoint."""

import json
import logging
import os
import threading
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer

logger = logging.getLogger(__name__)

# Global state updated by the worker main loop
_worker_state = {
    "status": "starting",
    "last_heartbeat": None,
    "last_job_processed": None,
    "last_cleanup": None,
    "pid": os.getpid(),
}

_start_time = datetime.now(UTC)
_health_server = None


def update_worker_state(**kwargs):
    """Update worker state for health reporting."""
    _worker_state.update(kwargs)
    _worker_state["last_heartbeat"] = datetime.now(UTC).isoformat()


def get_redis_url() -> str:
    """Get Redis URL from environment."""
    return os.environ.get("REDIS_URL", "redis://localhost:6379")


def get_worker_id() -> str:
    """Get worker ID from environment or default."""
    return os.environ.get("WORKER_ID", "worker-1")


def write_health_sync() -> bool:
    """Write worker health (synchronous version for shell scripts)."""
    import redis

    redis_url = get_redis_url()
    worker_id = get_worker_id()

    health_data = {
        "worker_id": worker_id,
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "pid": os.getpid(),
    }

    r = redis.from_url(redis_url)
    r.setex(f"worker:health:{worker_id}", 30, json.dumps(health_data))
    r.close()
    return True


async def write_health_async() -> bool:
    """Write worker health (async version for use in worker loop)."""
    import redis.asyncio as aioredis

    redis_url = get_redis_url()
    worker_id = get_worker_id()

    health_data = {
        "worker_id": worker_id,
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "pid": os.getpid(),
    }

    try:
        client = aioredis.from_url(redis_url, decode_responses=True)
        await client.setex(f"worker:health:{worker_id}", 30, json.dumps(health_data))
        # aclose() was added in redis-py 5.0; fall back to close() for older versions
        if hasattr(client, "aclose"):
            await client.aclose()  # type: ignore[union-attr]
        else:
            await client.close()
        return True
    except Exception:
        return False


class _HealthHandler(BaseHTTPRequestHandler):
    """HTTP request handler for health checks."""

    def do_GET(self):
        if self.path == "/health":
            uptime = (datetime.now(UTC) - _start_time).total_seconds()
            # Clone worker state to avoid race conditions
            worker_status = _worker_state.get("status", "unknown")
            health_data = {
                **_worker_state,
                "uptime_seconds": round(uptime),
            }

            # Determine health status based on worker state and heartbeat
            last_hb = _worker_state.get("last_heartbeat")
            if worker_status == "running":
                # Worker is running, check heartbeat
                if last_hb:
                    last_hb_dt = datetime.fromisoformat(last_hb)
                    seconds_since_hb = (datetime.now(UTC) - last_hb_dt).total_seconds()
                    if seconds_since_hb > 120:
                        health_data["status"] = "unhealthy"
                        health_data["reason"] = "No heartbeat in over 120 seconds"
                else:
                    # No heartbeat yet but running - this is okay initially
                    pass
            elif worker_status == "starting":
                health_data["status"] = "starting"
            else:
                health_data["status"] = "unhealthy"
                health_data["reason"] = f"Worker status is {worker_status}"

            status_code = 200 if health_data["status"] in ("running", "starting") else 503

            self.send_response(status_code)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(health_data).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def start_health_server(port: int | None = None) -> HTTPServer | None:
    """Start the health check HTTP server in a background thread.

    Port is read from WORKER_HEALTH_PORT env var (default: 8081).
    Set WORKER_HEALTH_PORT=0 to disable.

    Returns the server instance (call server.shutdown() to stop).
    """
    global _health_server
    if _health_server is not None:
        return _health_server

    env_port = os.environ.get("WORKER_HEALTH_PORT", "8081")
    if port is None:
        port = int(env_port)

    if port == 0:
        logger.info("Worker health HTTP server disabled (WORKER_HEALTH_PORT=0)")
        return None

    _health_server = HTTPServer(("0.0.0.0", port), _HealthHandler)
    thread = threading.Thread(target=_health_server.serve_forever, daemon=True)
    thread.start()
    logger.info("Worker health server started on port %d", port)
    return _health_server


def stop_health_server():
    """Stop the health check HTTP server."""
    global _health_server
    if _health_server:
        _health_server.shutdown()
        _health_server = None


if __name__ == "__main__":
    import sys

    success = write_health_sync()
    sys.exit(0 if success else 1)
