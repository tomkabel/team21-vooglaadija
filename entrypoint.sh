#!/bin/bash
set -e

# Ensure storage directories exist
# The container runs as non-root user (UID 1000), so we can create directories directly
echo "Setting up storage directories..."
mkdir -p /app/storage/downloads /app/storage/temp

# Run migrations with distributed lock to prevent concurrent runs
/app/migrate.sh

echo "Starting application..."
exec "$@"
