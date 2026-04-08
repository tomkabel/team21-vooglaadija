#!/bin/bash
set -e

# Ensure storage directories exist
# The container runs as non-root user (UID 1000), so we can create directories directly
echo "Setting up storage directories..."
mkdir -p /app/storage/downloads /app/storage/temp

# If running as root, fix ownership and drop privileges
if [ "$(id -u)" = "0" ]; then
    echo "Running as root - fixing storage ownership..."
    chown -R appuser:appuser /app/storage 2>/dev/null || true
    chown -R appuser:appuser /app 2>/dev/null || true
fi

# Run migrations with distributed lock to prevent concurrent runs
/app/migrate.sh

echo "Starting application..."
# If running as root, drop to appuser before exec
if [ "$(id -u)" = "0" ]; then
    exec gosu appuser "$@"
else
    exec "$@"
fi
