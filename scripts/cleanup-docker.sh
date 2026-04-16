#!/bin/bash
# Docker Cleanup Script for Vooglaadija
# Frees up disk space by removing unused Docker resources
# 
# Usage:
#   ./scripts/cleanup-docker.sh [--all] [--images] [--volumes] [--build-cache]
#
# Options:
#   --all          Clean everything (images, volumes, build cache)
#   --images       Remove unused images
#   --volumes      Remove unused volumes (WARNING: destroys data!)
#   --build-cache  Remove build cache
#   --dry-run      Show what would be cleaned without actually cleaning

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_disk_usage() {
    echo "=== Current Disk Usage ==="
    docker system df
    echo ""
    echo "=== Root Partition ==="
    df -h / | tail -1
}

# Parse arguments
DRY_RUN=false
CLEAN_IMAGES=false
CLEAN_VOLUMES=false
CLEAN_BUILD_CACHE=false
CLEAN_ALL=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            CLEAN_ALL=true
            shift
            ;;
        --images)
            CLEAN_IMAGES=true
            shift
            ;;
        --volumes)
            CLEAN_VOLUMES=true
            shift
            ;;
        --build-cache)
            CLEAN_BUILD_CACHE=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --help|-h)
            echo "Docker Cleanup Script for Vooglaadija"
            echo ""
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --all          Clean everything (images, volumes, build cache)"
            echo "  --images       Remove unused images"
            echo "  --volumes      Remove unused volumes (WARNING: destroys data!)"
            echo "  --build-cache  Remove build cache"
            echo "  --dry-run      Show what would be cleaned without actually cleaning"
            echo "  --help, -h     Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --all                    # Clean everything"
            echo "  $0 --build-cache --images   # Clean build cache and images"
            echo "  $0 --dry-run                # Preview what would be cleaned"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# If --all is specified, clean everything
if $CLEAN_ALL; then
    CLEAN_IMAGES=true
    CLEAN_VOLUMES=true
    CLEAN_BUILD_CACHE=true
fi

# Show current state
echo ""
log_info "Docker Cleanup Script"
echo ""
show_disk_usage
echo ""

if $DRY_RUN; then
    log_warn "DRY RUN - No changes will be made"
    echo ""
fi

# Confirm if cleaning volumes (destructive)
if $CLEAN_VOLUMES && ! $DRY_RUN; then
    log_warn "WARNING: Volume pruning will delete unused volumes!"
    log_warn "This includes named volumes that are not attached to a container."
    read -p "Are you sure you want to continue? (yes/no) " -r
    if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
        log_info "Aborting volume cleanup"
        CLEAN_VOLUMES=false
    fi
    echo ""
fi

# Build the docker system prune command
PRUNE_CMD="docker system prune"

if $CLEAN_IMAGES; then
    PRUNE_CMD="$PRUNE_CMD -a"
fi

if $CLEAN_VOLUMES; then
    PRUNE_CMD="$PRUNE_CMD --volumes"
fi

if $CLEAN_BUILD_CACHE; then
    PRUNE_CMD="$PRUNE_CMD --all"
fi

# Add force flag for non-interactive mode
if $DRY_RUN; then
    log_info "Would execute: $PRUNE_CMD -f"
    echo ""
    log_warn "Dry run complete - no changes made"
else
    log_info "Executing: $PRUNE_CMD"
    echo ""
    eval $PRUNE_CMD
    echo ""
    log_info "Cleanup complete!"
    echo ""
    show_disk_usage
fi
