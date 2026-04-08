#!/usr/bin/env bash
set -euo pipefail

# Fix ownership of storage directory (needed when volume is mounted from host as root)
echo "Ensuring storage directory ownership..."
chown -R appuser:appuser /app/storage 2>/dev/null || true

# Ensure non-root user can still access everything under /app
chown -R appuser:appuser /app 2>/dev/null || true

# Run migrations if not already done (check for alembic lock file)
if [ ! -f /app/.migrations_done ]; then
    echo "Running database migrations..."
    /app/migrate.sh || {
        echo "WARNING: Migration failed, continuing anyway..."
    }
    touch /app/.migrations_done
else
    echo "Migrations already completed, skipping..."
fi

echo "Starting worker..."
exec python -m worker.main