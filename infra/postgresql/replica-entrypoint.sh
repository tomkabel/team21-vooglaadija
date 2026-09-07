#!/bin/bash
# ============================================
# PostgreSQL Read Replica — standby bootstrap
# ============================================
# The official postgres image's own entrypoint only knows how to initialize
# a fresh *primary* (initdb). A physical streaming replica instead needs its
# data directory cloned from the primary with pg_basebackup before postgres
# ever starts. This script does that clone (idempotently — it only runs when
# PGDATA is empty) and then hands off to the image's normal entrypoint,
# which will find a populated data directory and just start postgres.
set -euo pipefail

PGDATA="${PGDATA:-/var/lib/postgresql/data}"
PRIMARY_HOST="${DB_HOST:-db}"
PRIMARY_PORT="${DB_PORT:-5432}"
: "${DB_REPLICATION_USER:?DB_REPLICATION_USER is required}"
: "${DB_REPLICATION_PASSWORD:?DB_REPLICATION_PASSWORD is required}"

if [ -z "$(ls -A "$PGDATA" 2>/dev/null)" ]; then
    echo "replica-entrypoint: PGDATA is empty, waiting for primary at ${PRIMARY_HOST}:${PRIMARY_PORT}..."
    until PGPASSWORD="$DB_REPLICATION_PASSWORD" pg_isready \
        -h "$PRIMARY_HOST" -p "$PRIMARY_PORT" -U "$DB_REPLICATION_USER" -d postgres >/dev/null 2>&1; do
        sleep 2
    done

    echo "replica-entrypoint: cloning primary via pg_basebackup..."
    PGPASSWORD="$DB_REPLICATION_PASSWORD" pg_basebackup \
        -h "$PRIMARY_HOST" \
        -p "$PRIMARY_PORT" \
        -U "$DB_REPLICATION_USER" \
        -D "$PGDATA" \
        -Fp -Xs -P -R -w

    chmod 700 "$PGDATA"
    echo "replica-entrypoint: base backup complete, standby.signal written."
else
    echo "replica-entrypoint: PGDATA already populated, skipping base backup."
fi

exec docker-entrypoint.sh "$@"
