#!/usr/bin/env bash
set -euo pipefail

# Worker entrypoint that runs database migrations then starts the worker
echo "Running database migrations..."
python -m alembic upgrade head

echo "Starting worker..."
exec python -m worker.main