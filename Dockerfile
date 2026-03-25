# ============================================
# Multi-stage build for API container
# ============================================
FROM python:3.12-slim AS builder

# Set environment variables for best practices
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# Copy application source first
COPY app ./app
COPY worker ./worker

# Install uv for fast dependency management
RUN pip install uv

# Copy only dependency files first for better layer caching
COPY pyproject.toml pyproject.toml

# Pre-install dependencies layer - use uv for speed
# Install in a virtual environment for cleaner separation
RUN uv venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
RUN uv pip install -e .

# ============================================
# Production stage
# ============================================
FROM python:3.12-slim AS production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application source
COPY --from=builder /app/app ./app
COPY --from=builder /app/pyproject.toml ./pyproject.toml

# Create non-root user for security
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health')" || exit 1

# Run with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
