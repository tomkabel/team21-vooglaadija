#!/bin/bash
set -e

# Ensure storage directories exist and are owned by appuser
# This is necessary because Docker volumes are mounted with root ownership
echo "Setting up storage directories..."
mkdir -p /app/storage/downloads /app/storage/temp
chown -R appuser:appuser /app/storage

echo "Running database migrations..."
su -s /bin/sh appuser -c "python -m alembic upgrade head"

echo "Starting application..."
exec su -s /bin/sh appuser -c "$*"
