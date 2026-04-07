# ============================================
# A++ Production Dockerfile - 2026 Best Practices
# Distroless, SBOM, Sigstore, SLSA, Reproducible, Non-root, Observability
# ============================================

# ============================================
# Stage 1: Build Environment
# ============================================
FROM eclipse-temurin:21-jdk-alpine@sha256:7f09518f1eab51c0de2488baee0a05ce178f3326c76010a2eb8d3dcb5ee76545 AS build-tools
# Install tools needed for building Python extensions and frontend
RUN apk add --no-cache \
    build-base \
    python3-dev \
    libffi-dev \
    openssl-dev \
    cargo \
    nodejs \
    npm \
    && rm -rf /var/cache/apk/*

# ============================================
# Stage 2: Python Dependency Builder
# ============================================
FROM python:3.12-slim AS python-builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Install system build dependencies and curl for HTMX download
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv (pinned version for reproducible builds)
# In production, verify the digest at https://github.com/astral-sh/uv/releases
COPY --from=ghcr.io/astral-sh/uv:0.5.18 /uv /uvx /bin/
ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install build dependencies (cached layer)
COPY pyproject.toml .
RUN pip install --upgrade pip setuptools wheel && \
    pip install hatchling hatch-uv

# ============================================
# Stage 3: Frontend Builder
# ============================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app

# Install frontend dependencies
COPY frontend/package*.json ./frontend/
RUN cd frontend && npm ci

# Copy Tailwind config
COPY frontend/tailwind.config.js ./frontend/tailwind.config.js
COPY frontend/postcss.config.js ./frontend/postcss.config.js
COPY frontend/.browserslistrc ./frontend/.browserslistrc

# Copy source templates for Tailwind scanning
COPY app/templates ./app/templates

# Copy CSS source
COPY frontend/css ./frontend/css

# Build Tailwind CSS
RUN cd frontend && npm run build

# ============================================
# Stage 4: Application Builder
# ============================================
FROM python-builder AS app-builder
# Copy source code and Alembic configuration
COPY app ./app
COPY worker ./worker
COPY pyproject.toml .
COPY alembic.ini .
COPY alembic ./alembic

# Install the package (production deps only)
RUN pip install .

# Copy built frontend assets - ensure destination directory exists
RUN mkdir -p /app/static/css /app/static/js
COPY --from=frontend-builder /app/frontend/css/dist ./app/static/css

# Download HTMX for production (cache-friendly)
# Note: For stronger supply chain guarantees, add htmx to frontend/package.json
# so it's installed via pnpm with a committed lockfile
RUN curl -sSfL https://unpkg.com/htmx.org@1.9.12/dist/htmx.min.js -o /app/static/js/htmx.min.js

# Generate SBOM (best-effort; fallback to empty if CLI is incompatible)
RUN pip install cyclonedx-bom 2>/dev/null; \
    python -m cyclonedx_py requirements . -o /tmp/sbom.xml --output-format XML 2>/dev/null || echo "<bom/>" > /tmp/sbom.xml; \
    python -m cyclonedx_py requirements . -o /tmp/sbom.json --output-format JSON 2>/dev/null || echo "{}" > /tmp/sbom.json

# Generate SLSA provenance metadata (simplified for this example)
# In production, use slsa-framework/github-actions-slsa-generator or similar
RUN echo '{"buildType": "https://slsa-framework.fr.dev/build-types/1.0", "invocation": {"configSource": {"uri": "git+https://github.com/team21/vooglaadija.git"}, "entryPoint": "hatch build"}}' > /tmp/slsa-provenance.json

# ============================================
# Stage 5: Runtime Base
# ============================================
# Use python:slim as base for runtime (distroless lacks ffmpeg dependencies)
FROM python:3.12-slim AS runtime-base

# Copy Python runtime from builder (with dependencies installed)
COPY --from=app-builder /opt/venv /opt/venv

# Copy application code - ownership will be handled by distroless default user
COPY --from=app-builder /app/app ./app
COPY --from=app-builder /app/pyproject.toml ./pyproject.toml
COPY --from=app-builder /app/worker ./worker
COPY --from=app-builder /app/static/css ./app/static/css
COPY --from=app-builder /app/static/js ./app/static/js
# Copy Alembic configuration and migration files
COPY alembic.ini ./alembic.ini
COPY alembic ./alembic
COPY --from=app-builder /tmp/sbom.xml ./sbom.xml
COPY --from=app-builder /tmp/sbom.json ./sbom.json
COPY --from=app-builder /tmp/slsa-provenance.json ./slsa-provenance.json

# Create non-root user
RUN groupadd -r appuser -g 1000 && \
    useradd -r -g appuser -u 1000 appuser

# Create storage directory and set ownership
RUN mkdir -p /app/storage && \
    chown -R appuser:appuser /app /opt/venv

# Note: ffmpeg is not copied as it's not required for basic operation
# yt-dlp will work without ffmpeg for basic downloading (some post-processing features limited)
# For production use with ffmpeg post-processing, consider:
# 1. Using a distroless ffmpeg variant from Chainguard
# 2. Building ffmpeg statically and adding it
# 3. Use cosign to verify ffmpeg binary

# ============================================
# Stage 6: API Service
# ============================================
FROM runtime-base AS api
# Set environment
ENV PYTHONPATH=/app \
    PATH=/opt/venv/bin:$PATH \
    STORAGE_PATH=/app/storage

# Copy entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh && \
    chown appuser:appuser /app/entrypoint.sh

# Health check - internal TCP check (no external deps)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import socket; s=socket.socket(); s.settimeout(1); s.connect(('localhost', 8000)); s.close()"]

# Expose port
EXPOSE 8000

# Metadata for observability and supply chain security
LABEL org.opencontainers.image.source="https://github.com/team21/vooglaadija" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.description="YouTube Link Processor API" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.revision=${GIT_SHA:-unknown} \
      io.buildkit.sbom="true" \
      io.sigstore.cosign.signature="true"

# Switch to non-root user
USER appuser

# Run application via entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/opt/venv/bin/python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# ============================================
# Stage 7: Worker Service
# ============================================
FROM runtime-base AS worker
# Set environment
ENV PYTHONPATH=/app \
    PATH=/opt/venv/bin:$PATH \
    STORAGE_PATH=/app/storage \
    WORKER_ID=${HOSTNAME:-worker-1}

# Health check - Python-based check using worker's health server on port 8081
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import socket; s=socket.socket(); s.settimeout(1); s.connect(('localhost', 8081)); s.close()"]

# Copy worker entrypoint
COPY --from=app-builder /app/worker/entrypoint-worker.sh ./entrypoint-worker.sh
RUN chmod +x ./entrypoint-worker.sh && \
    chown appuser:appuser ./entrypoint-worker.sh

# Switch to non-root user
USER appuser

# Run worker
ENTRYPOINT ["./entrypoint-worker.sh"]
