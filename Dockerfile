# ============================================
# Multi-stage build for API container
# Optimized: standard install, ffmpeg, [server] extras
# ============================================
FROM python:3.12-slim AS builder

# Set environment variables for best practices
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system dependencies including ffmpeg for yt-dlp
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install uv first (separate layer for caching)
RUN pip install --no-cache-dir uv

# Create virtual environment
RUN uv venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy only pyproject.toml first for better layer caching
COPY pyproject.toml .

# Install the package with server extras (non-editable)
# This installs all dependencies defined in [project] and [project.optional-dependencies] server
COPY app ./app
COPY worker ./worker
COPY alembic.ini .
COPY alembic ./alembic
RUN uv pip install ".[server]"

# ============================================
# Production stage
# ============================================
FROM python:3.12-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1

WORKDIR /app

# Install ffmpeg in production stage (required for yt-dlp video processing)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application source
COPY --from=builder /app/app ./app
COPY --from=builder /app/worker ./worker
COPY --from=builder /app/pyproject.toml ./pyproject.toml
COPY --from=builder /app/alembic.ini ./alembic.ini
COPY --from=builder /app/alembic ./alembic

# Copy entrypoint script
COPY entrypoint.sh ./entrypoint.sh
RUN chmod +x ./entrypoint.sh

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# NOTE: Not switching to USER appuser here — entrypoint.sh runs as root
# to set up volume permissions, then drops to appuser via su-exec.

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Run with entrypoint (migrations + uvicorn)
ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
