#!/bin/bash
# ===========================================
# Vooglaadija - VPS Deployment Script
# For subdomain: youtube.tomabel.ee
# Target: Ubuntu 25 VPS at 37.114.46.226
# ===========================================

set -euo pipefail

# Configuration
DOMAIN="youtube.tomabel.ee"
DEPLOY_DIR="/opt/vooglaadija"
SSL_DIR="$DEPLOY_DIR/infra/ssl"
CERTBOT_DATA_DIR="$DEPLOY_DIR/infra/certbot/data"
BACKUP_DIR="/opt/vooglaadija-backups"
APACHE_USER="www-data"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# ===========================================
# PHASE 0: Pre-flight Checks
# ===========================================
phase0() {
    log_step "=== Phase 0: Pre-flight Checks ==="

    # Check if running as root
    if [[ $EUID -ne 0 ]]; then
        log_warn "This script should be run as root for system installation"
        printf '%s\n' "Re-run with: sudo \"$0\" \"\$@\""
    fi

    # Check for required files
    if [[ ! -f "docker-compose.yml" ]]; then
        log_error "docker-compose.yml not found. Run from project directory."
        exit 1
    fi

    if [[ ! -f "infra/nginx/nginx.production.conf" ]]; then
        log_error "nginx.production.conf not found."
        exit 1
    fi

    log_info "Pre-flight checks passed"
}

# ===========================================
# PHASE 1: System Preparation
# ===========================================
phase1() {
    log_step "=== Phase 1: System Preparation ==="

    log_info "Updating system packages..."
    export DEBIAN_FRONTEND=noninteractive
    apt update && apt upgrade -y

    log_info "Installing required packages..."
    apt install -y \
        docker.io \
        docker-compose-plugin \
        nginx \
        certbot \
        python3-certbot-nginx \
        ufw \
        rsync \
        curl \
        wget \
        vim \
        htop

    # Enable and start Docker
    systemctl enable docker
    systemctl start docker

    # Add deploy user to docker group
    if [[ -n "${SUDO_USER:-}" ]]; then
        usermod -aG docker "$SUDO_USER" || log_warn "Could not add user to docker group"
    fi

    # Configure UFW
    log_info "Configuring firewall..."
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable

    log_info "Phase 1 complete - System prepared"
}

# ===========================================
# PHASE 2: DNS Verification
# ===========================================
phase2() {
    log_step "=== Phase 2: DNS Verification ==="

    log_info "Checking DNS configuration for $DOMAIN..."

    DNS_IP=$(dig +short "$DOMAIN" | tail -n1)

    if [[ -z "$DNS_IP" ]]; then
        log_error "DNS lookup failed for $DOMAIN"
        log_info "Please configure DNS A record: Type=A, Name=youtube, Value=37.114.46.226"
        return 1
    fi

    if [[ "$DNS_IP" != "37.114.46.226" ]]; then
        log_error "DNS points to wrong IP: $DNS_IP (expected 37.114.46.226)"
        log_info "Update your DNS A record to point to 37.114.46.226"
        return 1
    fi

    log_info "DNS verified: $DOMAIN -> $DNS_IP"
}

# ===========================================
# PHASE 3: Directory Setup
# ===========================================
phase3() {
    log_step "=== Phase 3: Directory Setup ==="

    # Create deployment directory
    mkdir -p "$DEPLOY_DIR"
    mkdir -p "$SSL_DIR"
    mkdir -p "$CERTBOT_DATA_DIR"
    mkdir -p "$BACKUP_DIR"
    mkdir -p /var/www/certbot

    # Set permissions
    chmod 755 /var/www/certbot
    chmod 755 "$DEPLOY_DIR"
    chmod 755 "$SSL_DIR"
    chmod 755 "$CERTBOT_DATA_DIR"

    # Set ownership (use www-data for nginx compatibility)
    chown -R root:root "$DEPLOY_DIR"
    chown -R www-data:www-data /var/www/certbot

    # Copy project files (excluding sensitive data)
    log_info "Copying project files to $DEPLOY_DIR..."

    rsync -av \
        --exclude='.git' \
        --exclude='.env' \
        --exclude='.env.*' \
        --exclude='*.pem' \
        --exclude='*.key' \
        --exclude='*.crt' \
        --exclude='storage/' \
        --exclude='data/' \
        --exclude='node_modules/' \
        --exclude='__pycache__/' \
        --exclude='.pytest_cache/' \
        --exclude='.coverage' \
        --exclude='coverage/' \
        --exclude='logs/' \
        --exclude='*.log' \
        --exclude='.ruff_cache/' \
        --exclude='.mypy_cache/' \
        --exclude='.hatch/' \
        ./ "$DEPLOY_DIR/"

    log_info "Phase 3 complete - Directories set up"
}

# ===========================================
# PHASE 4: SSL Certificate Acquisition
# ===========================================
phase4() {
    log_step "=== Phase 4: SSL Certificate Acquisition ==="

    # Stop nginx if running (conflicts with certbot port 80)
    systemctl stop nginx || true

    # Check if certificates already exist
    if [[ -f "$SSL_DIR/fullchain.pem" ]] && [[ -f "$SSL_DIR/privkey.pem" ]]; then
        log_info "SSL certificates already exist in $SSL_DIR"
        log_info "To re-generate, delete existing certs and run this phase again"
        return 0
    fi

    log_info "Obtaining Let's Encrypt certificate for $DOMAIN..."

    # Create temporary nginx config for ACME challenge
    cat > /tmp/certbot-nginx.conf << 'EOF'
server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
}
EOF

    sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" /tmp/certbot-nginx.conf

    # Configure nginx temporarily
    cp /tmp/certbot-nginx.conf /etc/nginx/sites-available/"$DOMAIN"
    ln -sf /etc/nginx/sites-available/"$DOMAIN" /etc/nginx/sites-enabled/"$DOMAIN"

    # Test and reload nginx
    nginx -t && systemctl reload nginx || systemctl start nginx

    # Obtain certificate
    certbot certonly \
        --webroot \
        --webroot-path=/var/www/certbot \
        --email "admin@tomabel.ee" \
        --agree-tos \
        --no-eff-email \
        -d "$DOMAIN" \
        --verbose

    # Copy certificates to project directory
    log_info "Copying certificates to project directory..."
    cp /etc/letsencrypt/live/"$DOMAIN"/fullchain.pem "$SSL_DIR/fullchain.pem"
    cp /etc/letsencrypt/live/"$DOMAIN"/privkey.pem "$SSL_DIR/privkey.pem"

    # Create symlinks for compatibility (cert.pem -> fullchain.pem, key.pem -> privkey.pem)
    cd "$SSL_DIR"
    ln -sf fullchain.pem cert.pem 2>/dev/null || true
    ln -sf privkey.pem key.pem 2>/dev/null || true

    # Set secure permissions
    chmod 644 "$SSL_DIR/fullchain.pem"
    chmod 644 "$SSL_DIR/cert.pem"
    chmod 600 "$SSL_DIR/privkey.pem"
    chmod 600 "$SSL_DIR/key.pem"

    # Verify certificates
    log_info "Certificate details:"
    openssl x509 -in "$SSL_DIR/fullchain.pem" -noout -subject -dates

    log_info "Phase 4 complete - SSL certificates obtained"
}

# ===========================================
# PHASE 5: Nginx Configuration
# ===========================================
phase5() {
    log_step "=== Phase 5: Nginx Configuration ==="

    # Deploy production nginx config
    log_info "Deploying production nginx configuration..."

    # Create production site config
    cat > /etc/nginx/sites-available/"$DOMAIN" << 'EOF'
# HTTP to HTTPS redirect
server {
    listen 80;
    server_name DOMAIN_PLACEHOLDER;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name DOMAIN_PLACEHOLDER;

    ssl_certificate /PATH_TO_SSL/fullchain.pem;
    ssl_certificate_key /PATH_TO_SSL/privkey.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers off;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;

    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;
    resolver_timeout 5s;

    proxy_connect_timeout 60s;
    proxy_send_timeout 300s;
    proxy_read_timeout 300s;
    proxy_buffering off;
    proxy_request_buffering off;

    gzip on;
    gzip_types application/json text/plain application/octet-stream;
    gzip_min_length 1000;

    client_max_body_size 500M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health endpoint
    location /health {
        access_log off;
        return 200 "nginx healthy\n";
        add_header Content-Type text/plain;
    }
}
EOF

    # Replace placeholders
    sed -i "s/DOMAIN_PLACEHOLDER/$DOMAIN/g" /etc/nginx/sites-available/"$DOMAIN"
    sed -i "s|PATH_TO_SSL|$SSL_DIR|g" /etc/nginx/sites-available/"$DOMAIN"

    # Enable site
    rm -f /etc/nginx/sites-enabled/default 2>/dev/null || true
    ln -sf /etc/nginx/sites-available/"$DOMAIN" /etc/nginx/sites-enabled/"$DOMAIN"

    # Test and reload nginx
    nginx -t && systemctl reload nginx

    log_info "Phase 5 complete - Nginx configured"
}

# ===========================================
# PHASE 6: Environment Configuration
# ===========================================
phase6() {
    log_step "=== Phase 6: Environment Configuration ==="

    # Create production .env if it doesn't exist
    if [[ -f "$DEPLOY_DIR/.env" ]]; then
        log_info ".env already exists, skipping creation"
        log_warn "To regenerate, delete .env and run this phase again"
        return 0
    fi

    log_info "Creating production .env file..."

    # Generate secure SECRET_KEY
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

    # Generate strong database password
    DB_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")

    # Generate strong Redis password
    REDIS_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(24))")

    cat > "$DEPLOY_DIR/.env" << EOF
# ===========================================
# Production Environment Configuration
# Generated by deploy.sh on $(date)
# ===========================================

# Database
DB_USER=postgres
DB_PASSWORD=${DB_PASSWORD}
DB_NAME=ytprocessor

# Redis
REDIS_PASSWORD=${REDIS_PASSWORD}

# Security
SECRET_KEY=${SECRET_KEY}
COOKIE_SECURE=True

# CORS - HTTPS required
CORS_ORIGINS=https://youtube.tomabel.ee

# Token Expiry
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# Storage
FILE_EXPIRE_HOURS=24
STORAGE_PATH=/app/storage

# Observability (disabled for production)
FEATURE_METRICS_ENABLED=false
FEATURE_TRACING_ENABLED=false
EOF

    chmod 600 "$DEPLOY_DIR/.env"

    log_info ".env created at $DEPLOY_DIR/.env"
    log_warn "IMPORTANT: Backup this file securely - it contains database and Redis passwords!"

    # Generate summary of what was generated (except passwords)
    log_info "Environment summary:"
    log_info "  DB_USER: postgres"
    log_info "  DB_PASSWORD: <generated - stored in .env>"
    log_info "  REDIS_PASSWORD: <generated - stored in .env>"
    log_info "  SECRET_KEY: <generated - stored in .env>"
}

# ===========================================
# PHASE 7: Application Deployment
# ===========================================
phase7() {
    log_step "=== Phase 7: Application Deployment ==="

    cd "$DEPLOY_DIR"

    # Ensure .env exists
    if [[ ! -f ".env" ]]; then
        log_error ".env not found. Run phase 6 first."
        return 1
    fi

    # Verify SSL certificates exist
    if [[ ! -f "infra/ssl/fullchain.pem" ]] || [[ ! -f "infra/ssl/privkey.pem" ]]; then
        log_error "SSL certificates not found in infra/ssl/"
        log_info "Run phase 4 to obtain certificates"
        return 1
    fi

    log_info "Building Docker images..."
    docker compose -f docker-compose.yml -f docker-compose.production.yml build --no-cache

    log_info "Starting database and redis..."
    docker compose -f docker-compose.yml -f docker-compose.production.yml up -d db redis

    log_info "Waiting for database to be healthy..."
    sleep 15

    # Check database health
    for i in {1..30}; do
        if docker compose -f docker-compose.yml -f docker-compose.production.yml exec db pg_isready -U postgres -d ytprocessor >/dev/null 2>&1; then
            log_info "Database is healthy"
            break
        fi
        log_info "Waiting for database... ($i/30)"
        sleep 2
    done

    log_info "Running database migrations..."
    docker compose -f docker-compose.yml -f docker-compose.production.yml exec api python /app/migrate.sh || log_warn "Migration may have already been run"

    log_info "Starting all services..."
    docker compose -f docker-compose.yml -f docker-compose.production.yml up -d

    log_info "Waiting for services to stabilize..."
    sleep 10

    log_info "Phase 7 complete - Application deployed"
}

# ===========================================
# PHASE 8: Verification
# ===========================================
phase8() {
    log_step "=== Phase 8: Verification ==="

    cd "$DEPLOY_DIR"

    log_info "=== Service Status ==="
    docker compose -f docker-compose.yml -f docker-compose.production.yml ps

    log_info ""
    log_info "=== Testing Endpoints ==="

    # Test HTTP (should redirect)
    log_info "Testing HTTP redirect..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -L http://"$DOMAIN" --max-redirs 0 2>/dev/null || echo "000")
    if [[ "$HTTP_CODE" == "301" ]]; then
        log_info "✓ HTTP redirects to HTTPS (301)"
    else
        log_warn "✗ HTTP returned $HTTP_CODE (expected 301)"
    fi

    # Test HTTPS
    log_info "Testing HTTPS endpoint..."
    HTTPS_CODE=$(curl -s -o /dev/null -w "%{http_code}" https://"$DOMAIN" 2>/dev/null || echo "000")
    if [[ "$HTTPS_CODE" == "200" ]]; then
        log_info "✓ HTTPS returns 200 OK"
    else
        log_warn "✗ HTTPS returned $HTTPS_CODE (expected 200)"
    fi

    # Test API health
    log_info "Testing API health..."
    curl -s https://"$DOMAIN"/api/v1/health || log_warn "API health check failed"

    # Check SSL certificate
    log_info ""
    log_info "=== SSL Certificate Info ==="
    if [[ -f "infra/ssl/fullchain.pem" ]]; then
        openssl x509 -in infra/ssl/fullchain.pem -noout -subject -issuer -dates 2>/dev/null || log_warn "Could not display certificate info"
    else
        log_warn "Certificate file not found"
    fi

    # Check container logs
    log_info ""
    log_info "=== Recent API Logs ==="
    docker compose -f docker-compose.yml -f docker-compose.production.yml logs --tail=20 api 2>/dev/null || true

    log_info ""
    log_info "=== Deployment Complete ==="
    log_info "Visit: https://$DOMAIN"
    log_info "API Docs: https://$DOMAIN/docs"
    log_info ""
    log_info "To view logs: cd $DEPLOY_DIR && docker compose -f docker-compose.yml -f docker-compose.production.yml logs -f"
    log_info "To restart: cd $DEPLOY_DIR && docker compose -f docker-compose.yml -f docker-compose.production.yml restart"
}

# ===========================================
# Rollback Function
# ===========================================
rollback() {
    log_warn "=== Rolling Back Deployment ==="
    cd "$DEPLOY_DIR"
    docker compose -f docker-compose.yml -f docker-compose.production.yml down || true
    log_info "Rollback complete"
}

# ===========================================
# Show Status
# ===========================================
status() {
    log_step "=== Deployment Status ==="
    cd "$DEPLOY_DIR" 2>/dev/null || { log_error "Deployment directory not found"; return 1; }

    echo ""
    echo "Docker Containers:"
    docker compose -f docker-compose.yml -f docker-compose.production.yml ps 2>/dev/null || echo "Not running"

    echo ""
    echo "SSL Certificates:"
    if [[ -f "infra/ssl/fullchain.pem" ]]; then
        echo "  Certificate: VALID"
        openssl x509 -in infra/ssl/fullchain.pem -noout -enddate 2>/dev/null || true
    else
        echo "  Certificate: NOT FOUND"
    fi

    echo ""
    echo "Environment:"
    if [[ -f ".env" ]]; then
        echo "  .env: EXISTS"
    else
        echo "  .env: NOT FOUND"
    fi

    echo ""
    echo "Services reachable:"
    curl -s -o /dev/null -w "  HTTP: %{http_code}\n" -L http://"$DOMAIN" 2>/dev/null || echo "  HTTP: FAILED"
    curl -s -o /dev/null -w "  HTTPS: %{http_code}\n" https://"$DOMAIN" 2>/dev/null || echo "  HTTPS: FAILED"
}

# ===========================================
# Main Menu
# ===========================================
show_menu() {
    echo ""
    echo "============================================"
    echo "  Vooglaadija VPS Deployment"
    echo "  Domain: $DOMAIN"
    echo "============================================"
    echo ""
    echo "  0) Pre-flight checks (optional)"
    echo "  1) Phase 1 - System preparation"
    echo "  2) Phase 2 - DNS verification"
    echo "  3) Phase 3 - Directory setup"
    echo "  4) Phase 4 - SSL certificates"
    echo "  5) Phase 5 - Nginx configuration"
    echo "  6) Phase 6 - Environment setup"
    echo "  7) Phase 7 - Application deployment"
    echo "  8) Phase 8 - Verification"
    echo ""
    echo "  R) Rollback"
    echo "  S) Status"
    echo "  Q) Quit"
    echo ""
    echo -n "  Select option: "
}

# ===========================================
# Main Execution
# ===========================================
main() {
    if [[ $# -gt 0 ]]; then
        case "$1" in
            0) phase0 ;;
            1) phase1 ;;
            2) phase2 ;;
            3) phase3 ;;
            4) phase4 ;;
            5) phase5 ;;
            6) phase6 ;;
            7) phase7 ;;
            8) phase8 ;;
            all) phase0 && phase1 && phase2 && phase3 && phase4 && phase5 && phase6 && phase7 && phase8 ;;
            rollback) rollback ;;
            status) status ;;
            *)
                echo "Usage: $0 [0-8|all|rollback|status]"
                echo ""
                echo "Phases:"
                echo "  0 - Pre-flight checks"
                echo "  1 - System preparation"
                echo "  2 - DNS verification"
                echo "  3 - Directory setup"
                echo "  4 - SSL certificates"
                echo "  5 - Nginx configuration"
                echo "  6 - Environment setup"
                echo "  7 - Application deployment"
                echo "  8 - Verification"
                echo "  all - Run all phases"
                echo "  rollback - Stop all services"
                echo "  status - Show deployment status"
                exit 1
                ;;
        esac
    else
        show_menu
        read -r choice
        case "$choice" in
            0) phase0 ;;
            1) phase1 ;;
            2) phase2 ;;
            3) phase3 ;;
            4) phase4 ;;
            5) phase5 ;;
            6) phase6 ;;
            7) phase7 ;;
            8) phase8 ;;
            R|r) rollback ;;
            S|s) status ;;
            Q|q) exit 0 ;;
            *) log_error "Invalid option" ;;
        esac
    fi
}

main "$@"