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
exec su -s /bin/sh appuser -c "python -m worker.main"