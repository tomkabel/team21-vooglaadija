#!/bin/bash
set -e

# Migrator script that uses Redis lock to ensure migrations run only once
# Usage: ./migrate.sh

REDIS_HOST="${REDIS_HOST:-localhost}"
REDIS_PORT="${REDIS_PORT:-6379}"
REDIS_PASSWORD="${REDIS_PASSWORD:-}"
export REDISCLI_AUTH="${REDIS_PASSWORD}"  # Export for redis-cli to use
MIGRATION_LOCK_KEY="vooglaadija:migration:lock"
MIGRATION_LOCK_TIMEOUT=60
MIGRATION_LOCK_PX=60000  # 60 seconds in milliseconds for PX option

# Helper to build redis-cli command with optional auth
redis_cmd() {
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "${REDISCLI_AUTH:+-a $REDISCLI_AUTH}"
}

acquire_lock() {
    # Use PX for millisecond precision and return the result
    redis_cmd SET "$MIGRATION_LOCK_KEY" "$$" NX PX "$MIGRATION_LOCK_PX"
}

# Safe release: only delete if we own the lock (compare $$ to stored value)
release_lock() {
    # Use EVAL Lua script for atomic check-and-delete
    redis_cmd EVAL "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('del', KEYS[1]) else return 0 end" 1 "$MIGRATION_LOCK_KEY" "$$"
}

# Renew lock timeout while holding it (called periodically in background)
renew_lock() {
    redis_cmd EVAL "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('pexpire', KEYS[1], ARGV[2]) else return 0 end" 1 "$MIGRATION_LOCK_KEY" "$$" "$MIGRATION_LOCK_PX"
}

wait_for_lock_release() {
    max_wait=120
    waited=0
    while [ $waited -lt $max_wait ]; do
        holder=$(redis_cmd GET "$MIGRATION_LOCK_KEY" 2>/dev/null)
        
        if [ -z "$holder" ]; then
            # Lock expired or missing - try to re-acquire
            lock_result=$(acquire_lock)
            if [ "$lock_result" = "OK" ]; then
                echo "Lock expired and re-acquired"
                return 0
            fi
            # Someone else got it first, keep waiting
        elif [ "$holder" = "done" ]; then
            # Previous owner marked done - wait a bit more for actual deletion
            sleep 1
            waited=$((waited + 1))
            continue
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
    
    # Start lock renewal in background (renew every MIGRATION_LOCK_TIMEOUT/2 seconds)
    renew_lock &
    RENEW_PID=$!
    
    # Register trap to release lock on EXIT only (not ERR - don't mark done on failure)
    trap 'kill $RENEW_PID 2>/dev/null; release_lock' EXIT
    
    python -m alembic upgrade head
    migrations_result=$?
    
    # Stop renewal background job
    kill $RENEW_PID 2>/dev/null
    wait $RENEW_PID 2>/dev/null || true
    
    if [ $migrations_result -eq 0 ]; then
        echo "Migrations completed successfully"
        
        # Verify migrations are at head
        current=$(python -m alembic current 2>/dev/null | tr -d '[:space:]')
        head=$(python -m alembic heads 2>/dev/null | head -1 | awk '{print $1}' | tr -d '[:space:]')
        
        if [ "$current" = "$head" ]; then
            echo "Verified: migrations at head ($head)"
        else
            echo "Warning: current ($current) does not match head ($head)"
        fi
    else
        echo "Migration failed with exit code $migrations_result"
    fi
    
    # Release lock before exiting
    release_lock
    
    # Remove trap since we already released
    trap - EXIT
    
    # Exit with migration result
    exit $migrations_result
else
    echo "Migration lock held by another process, waiting..."
    wait_for_lock_release
    wait_result=$?
    
    if [ $wait_result -ne 0 ]; then
        echo "Failed to wait for lock release"
        exit 1
    fi
    
    # Check if migrations already ran
    current=$(python -m alembic current 2>/dev/null | tr -d '[:space:]')
    if [ -n "$current" ]; then
        head=$(python -m alembic heads 2>/dev/null | head -1 | awk '{print $1}' | tr -d '[:space:]')
        if [ "$current" = "$head" ]; then
            echo "Migrations already at head ($head)"
        else
            echo "Warning: current ($current) does not match head ($head)"
        fi
    else
        echo "Warning: Could not verify migration status"
    fi
fi

echo "Migration check complete"
