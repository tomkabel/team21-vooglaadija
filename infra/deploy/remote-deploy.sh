#!/bin/bash
set -euo pipefail

# ============================================
# Vooglaadija - Remote Deployment Script
# Executed on production server via SSH
# ============================================
#
# Environment variables passed from the workflow:
#   GHCR_PAT      - Classic PAT with read:packages scope
#   ENV_B64       - Base64-encoded production .env file
#   IMAGE_TAG     - Commit SHA for immutable image tags
#   GHCR_OWNER    - GitHub repository owner
#   GHCR_REPO     - GitHub repository name
#
# Usage (from GitHub Actions runner):
#   ssh ubuntu@37.114.46.226 \
#     "GHCR_PAT='...' ENV_B64='...' IMAGE_TAG='...' GHCR_OWNER='...' GHCR_REPO='...' bash -s" \
#     < infra/deploy/remote-deploy.sh
# ============================================

DEPLOY_DIR="/opt/vooglaadija"
DOMAIN="youtube.tomabel.ee"
GHCR_REGISTRY="ghcr.io"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# ============================================
# Configuration Validation
# ============================================

: "${GHCR_PAT:?GHCR_PAT is required}"
: "${ENV_B64:?ENV_B64 is required}"
: "${IMAGE_TAG:?IMAGE_TAG is required}"
: "${GHCR_OWNER:?GHCR_OWNER is required}"
: "${GHCR_REPO:?GHCR_REPO is required}"

API_IMAGE="${GHCR_REGISTRY}/${GHCR_OWNER}/${GHCR_REPO}:${IMAGE_TAG}"
WORKER_IMAGE="${GHCR_REGISTRY}/${GHCR_OWNER}/${GHCR_REPO}:worker-${IMAGE_TAG}"

COMPOSE_CMD="docker compose -f ${DEPLOY_DIR}/docker-compose.yml -f ${DEPLOY_DIR}/docker-compose.production.yml"

# Backup state
BACKUP_API=""
BACKUP_WORKER=""

# ============================================
# Capture Backup State
# ============================================

capture_backup() {
    log_step "Capturing current deployment state..."

    if docker inspect ytprocessor-api >/dev/null 2>&1; then
        BACKUP_API=$(docker inspect --format='{{.Config.Image}}' ytprocessor-api)
        log_info "Current API image: ${BACKUP_API}"
    fi

    if docker inspect ytprocessor-worker >/dev/null 2>&1; then
        BACKUP_WORKER=$(docker inspect --format='{{.Config.Image}}' ytprocessor-worker)
        log_info "Current Worker image: ${BACKUP_WORKER}"
    fi
}

# ============================================
# Write .env Atomically
# ============================================

write_env() {
    log_step "Writing production .env..."

    local env_tmp="${DEPLOY_DIR}/.env.tmp"
    printf '%s' "$ENV_B64" | base64 -d > "$env_tmp"
    chmod 600 "$env_tmp"
    mv "$env_tmp" "${DEPLOY_DIR}/.env"
    log_info ".env written successfully"
}

# ============================================
# GHCR Login
# ============================================

ghcr_login() {
    log_step "Logging into GHCR..."
    echo "$GHCR_PAT" | docker login "$GHCR_REGISTRY" -u "$GHCR_OWNER" --password-stdin
    log_info "GHCR login successful"
}

# ============================================
# Pull Images
# ============================================

pull_images() {
    log_step "Pulling images..."
    docker pull "$API_IMAGE"
    docker pull "$WORKER_IMAGE"
    log_info "Images pulled successfully"
}

# ============================================
# Create Deploy Override
# ============================================

create_deploy_override() {
    log_step "Creating deployment override..."
    cat > /tmp/deploy-override.yml << EOF
services:
  api:
    image: ${API_IMAGE}
  worker:
    image: ${WORKER_IMAGE}
EOF
    log_info "Deploy override created"
}

# ============================================
# Run Migrations
# ============================================

run_migrations() {
    log_step "Running database migrations..."

    # Ensure infrastructure services are running before migrations
    $COMPOSE_CMD up -d db redis

    # Wait for database to be healthy
    log_info "Waiting for database to be healthy..."
    for i in {1..30}; do
        if $COMPOSE_CMD exec -T db pg_isready -U postgres -d ytprocessor >/dev/null 2>&1; then
            log_info "Database is healthy"
            break
        fi
        if [[ $i -eq 30 ]]; then
            log_error "Database did not become healthy within 60 seconds"
            return 1
        fi
        sleep 2
    done

    # Run migrations in a one-off container with the new image.
    # The api service depends on storage-init in production, which will
    # run automatically as a dependency.
    $COMPOSE_CMD -f /tmp/deploy-override.yml run --rm api /app/migrate.sh || {
        log_error "Migration failed"
        return 1
    }

    log_info "Migrations completed successfully"
}

# ============================================
# Update Services
# ============================================

update_services() {
    log_step "Updating services..."

    # --no-build ensures we use the pre-pulled images rather than
    # attempting to build from the local context.
    $COMPOSE_CMD -f /tmp/deploy-override.yml up -d --no-build

    log_info "Services updated"
}

# ============================================
# Health Check
# ============================================

health_check() {
    log_step "Running health checks..."

    # Give services time to start
    sleep 5

    for i in {1..12}; do
        local http_code
        http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "https://${DOMAIN}/api/v1/health" || echo "000")

        if [ "$http_code" = "200" ]; then
            log_info "Health check passed (HTTP 200)"
            return 0
        fi

        log_info "Health check attempt $i/12: HTTP $http_code"
        sleep 5
    done

    log_error "Health check failed after 60 seconds"
    return 1
}

# ============================================
# Rollback
# ============================================

rollback() {
    log_warn "Initiating rollback..."

    if [[ -z "$BACKUP_API" && -z "$BACKUP_WORKER" ]]; then
        log_warn "No backup images captured. Manual intervention required."
        return 1
    fi

    cat > /tmp/rollback-override.yml << EOF
services:
  api:
    image: ${BACKUP_API:-${API_IMAGE}}
  worker:
    image: ${BACKUP_WORKER:-${WORKER_IMAGE}}
EOF

    $COMPOSE_CMD -f /tmp/rollback-override.yml up -d --no-build || {
        log_error "Rollback failed"
        return 1
    }

    log_warn "Rollback completed. Previous images restored."

    # Verify rollback health
    sleep 5
    local http_code
    http_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "https://${DOMAIN}/api/v1/health" || echo "000")
    if [ "$http_code" = "200" ]; then
        log_info "Rollback health check passed"
    else
        log_error "Rollback health check failed (HTTP $http_code). Manual intervention required."
    fi
}

# ============================================
# Cleanup
# ============================================

cleanup() {
    log_step "Cleaning up..."
    rm -f /tmp/deploy-override.yml /tmp/rollback-override.yml
    # Do not log out of GHCR to preserve cached credentials for future pulls
    log_info "Cleanup complete"
}

# ============================================
# Main
# ============================================

main() {
    capture_backup
    write_env
    ghcr_login
    pull_images
    create_deploy_override

    local deploy_success=false

    if run_migrations; then
        if update_services; then
            if health_check; then
                deploy_success=true
            fi
        fi
    fi

    if [[ "$deploy_success" != "true" ]]; then
        rollback
        cleanup
        exit 1
    fi

    cleanup
    log_step "Deployment successful!"
}

main "$@"
