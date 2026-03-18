#!/bin/bash

# =============================================================================
# GitHub Projects v2 Setup Script for Sprint 2
# Repository: https://github.com/tomkabel/team21-vooglaadija
# Description: Kanban board setup for Sprint 2
# Note: Workflows are managed separately in .github/workflows/
# Version: 2.1.0 (Workflow-free)
# =============================================================================

set -euo pipefail

# =============================================================================
# CONFIGURATION & CONSTANTS
# =============================================================================
readonly SCRIPT_VERSION="2.1.0"
readonly SCRIPT_NAME="$(basename "$0")"

# Default values
REPO="${REPO:-tomkabel/team21-vooglaadija}"
SPRINT_NUMBER="${SPRINT_NUMBER:-2}"
SPRINT_NAME="${SPRINT_NAME:-Architecture Foundation}"
PROJECT_NAME="${PROJECT_NAME:-Cobalt Sprint $SPRINT_NUMBER: $SPRINT_NAME}"
SPRINT_START="${SPRINT_START:-2026-03-16}"
SPRINT_END="${SPRINT_END:-2026-03-22}"

# Field options
readonly PRIORITY_OPTIONS="Critical,High,Medium,Low"
readonly STATUS_OPTIONS="Backlog,Ready for Dev,In Progress,Code Review,Testing,Done"
readonly TYPE_OPTIONS="Feature,Refactor,Infrastructure,Testing,Documentation"

# Story points mapping
declare -A STORY_POINTS_MAP=(
    ["PostgreSQL"]=5
    ["Svelte 5"]=8
    ["pnpm workspaces"]=5
    ["authentication service"]=5
    ["CI/CD pipeline"]=3
)

# =============================================================================
# GLOBAL STATE
# =============================================================================
VERBOSE=false
DRY_RUN=false
PROJECT_NUMBER=""
PROJECT_ID=""
PROJECT_URL=""
CREATED_FIELDS=()
ADDED_ITEMS=()
FAILED_ITEMS=()
TMPDIR=""

# =============================================================================
# LOGGING FUNCTIONS
# =============================================================================

log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp
    timestamp=$(date '+%H:%M:%S')
    
    case "$level" in
        INFO)  echo -e "\033[0;32m[${timestamp}] ℹ️  ${message}\033[0m" ;;
        WARN)  echo -e "\033[1;33m[${timestamp}] ⚠️  ${message}\033[0m" ;;
        ERROR) echo -e "\033[0;31m[${timestamp}] ❌ ${message}\033[0m" >&2 ;;
        DEBUG) 
            if [[ "$VERBOSE" == "true" ]]; then
                echo -e "\033[0;34m[${timestamp}] 🐛 ${message}\033[0m"
            fi
            ;;
        SUCCESS) echo -e "\033[0;32m[${timestamp}] ✅ ${message}\033[0m" ;;
    esac
}

# =============================================================================
# CLEANUP & ROLLBACK
# =============================================================================

cleanup_temp() {
    if [[ -n "$TMPDIR" && -d "$TMPDIR" ]]; then
        log DEBUG "Cleaning up temp directory: $TMPDIR"
        rm -rf "$TMPDIR"
    fi
}

trap cleanup_temp EXIT
trap 'log ERROR "Interrupted by user"; exit 130' INT TERM

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

check_dependencies() {
    log INFO "Checking dependencies..."
    
    if ! command -v gh &> /dev/null; then
        log ERROR "GitHub CLI (gh) is not installed."
        exit 1
    fi
    
    if ! command -v jq &> /dev/null; then
        log ERROR "jq is required but not installed."
        exit 1
    fi
    
    if ! gh auth status &> /dev/null; then
        log ERROR "Not authenticated with GitHub."
        exit 1
    fi
    
    log SUCCESS "All dependencies satisfied"
}

validate_inputs() {
    log INFO "Validating inputs..."
    
    if ! [[ "$SPRINT_NUMBER" =~ ^[0-9]+$ ]]; then
        log ERROR "SPRINT_NUMBER must be a positive integer"
        exit 1
    fi
    
    if ! date -d "$SPRINT_START" &> /dev/null; then
        log ERROR "Invalid SPRINT_START date: $SPRINT_START"
        exit 1
    fi
    
    if ! date -d "$SPRINT_END" &> /dev/null; then
        log ERROR "Invalid SPRINT_END date: $SPRINT_END"
        exit 1
    fi
    
    log SUCCESS "Input validation passed"
}

# =============================================================================
# PROJECT FUNCTIONS
# =============================================================================

find_existing_project() {
    log INFO "Checking for existing project: $PROJECT_NAME"
    
    local owner
    owner=$(echo "$REPO" | cut -d'/' -f1)
    
    local existing
    existing=$(gh project list --owner="$owner" --format=json 2>/dev/null | \
        jq -r --arg name "$PROJECT_NAME" '.projects[] | select(.title == $name) | .number' | \
        head -n1)
    
    if [[ -n "$existing" && "$existing" != "null" ]]; then
        log WARN "Project already exists (#$existing)"
        return 0
    fi
    
    return 1
}

create_project() {
    log INFO "Creating GitHub Project v2..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log WARN "DRY RUN: Would create project '$PROJECT_NAME'"
        PROJECT_NUMBER="DRY-RUN"
        return 0
    fi
    
    local owner
    owner=$(echo "$REPO" | cut -d'/' -f1)
    
    local output
    if ! output=$(gh project create \
        --owner="$owner" \
        --title="$PROJECT_NAME" \
        --format=json 2>&1); then
        log ERROR "Failed to create project: $output"
        return 1
    fi
    
    PROJECT_NUMBER=$(echo "$output" | jq -r '.number')
    PROJECT_URL=$(echo "$output" | jq -r '.url')
    PROJECT_ID=$(echo "$output" | jq -r '.id')
    
    log SUCCESS "Project created (#$PROJECT_NUMBER)"
    log INFO "URL: $PROJECT_URL"
    
    return 0
}

load_existing_project() {
    local existing_number="$1"
    
    log INFO "Loading existing project #$existing_number..."
    
    local owner
    owner=$(echo "$REPO" | cut -d'/' -f1)
    
    local output
    if ! output=$(gh project view "$existing_number" \
        --owner="$owner" \
        --format=json 2>&1); then
        log ERROR "Failed to load project #$existing_number"
        return 1
    fi
    
    PROJECT_NUMBER="$existing_number"
    PROJECT_URL=$(echo "$output" | jq -r '.url')
    PROJECT_ID=$(echo "$output" | jq -r '.id')
    
    log SUCCESS "Loaded existing project (#$PROJECT_NUMBER)"
}

# =============================================================================
# FIELD FUNCTIONS
# =============================================================================

field_exists() {
    local field_name="$1"
    
    local owner
    owner=$(echo "$REPO" | cut -d'/' -f1)
    
    local fields
    fields=$(gh project field-list "$PROJECT_NUMBER" \
        --owner="$owner" \
        --format=json 2>/dev/null)
    
    if echo "$fields" | jq -e --arg name "$field_name" '.fields[] | select(.name == $name)' &> /dev/null; then
        return 0
    fi
    
    return 1
}

create_field() {
    local name="$1"
    local data_type="$2"
    local options="${3:-}"
    
    log INFO "Creating field: $name ($data_type)"
    
    if field_exists "$name"; then
        log WARN "Field '$name' already exists, skipping"
        return 0
    fi
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log WARN "DRY RUN: Would create field '$name'"
        CREATED_FIELDS+=("$name")
        return 0
    fi
    
    local owner
    owner=$(echo "$REPO" | cut -d'/' -f1)
    
    local cmd=(gh project field-create "$PROJECT_NUMBER")
    cmd+=(--owner="$owner")
    cmd+=(--name="$name")
    cmd+=(--data-type="$data_type")
    
    if [[ -n "$options" && "$data_type" == "SINGLE_SELECT" ]]; then
        cmd+=(--single-select-options="$options")
    fi
    
    local output
    if ! output=$("${cmd[@]}" 2>&1); then
        log ERROR "Failed to create field '$name': $output"
        return 1
    fi
    
    CREATED_FIELDS+=("$name")
    log SUCCESS "Created field: $name"
    
    return 0
}

configure_fields() {
    log INFO "Configuring custom fields..."
    
    create_field "Story Points" "NUMBER" "" || return 1
    create_field "Priority" "SINGLE_SELECT" "$PRIORITY_OPTIONS" || return 1
    create_field "Status" "SINGLE_SELECT" "$STATUS_OPTIONS" || return 1
    create_field "Type" "SINGLE_SELECT" "$TYPE_OPTIONS" || return 1
    
    log SUCCESS "All fields configured"
}

# =============================================================================
# ISSUE FUNCTIONS
# =============================================================================

get_sprint_issues() {
    log INFO "Fetching Sprint $SPRINT_NUMBER issues..."
    
    local output
    if ! output=$(gh issue list -R "$REPO" \
        --label="sprint-$SPRINT_NUMBER" \
        --state=open \
        --json=number,title,url,labels \
        --limit=50 2>&1); then
        log ERROR "Failed to fetch issues: $output"
        return 1
    fi
    
    local count
    count=$(echo "$output" | jq 'length')
    
    if [[ "$count" -eq 0 ]]; then
        log ERROR "No Sprint $SPRINT_NUMBER issues found!"
        log INFO "Run: ./setup-sprint-2.sh first"
        return 1
    fi
    
    log SUCCESS "Found $count Sprint $SPRINT_NUMBER issues"
    echo "$output" > "$TMPDIR/issues.json"
}

determine_priority() {
    local issue_json="$1"
    local labels
    labels=$(echo "$issue_json" | jq -r '.labels[].name' 2>/dev/null)
    
    if echo "$labels" | grep -q "priority-critical"; then
        echo "Critical"
    elif echo "$labels" | grep -q "priority-high"; then
        echo "High"
    elif echo "$labels" | grep -q "priority-medium"; then
        echo "Medium"
    else
        echo "Low"
    fi
}

determine_story_points() {
    local title="$1"
    
    for key in "${!STORY_POINTS_MAP[@]}"; do
        if [[ "$title" == *"$key"* ]]; then
            echo "${STORY_POINTS_MAP[$key]}"
            return
        fi
    done
    echo ""
}

add_issue_to_project() {
    local issue_json="$1"
    local counter="$2"
    
    local issue_number issue_title issue_url
    issue_number=$(echo "$issue_json" | jq -r '.number')
    issue_title=$(echo "$issue_json" | jq -r '.title')
    issue_url=$(echo "$issue_json" | jq -r '.url')
    
    log INFO "[$counter] Adding Issue #$issue_number: ${issue_title:0:50}..."
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log WARN "DRY RUN: Would add issue #$issue_number"
        return 0
    fi
    
    local owner
    owner=$(echo "$REPO" | cut -d'/' -f1)
    
    local add_output
    if ! add_output=$(gh project item-add "$PROJECT_NUMBER" \
        --owner="$owner" \
        --url="$issue_url" \
        --format=json 2>&1); then
        log ERROR "Failed to add issue #$issue_number: $add_output"
        FAILED_ITEMS+=("$issue_number")
        return 1
    fi
    
    local item_id
    item_id=$(echo "$add_output" | jq -r '.id')
    ADDED_ITEMS+=("$item_id")
    
    local priority points
    priority=$(determine_priority "$issue_json")
    points=$(determine_story_points "$issue_title")
    
    gh project item-edit "$PROJECT_NUMBER" \
        --owner="$owner" \
        --id="$item_id" \
        --field="Priority" \
        --value="$priority" 2>/dev/null || log WARN "Failed to set Priority"
    
    if [[ -n "$points" ]]; then
        gh project item-edit "$PROJECT_NUMBER" \
            --owner="$owner" \
            --id="$item_id" \
            --field="Story Points" \
            --value="$points" 2>/dev/null || log WARN "Failed to set Story Points"
    fi
    
    gh project item-edit "$PROJECT_NUMBER" \
        --owner="$owner" \
        --id="$item_id" \
        --field="Status" \
        --value="Backlog" 2>/dev/null || log WARN "Failed to set Status"
    
    log SUCCESS "Added #$issue_number (Priority: $priority, Points: ${points:-N/A})"
}

add_all_issues() {
    log INFO "Adding issues to project..."
    
    local issues_json
    issues_json=$(cat "$TMPDIR/issues.json")
    
    local counter=0
    while IFS= read -r issue; do
        counter=$((counter + 1))
        add_issue_to_project "$issue" "$counter"
    done < <(echo "$issues_json" | jq -c '.[]')
    
    log SUCCESS "Processed $counter issues"
}

# =============================================================================
# SUMMARY & MAIN
# =============================================================================

show_summary() {
    echo ""
    echo "================================================"
    log SUCCESS "Sprint $SPRINT_NUMBER Project Setup Complete!"
    echo "================================================"
    echo ""
    log INFO "Project Details:"
    echo "  📊 Name: $PROJECT_NAME"
    echo "  🔢 Number: $PROJECT_NUMBER"
    echo "  🔗 URL: $PROJECT_URL"
    echo ""
    log INFO "Sprint Details:"
    echo "  📅 Period: $SPRINT_START → $SPRINT_END"
    echo "  📋 Sprint: $SPRINT_NUMBER"
    echo ""
    log INFO "Created/Configured:"
    echo "  • 1 GitHub Project v2"
    echo "  • ${#CREATED_FIELDS[@]} Custom Fields"
    echo "  • ${#ADDED_ITEMS[@]} Issues Added"
    echo ""
    log INFO "Note: Automation workflows are in .github/workflows/"
    echo "      (sprint-automation.yml, ai-pr-reviewer.yml)"
    echo ""
    log INFO "Next Steps:"
    echo "  1. Open project: $PROJECT_URL"
    echo "  2. Create Board view (Kanban)"
    echo "  3. Invite team members"
    echo ""
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log WARN "This was a DRY RUN - no actual changes were made"
    fi
    
    log SUCCESS "🚀 Sprint $SPRINT_NUMBER is ready!"
}

usage() {
    cat << EOF
Usage: $SCRIPT_NAME [OPTIONS]

GitHub Projects v2 setup for Sprint 2 (Workflow-free version).

OPTIONS:
    -n, --sprint-number NUM     Sprint number (default: $SPRINT_NUMBER)
    -s, --sprint-name NAME      Sprint name (default: "$SPRINT_NAME")
    --start-date DATE           Sprint start date (default: $SPRINT_START)
    --end-date DATE             Sprint end date (default: $SPRINT_END)
    -r, --repo OWNER/REPO       Repository (default: $REPO)
    --dry-run                   Show what would be done without making changes
    -v, --verbose               Enable verbose logging
    -h, --help                  Show this help message

VERSION: $SCRIPT_VERSION
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -n|--sprint-number) SPRINT_NUMBER="$2"; shift 2 ;;
            -s|--sprint-name) SPRINT_NAME="$2"; shift 2 ;;
            --start-date) SPRINT_START="$2"; shift 2 ;;
            --end-date) SPRINT_END="$2"; shift 2 ;;
            -r|--repo) REPO="$2"; shift 2 ;;
            --dry-run) DRY_RUN=true; shift ;;
            -v|--verbose) VERBOSE=true; shift ;;
            -h|--help) usage; exit 0 ;;
            *) log ERROR "Unknown option: $1"; usage; exit 1 ;;
        esac
    done
    PROJECT_NAME="Cobalt Sprint $SPRINT_NUMBER: $SPRINT_NAME"
}

main() {
    parse_args "$@"
    
    echo "🎯 $SCRIPT_NAME v$SCRIPT_VERSION"
    echo "=================================================="
    echo ""
    
    TMPDIR=$(mktemp -d -t sprint-setup-XXXXXX)
    
    check_dependencies
    validate_inputs
    
    log INFO "Configuration:"
    log INFO "  Repository: $REPO"
    log INFO "  Sprint: $SPRINT_NUMBER ($SPRINT_NAME)"
    log INFO "  Project: $PROJECT_NAME"
    log INFO "  Period: $SPRINT_START → $SPRINT_END"
    [[ "$DRY_RUN" == "true" ]] && log WARN "Mode: DRY RUN"
    echo ""
    
    local existing_project=""
    if find_existing_project; then
        existing_project=$(gh project list --owner="$(echo "$REPO" | cut -d'/' -f1)" --format=json 2>/dev/null | \
            jq -r --arg name "$PROJECT_NAME" '.projects[] | select(.title == $name) | .number' | head -n1)
        
        log WARN "Project '$PROJECT_NAME' already exists (#$existing_project)"
        read -p "Use existing project? (Y/n): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            log INFO "Exiting."
            exit 0
        fi
        
        load_existing_project "$existing_project"
    else
        create_project || exit 1
    fi
    
    configure_fields || exit 1
    get_sprint_issues || exit 1
    add_all_issues
    
    show_summary
    
    trap - EXIT
    cleanup_temp
    
    exit 0
}

main "$@"
