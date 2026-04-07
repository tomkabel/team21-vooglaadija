#!/bin/bash
set -e

# Migrator script that uses Redis lock to ensure migrations run only once
# Usage: ./migrate.sh

REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"
REDISCLI_AUTH="${REDIS_PASSWORD}"  # Use env var for password to avoid -a flag
MIGRATION_LOCK_KEY="vooglaadija:migration:lock"
MIGRATION_LOCK_TIMEOUT=60

acquire_lock() {
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" SET "$MIGRATION_LOCK_KEY" "$$" NX EX "$MIGRATION_LOCK_TIMEOUT"
}

release_lock() {
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" SET "$MIGRATION_LOCK_KEY" "done" EX 300
}

wait_for_lock_release() {
    max_wait=120
    waited=0
    while [ $waited -lt $max_wait ]; do
        holder=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" GET "$MIGRATION_LOCK_KEY" 2>/dev/null)
        
        if [ -z "$holder" ] || [ "$holder" = "done" ]; then
            return 0
        fi
        
        echo "Waiting for migration lock to be released by PID $holder..."
        sleep 2
        waited=$((waited + 2))
    done
    
    echo "Timeout waiting for migration lock"
    return 1
}

echo "Running database migrations..."

# Try to acquire lock
lock_result=$(acquire_lock)
if [ "$lock_result" = "OK" ]; then
    echo "Acquired migration lock, running migrations..."
    
    # Register trap to release lock on EXIT/ERR - only if we acquired the lock
    trap 'release_lock' EXIT ERR
    
    python -m alembic upgrade head
    echo "Migrations completed successfully"
    
    # Release lock
    release_lock
    
    # Remove trap since we already released
    trap - EXIT ERR
else
    echo "Migration lock held by another process, waiting..."
    wait_for_lock_release
    
    # Check if migrations already ran (by trying to get current version)
    current=$(python -m alembic current 2>/dev/null)
    if [ -n "$current" ]; then
        echo "Migrations already applied (current: $current)"
    else
        echo "Warning: Could not verify migration status"
    fi
fi

echo "Migration check complete"
