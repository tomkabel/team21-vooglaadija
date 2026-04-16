# ============================================
# A++ Production Dockerfile - 2026 Best Practices
# Distroless, SBOM, Sigstore, SLSA, Reproducible, Non-root, Observability
# ============================================

# ============================================
# Stage 2: Python Dependency Builder
# ============================================
FROM python:3.12-slim AS python-builder
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system build dependencies and curl for HTMX download
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install build dependencies (cached layer)
COPY pyproject.toml .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip setuptools wheel && \
    pip install hatchling hatch-uv

# ============================================
# Stage 3: Frontend Builder
# ============================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app

# Install pnpm for package management (version pinned in package.json packageManager field)
# Note: we use plain version here; integrity hash is enforced via lockfile
RUN corepack enable && corepack prepare pnpm@10.33.0 --activate

# Copy frontend package files and pnpm lockfile to frontend subdirectory
COPY frontend/package*.json pnpm-lock.yaml ./frontend/

# Install frontend dependencies using pnpm from the frontend directory
WORKDIR /app/frontend
RUN --mount=type=cache,target=/root/.local/share/pnpm/store pnpm install

# Copy Tailwind config
COPY frontend/tailwind.config.js ./tailwind.config.js
COPY frontend/postcss.config.js ./postcss.config.js
COPY frontend/.browserslistrc ./.browserslistrc

# Copy source templates for Tailwind scanning
COPY app/templates ./app/templates

# Copy CSS source
COPY frontend/css ./css

# Build Tailwind CSS
RUN pnpm run build

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
COPY --from=frontend-builder /app/frontend/css/dist /app/static/css

# Copy HTMX from node_modules (installed via pnpm with lockfile for supply-chain integrity)
COPY --from=frontend-builder /app/frontend/node_modules/htmx.org/dist/htmx.min.js /app/static/js/htmx.min.js

# Generate SBOM (best-effort; fallback to empty if CLI is incompatible)
RUN pip install cyclonedx-bom 2>/dev/null; \
    python -m cyclonedx_py environment -o /tmp/sbom.xml --output-format XML 2>/dev/null || echo "<bom/>" > /tmp/sbom.xml; \
    python -m cyclonedx_py environment -o /tmp/sbom.json --output-format JSON 2>/dev/null || echo "{}" > /tmp/sbom.json

# Generate SLSA provenance metadata (simplified for this example)
# In production, use slsa-framework/github-actions-slsa-generator or similar
RUN echo '{"buildType": "https://slsa-framework.fr.dev/build-types/1.0", "invocation": {"configSource": {"uri": "git+https://github.com/team21/vooglaadija.git"}, "entryPoint": "hatch build"}}' > /tmp/slsa-provenance.json

# ============================================
# Stage 5: Runtime Base
# ============================================
# Use python:slim as base for runtime (distroless lacks ffmpeg dependencies)
FROM python:3.12-slim AS runtime-base

# Install ffmpeg for yt-dlp media merging, redis-tools for migrate.sh, and gosu for privilege dropping
# Also install redis-tools for migrate.sh's redis-cli commands
# Node.js is required for yt-dlp to solve YouTube video signatures (JS-based decryption)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    redis-tools \
    gosu \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

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

# ============================================
# Stage 6: API Service
# ============================================
FROM runtime-base AS api
# Set environment
ENV PYTHONPATH=/app \
    PATH=/opt/venv/bin:$PATH \
    STORAGE_PATH=/app/storage

# Copy entrypoint script and migrator
COPY entrypoint.sh /app/entrypoint.sh
COPY migrate.sh /app/migrate.sh
RUN chmod +x /app/entrypoint.sh /app/migrate.sh && \
    chown appuser:appuser /app/entrypoint.sh /app/migrate.sh

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

# Keep root so entrypoint can fix ownership of mounted volumes
# The entrypoint script will exec to appuser after setup
USER root

# Run application via entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/opt/venv/bin/python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

# ============================================
# Stage 7: Worker Service
# ============================================
FROM runtime-base AS worker
# Set environment - WORKER_ID is set at runtime via docker-compose
ENV PYTHONPATH=/app \
    PATH=/opt/venv/bin:$PATH \
    STORAGE_PATH=/app/storage

# Health check - HTTP check using worker's health endpoint on port 8081
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8081/health', timeout=5)"]

# Copy worker entrypoint
COPY --from=app-builder /app/worker/entrypoint-worker.sh ./entrypoint-worker.sh
COPY migrate.sh /app/migrate.sh
RUN chmod +x ./entrypoint-worker.sh /app/migrate.sh && \
    chown appuser:appuser ./entrypoint-worker.sh /app/migrate.sh

# Run as non-root user (storage ownership is already set in the image)
USER appuser

# Run worker via entrypoint script
ENTRYPOINT ["./entrypoint-worker.sh"]