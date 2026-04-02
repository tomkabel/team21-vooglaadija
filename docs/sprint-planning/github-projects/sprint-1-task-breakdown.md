# GitHub Projects Board Setup

## Sprint 1 Task Breakdown

**Sprint**: 1 - Foundation  
**Dates**: April 1-7, 2026 (5 working days)  
**Team**: 4 developers

### Board Structure

Create a GitHub Project (classic) or use GitHub Projects (beta) with these columns:

| Column | Description |
|--------|-------------|
| **To Do** | Ready to work on, not started |
| **In Progress** | Currently working on |
| **In Review** | Pull request open, awaiting review |
| **Done** | Completed and merged |

---

## Task Breakdown by Story

### BACKLOG-01: Set up Jinja2 templates in FastAPI (2 points)

| Task | Description | Time | Status |
|------|-------------|------|--------|
| T-001 | Create app/templates directory structure | 15min | ⬜ |
| T-002 | Import Jinja2Templates in main.py | 15min | ⬜ |
| T-003 | Configure template directory path | 15min | ⬜ |
| T-004 | Mount static files at /static | 15min | ⬜ |
| T-005 | Create test template (index.html) | 15min | ⬜ |
| T-006 | Add test route in main.py | 15min | ⬜ |
| T-007 | Verify template renders | 15min | ⬜ |
| T-008 | Code review | 30min | ⬜ |

**Total estimated time**: ~2 hours

---

### BACKLOG-02: Create base HTML layout with HTMX (3 points)

| Task | Description | Time | Status |
|------|-------------|------|--------|
| T-009 | Create base.html template | 30min | ⬜ |
| T-010 | Add HTMX CDN script | 10min | ⬜ |
| T-011 | Add Bootstrap CDN links | 10min | ⬜ |
| T-012 | Create navbar structure | 30min | ⬜ |
| T-013 | Create content block | 10min | ⬜ |
| T-014 | Create footer | 10min | ⬜ |
| T-015 | Add flash message partial | 20min | ⬜ |
| T-016 | Create pages/index.html extending base | 20min | ⬜ |
| T-017 | Create pages/error.html extending base | 20min | ⬜ |
| T-018 | Test layout in browser | 15min | ⬜ |
| T-019 | Code review | 30min | ⬜ |

**Total estimated time**: ~3 hours

---

### BACKLOG-03: Add basic CSS styling (1 point)

| Task | Description | Time | Status |
|------|-------------|------|--------|
| T-020 | Add Tailwind CSS CDN to base.html | 10min | ⬜ |
| T-021 | Create app/static/css/ directory | 5min | ⬜ |
| T-022 | Create styles.css with CSS variables | 15min | ⬜ |
| T-023 | Add navbar custom styles | 20min | ⃝ |
| T-024 | Add button styles | 15min | ⬜ |
| T-025 | Add form input styles | 15min | ⬜ |
| T-026 | Test styles on base template | 10min | ⬜ |
| T-027 | Code review | 15min | ⬜ |

**Total estimated time**: ~1.5 hours

---

## GitHub Project Setup Instructions

### Option A: GitHub Projects (Beta) - Recommended

```bash
# 1. Create new project
gh project create --title "YouTube Link Processor" --type board

# 2. Add columns via UI or API
# Columns: To Do, In Progress, In Review, Done

# 3. Add iteration (Sprint 1)
# Settings > Iterations > Add iteration > Apr 1 - Apr 7, 2026

# 4. Add field: Story Points (number)
# Settings > Fields > Add field > Number
```

### Option B: GitHub Project (Classic)

```bash
# 1. Navigate to repo > Projects > New project
# 2. Choose "Team project" for collaboration
# 3. Add columns: To Do, In Progress, In Review, Done
# 4. Pin to repo for visibility
```

### Adding Issues to Project

```bash
# Add individual issues
gh issue edit BACKLOG-01 --project "YouTube Link Processor" --add

# Or via project item add
gh project item-add #PROJECT_NUMBER --issue #ISSUE_NUMBER

# Bulk add via script (see below)
```

---

## Bulk Issue Creation Script

Run this to create all Sprint 1 issues:

```bash
#!/bin/bash
# create-sprint-1-issues.sh

REPO="team21-vooglaadija/vooglaadija"

# BACKLOG-01
gh issue create \
  --repo "$REPO" \
  --title "[BACKLOG-01] Set up Jinja2 templates in FastAPI" \
  --body "## Story
As a frontend developer, I want FastAPI configured with Jinja2 templates so I can render HTML pages.

## Points: 2

## Acceptance Criteria
- [ ] Jinja2Templates imported and configured in main.py
- [ ] Template directory path correctly set to app/templates
- [ ] Static files mounted at /static path
- [ ] Simple test template renders successfully

## Dependencies: None

## Tasks:
- [ ] Create app/templates directory
- [ ] Add Jinja2Templates configuration
- [ ] Mount static files
- [ ] Create test index.html
- [ ] Verify renders" \
  --label "sprint-1" \
  --label "frontend"

# Repeat for BACKLOG-02, BACKLOG-03...
```

---

## Task-to-Issue Mapping

| Task ID | Description | Issue | Assignee |
|---------|-------------|-------|----------|
| T-001 | Create app/templates directory | BACKLOG-01 | |
| T-002 | Import Jinja2Templates in main.py | BACKLOG-01 | |
| T-003 | Configure template directory path | BACKLOG-01 | |
| T-004 | Mount static files at /static | BACKLOG-01 | |
| T-005 | Create test template (index.html) | BACKLOG-01 | |
| T-006 | Add test route in main.py | BACKLOG-01 | |
| T-007 | Verify template renders | BACKLOG-01 | |
| T-008 | Code review for BACKLOG-01 | BACKLOG-01 | |
| T-009 | Create base.html template | BACKLOG-02 | |
| T-010 | Add HTMX CDN script | BACKLOG-02 | |
| T-011 | Add Bootstrap CDN links | BACKLOG-02 | |
| T-012 | Create navbar structure | BACKLOG-02 | |
| T-013 | Create content block | BACKLOG-02 | |
| T-014 | Create footer | BACKLOG-02 | |
| T-015 | Add flash message partial | BACKLOG-02 | |
| T-016 | Create pages/index.html | BACKLOG-02 | |
| T-017 | Create pages/error.html | BACKLOG-02 | |
| T-018 | Test layout in browser | BACKLOG-02 | |
| T-019 | Code review for BACKLOG-02 | BACKLOG-02 | |
| T-020 | Add Tailwind CSS CDN | BACKLOG-03 | |
| T-021 | Create app/static/css/ directory | BACKLOG-03 | |
| T-022 | Create styles.css | BACKLOG-03 | |
| T-023 | Add navbar custom styles | BACKLOG-03 | |
| T-024 | Add button styles | BACKLOG-03 | |
| T-025 | Add form input styles | BACKLOG-03 | |
| T-026 | Test styles | BACKLOG-03 | |
| T-027 | Code review for BACKLOG-03 | BACKLOG-03 | |

---

## Definition of Done Checklist

For each story to be marked Done:

- [ ] All tasks completed
- [ ] Code compiles/runs without errors
- [ ] Features work as described in acceptance criteria
- [ ] PR reviewed and approved
- [ ] Merged to main branch
- [ ] Tested on local environment
- [ ] Documentation updated (if needed)