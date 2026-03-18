#!/bin/bash

# =============================================================================
# Master Sprint Setup Script
# Repository: https://github.com/tomkabel/team21-vooglaadija
# Description: Run all sprint setups sequentially or selectively
# Usage: ./setup-all-sprints.sh [OPTIONS] [sprint_numbers...]
# =============================================================================

set -e

readonly SCRIPT_VERSION="1.0.0"
readonly SCRIPT_NAME="$(basename "$0")"
REPO="${REPO:-tomkabel/team21-vooglaadija}"

# Configuration
DRY_RUN=false
VERBOSE=false
SETUP_PROJECT_BOARDS=false
SKIP_CONFIRMATION=false

# Sprint definitions
SPRINTS=(1 2 3 4 5 6)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# LOGGING FUNCTIONS
# =============================================================================

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

log_debug() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${BLUE}[DEBUG]${NC} $1"
    fi
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

check_dependencies() {
    log_info "Checking dependencies..."
    
    if ! command -v gh &> /dev/null; then
        log_error "GitHub CLI (gh) is not installed."
        log_info "Install from: https://cli.github.com/"
        exit 1
    fi
    
    if ! gh auth status &> /dev/null; then
        log_error "Not authenticated with GitHub."
        log_info "Run: gh auth login"
        exit 1
    fi
    
    log_info "✅ All dependencies satisfied"
}

show_header() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║               🚀 COBALT PROJECT SPRINT SETUP 🚀              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo "Repository: $REPO"
    echo "Script Version: $SCRIPT_VERSION"
    echo ""
}

show_sprint_summary() {
    echo ""
    echo "📋 SPRINT OVERVIEW"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "Sprint 1: Mar 9-15  | Project Kickoff & Planning"
    echo "Sprint 2: Mar 16-22 | Architecture Foundation"
    echo "Sprint 3: Mar 23-29 | Core Features Implementation"
    echo "Sprint 4: Mar 30-Apr 5 | AWS Infrastructure & Deployment"
    echo "Sprint 5: Apr 6-12  | Advanced Features & Optimization"
    echo "Sprint 6: Apr 13-19 | Final Polish & Project Closure"
    echo ""
    echo "Total Duration: 6 weeks (Mar 9 - Apr 19, 2026)"
    echo "Total Story Points: 145"
    echo ""
}

# =============================================================================
# SETUP FUNCTIONS
# =============================================================================

run_sprint_setup() {
    local sprint_num="$1"
    local script_file="setup-sprint-${sprint_num}.sh"
    
    log_info "Setting up Sprint $sprint_num..."
    log_debug "Running: ./$script_file"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "[DRY RUN] Would execute: ./$script_file"
        return 0
    fi
    
    if [[ ! -f "$script_file" ]]; then
        log_error "Script not found: $script_file"
        return 1
    fi
    
    if ! ./"$script_file"; then
        log_error "Sprint $sprint_num setup failed!"
        return 1
    fi
    
    log_info "✅ Sprint $sprint_num setup complete"
    return 0
}

run_project_board_setup() {
    local sprint_num="$1"
    local script_file="setup-sprint${sprint_num}-project.sh"
    
    # Handle naming convention difference for sprint 2+
    if [[ "$sprint_num" == "2" ]]; then
        script_file="setup-sprint2-project.sh"
    elif [[ -f "setup-sprint-${sprint_num}-project.sh" ]]; then
        script_file="setup-sprint-${sprint_num}-project.sh"
    else
        log_warn "Project board script not found for Sprint $sprint_num, skipping..."
        return 0
    fi
    
    log_info "Setting up Sprint $sprint_num Project Board..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "[DRY RUN] Would execute: ./$script_file"
        return 0
    fi
    
    if [[ ! -f "$script_file" ]]; then
        log_warn "Project board script not found: $script_file"
        return 0
    fi
    
    if ! ./"$script_file"; then
        log_warn "Sprint $sprint_num project board setup failed (non-critical)"
        return 0
    fi
    
    log_info "✅ Sprint $sprint_num project board created"
    return 0
}

# =============================================================================
# MAIN FUNCTIONS
# =============================================================================

setup_all_sprints() {
    log_info "Setting up ALL sprints sequentially..."
    echo ""
    
    for sprint in "${SPRINTS[@]}"; do
        echo "───────────────────────────────────────────────────────────────"
        if ! run_sprint_setup "$sprint"; then
            log_error "Failed to setup Sprint $sprint"
            read -p "Continue with next sprint? (Y/n): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Nn]$ ]]; then
                log_error "Setup aborted"
                exit 1
            fi
        fi
        
        if [[ "$SETUP_PROJECT_BOARDS" == "true" ]]; then
            run_project_board_setup "$sprint"
        fi
        
        echo ""
    done
    
    echo "═══════════════════════════════════════════════════════════════"
    log_info "🎉 ALL SPRINTS SETUP COMPLETE!"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "Summary:"
    echo "  • 6 Sprints created"
    echo "  • 6 Epics created"
    echo "  • 30 Stories created"
    echo "  • 30+ Labels created"
    echo "  • 6 Milestones created"
    echo ""
    echo "Next Steps:"
    echo "  1. Review issues: gh issue list -R $REPO"
    echo "  2. Set up project boards (if not done automatically)"
    echo "  3. Begin Sprint 1 planning"
    echo ""
}

setup_specific_sprints() {
    local sprints=("$@")
    
    log_info "Setting up specific sprints: ${sprints[*]}"
    echo ""
    
    for sprint in "${sprints[@]}"; do
        if [[ ! " ${SPRINTS[*]} " =~ " ${sprint} " ]]; then
            log_error "Invalid sprint number: $sprint (valid: ${SPRINTS[*]})"
            continue
        fi
        
        echo "───────────────────────────────────────────────────────────────"
        if run_sprint_setup "$sprint"; then
            if [[ "$SETUP_PROJECT_BOARDS" == "true" ]]; then
                run_project_board_setup "$sprint"
            fi
        fi
        echo ""
    done
}

# =============================================================================
# CLI FUNCTIONS
# =============================================================================

usage() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS] [SPRINT_NUMBERS...]

Master script to set up Cobalt project sprints.

OPTIONS:
    -a, --all               Setup all sprints (1-6)
    -p, --with-projects     Also create GitHub Project boards
    -d, --dry-run           Show what would be done without making changes
    -y, --yes               Skip confirmation prompts
    -v, --verbose           Enable verbose output
    -h, --help              Show this help message

EXAMPLES:
    # Setup all sprints
    $SCRIPT_NAME --all

    # Setup specific sprints
    $SCRIPT_NAME 1 2 3

    # Setup all sprints with project boards (dry run)
    $SCRIPT_NAME --all --with-projects --dry-run

    # Setup Sprint 2 with verbose output
    $SCRIPT_NAME -v 2

SPRINTS:
    1: Project Kickoff & Planning (Mar 9-15)
    2: Architecture Foundation (Mar 16-22)
    3: Core Features Implementation (Mar 23-29)
    4: AWS Infrastructure & Deployment (Mar 30-Apr 5)
    5: Advanced Features & Optimization (Apr 6-12)
    6: Final Polish & Project Closure (Apr 13-19)

EOF
}

confirm_setup() {
    if [[ "$SKIP_CONFIRMATION" == "true" ]]; then
        return 0
    fi
    
    echo ""
    echo "⚠️  This will create issues, labels, and milestones in: $REPO"
    echo ""
    read -p "Are you sure you want to continue? (y/N): " -n 1 -r
    echo
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Setup cancelled by user"
        exit 0
    fi
}

# =============================================================================
# MAIN
# =============================================================================

main() {
    local setup_all=false
    local specific_sprints=()
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -a|--all)
                setup_all=true
                shift
                ;;
            -p|--with-projects)
                SETUP_PROJECT_BOARDS=true
                shift
                ;;
            -d|--dry-run)
                DRY_RUN=true
                shift
                ;;
            -y|--yes)
                SKIP_CONFIRMATION=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            [1-6])
                specific_sprints+=("$1")
                shift
                ;;
            *)
                log_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    show_header
    check_dependencies
    show_sprint_summary
    
    # Dry run notice
    if [[ "$DRY_RUN" == "true" ]]; then
        log_warn "DRY RUN MODE - No actual changes will be made"
        echo ""
    fi
    
    # Determine what to setup
    if [[ "$setup_all" == "true" ]]; then
        confirm_setup
        setup_all_sprints
    elif [[ ${#specific_sprints[@]} -gt 0 ]]; then
        confirm_setup
        setup_specific_sprints "${specific_sprints[@]}"
    else
        log_error "No sprints specified"
        usage
        exit 1
    fi
    
    exit 0
}

main "$@"
