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
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" "$@"
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

# Renew lock timeout while holding it - loops until lock is lost
renew_lock() {
    local sleep_interval=$((MIGRATION_LOCK_PX / 2 / 1000))  # Half of lock timeout in seconds
    while true; do
        # Check if we still own the lock
        current_holder=$(redis_cmd GET "$MIGRATION_LOCK_KEY" 2>/dev/null)
        if [ "$current_holder" != "$$" ]; then
            # Lock lost or different owner
            exit 0
        fi
        
        # Refresh the lock expiration
        result=$(redis_cmd EVAL "if redis.call('get', KEYS[1]) == ARGV[1] then return redis.call('pexpire', KEYS[1], ARGV[2]) else return 0 end" 1 "$MIGRATION_LOCK_KEY" "$$" "$MIGRATION_LOCK_PX")
        
        if [ "$result" != "1" ]; then
            # Failed to renew - lock lost
            exit 0
        fi
        
        sleep "$sleep_interval"
    done
}

wait_for_lock_release() {
    max_wait=120
    waited=0
    while [ $waited -lt $max_wait ]; do
        holder=$(redis_cmd GET "$MIGRATION_LOCK_KEY" 2>/dev/null)
        
        if [ -z "$holder" ]; then
            # Lock expired or released - try to acquire it ourselves
            echo "Lock released, attempting to acquire..."
            acquire_result=$(acquire_lock)
            if [ "$acquire_result" = "OK" ]; then
                echo "Successfully acquired migration lock"
                return 0  # We now own the lock
            fi
            # Someone else got it first - continue waiting
            echo "Lock acquired by another process, continuing to wait..."
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
    
    # Start lock renewal in background (continuous loop renewing every MIGRATION_LOCK_TIMEOUT/2 seconds)
    (
        while true; do
            sleep $((MIGRATION_LOCK_TIMEOUT / 2))
            renew_lock
        done
    ) &
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
        
        # Verify migrations are at head - treat as hard failure if not
        current=$(python -m alembic current 2>/dev/null | tr -d '[:space:]')
        head=$(python -m alembic heads 2>/dev/null | head -1 | awk '{print $1}' | tr -d '[:space:]')
        
        if [ "$current" = "$head" ]; then
            echo "Verified: migrations at head ($head)"
        else
            echo "ERROR: current ($current) does not match head ($head). Schema is out of date!"
            migrations_result=1
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
    
    # We now own the lock (wait_for_lock_release acquired it for us)
    # Run migrations with lock renewal and cleanup
    echo "Running migrations with acquired lock..."
    
    # Start lock renewal in background
    (
        renew_lock
    ) &
    RENEW_PID=$!
    
    # Register trap to release lock on EXIT
    trap 'kill $RENEW_PID 2>/dev/null; release_lock' EXIT
    
    python -m alembic upgrade head
    migrations_result=$?
    
    # Stop renewal background job
    kill $RENEW_PID 2>/dev/null
    wait $RENEW_PID 2>/dev/null || true
    
    if [ $migrations_result -eq 0 ]; then
        echo "Migrations completed successfully"
        
        # Verify migrations are at head - treat as hard failure if not
        current=$(python -m alembic current 2>/dev/null | tr -d '[:space:]')
        head=$(python -m alembic heads 2>/dev/null | head -1 | awk '{print $1}' | tr -d '[:space:]')
        
        if [ "$current" = "$head" ]; then
            echo "Verified: migrations at head ($head)"
        else
            echo "ERROR: current ($current) does not match head ($head). Schema is out of date!"
            migrations_result=1
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
fi

echo "Migration check complete"
