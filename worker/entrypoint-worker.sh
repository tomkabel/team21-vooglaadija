#!/usr/bin/env bash
set -euo pipefail

# Fix ownership of storage directory (needed when volume is mounted from host as root)
echo "Ensuring storage directory ownership..."
chown -R appuser:appuser /app/storage 2>/dev/null || true

# Ensure non-root user can still access everything under /app
chown -R appuser:appuser /app

echo "Running database migrations..."
/app/migrate.sh

echo "Starting worker as appuser..."
# Add some debugging to see if the worker starts
exec su -s /bin/sh appuser -c "echo 'Starting worker process...' && python -c 'import sys; print(f\"Python version: {sys.version}\"); import worker.main; print(\"Worker module imported successfully\")' && python -m worker.main"