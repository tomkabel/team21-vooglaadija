#!/usr/bin/env bash
set -euo pipefail

# Worker entrypoint that runs migrations with lock then starts the worker
echo "Running database migrations..."
/app/migrate.sh

echo "Starting worker..."
exec python -m worker.main