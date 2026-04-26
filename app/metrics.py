"""Prometheus metrics for the application."""

from prometheus_client import Counter, Gauge, Histogram, Info

APP_INFO = Info("ytprocessor", "YouTube media processor")

JOBS_CREATED = Counter(
    "ytprocessor_jobs_created_total",
    "Total number of download jobs created",
    ["status"],
)

JOBS_COMPLETED = Counter(
    "ytprocessor_jobs_completed_total",
    "Total number of download jobs completed",
    ["status"],
)

JOB_DURATION_SECONDS = Histogram(
    "ytprocessor_job_duration_seconds",
    "Time spent processing a job",
    buckets=[10, 30, 60, 120, 300, 600],
)

QUEUE_DEPTH = Gauge(
    "ytprocessor_queue_depth",
    "Number of jobs waiting in the queue",
)

OUTBOX_PENDING = Gauge(
    "ytprocessor_outbox_pending",
    "Number of pending outbox entries",
)

HTTP_REQUESTS = Counter(
    "ytprocessor_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION = Histogram(
    "ytprocessor_http_request_duration_seconds",
    "HTTP request duration",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
)

WORKER_STATUS = Gauge(
    "ytprocessor_worker_status",
    "Worker health status (1=healthy, 0=unhealthy)",
)

DOWNLOAD_SIZE_BYTES = Histogram(
    "ytprocessor_download_size_bytes",
    "Size of downloaded files in bytes",
    buckets=[1e6, 5e6, 10e6, 50e6, 100e6, 500e6],
)


def init_metrics() -> None:
    """Initialize application metrics."""
    APP_INFO.info({"version": "1.0.0", "service": "ytprocessor"})
