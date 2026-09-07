#!/bin/bash
# ============================================
# PostgreSQL Primary — replication role bootstrap
# ============================================
# Runs once via /docker-entrypoint-initdb.d on first initialization of the
# primary's data directory. Creates the replication role that db-replica
# uses to stream from this server (see infra/postgresql/replica-entrypoint.sh
# and pg_hba.conf's "replication" entries).
set -euo pipefail

: "${DB_REPLICATION_USER:?DB_REPLICATION_USER is required}"
: "${DB_REPLICATION_PASSWORD:?DB_REPLICATION_PASSWORD is required}"

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '${DB_REPLICATION_USER}') THEN
            CREATE ROLE "${DB_REPLICATION_USER}" WITH REPLICATION LOGIN PASSWORD '${DB_REPLICATION_PASSWORD}';
        END IF;
    END
    \$\$;
EOSQL
