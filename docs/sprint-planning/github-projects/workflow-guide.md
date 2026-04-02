# GitHub Projects Workflow

## Overview

This guide covers using GitHub Projects (beta) for sprint tracking with automation.

---

## Project Structure

```
YouTube Link Processor
├── Current Sprint (Sprint 1)
│   ├── To Do
│   ├── In Progress
│   ├── In Review
│   └── Done
└── Backlog
```

---

## Setting Up GitHub Projects (Beta)

### 1. Create Project

```bash
# Using GitHub CLI
gh project create --title "YouTube Link Processor" --type board

# Or via web:
# repo > Projects > New project > Board
```

### 2. Configure Fields

Add these custom fields:

| Field | Type | Description |
|-------|------|-------------|
| Sprint | Single select | Sprint number (1-8) |
| Story Points | Number | Fibonacci points |
| Priority | Single select | P0, P1, P2 |
| Iteration | Iteration | Sprint date range |

### 3. Create Views

- **Sprint Board**: Current sprint filtered view
- **Backlog**: All unstarted items
- **All Items**: Complete project view

---

## Workflow for Stories

### Creating a Story Issue

```bash
# Create issue with labels
gh issue create \
  --title "[BACKLOG-01] Set up Jinja2 templates" \
  --body "$(cat docs/sprint-planning/github-issues/backlog-01.md)" \
  --label "sprint-1" \
  --label "frontend"

# Add to project
gh project item-add #PROJECT_NUMBER --issue #ISSUE_NUMBER
```

### Workflow States

```
┌─────────┐    ┌─────────────┐    ┌───────────┐    ┌──────┐
│ To Do   │───▶│ In Progress │───▶│ In Review │───▶│ Done │
└─────────┘    └─────────────┘    └───────────┘    └──────┘
     │              │                  │              │
     │              │                  │              ▼
     │              │                  │         [MERGED]
     │              │                  │
     ▼              ▼                  ▼
  [BLOCKED]    [TASK CANCELLED]   [CHANGES REQUESTED]
```

### Daily Workflow

1. **Morning**: Move today's tasks to "In Progress"
2. **Work**: Update status as you progress
3. **PR**: Move to "In Review" when PR opened
4. **Merge**: Move to "Done" when merged

---

## Automation Rules

### Rule 1: Auto-add to Sprint 1

```javascript
// .github/project-automation/sprint1.yml
on:
  issues:
    types: [opened, labeled]
prs:
  types: [opened, labeled]

jobs:
  automate-project:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/add-to-project@v1
        with:
          project-url: ${{ secrets.PROJECT_URL }}
          github-token: ${{ secrets.GH_PROJECTS_TOKEN }}
          labeled: sprint-1
          label-operator: OR
```

### Rule 2: Move to Done on Merge

```javascript
// .github/workflows/sprint-sync.yml
name: Sync PR to Project
on:
  pull_request:
    types: [closed]

jobs:
  move-done:
    if: github.event.pull_request.merged == true
    runs-on: ubuntu-latest
    steps:
      - uses: actions/add-to-project@v1
        with:
          project-url: ${{ secrets.PROJECT_URL }}
          github-token: ${{ secrets.GH_PROJECTS_TOKEN }}
```

---

## Manual Commands

### Move Issue to Column

```bash
# Get project and item IDs
gh project item-list #PROJECT_NUMBER

# Move item (using GraphQL)
gh api graphql -f query='
  mutation {
    updateProjectV2ItemFieldValue(input: {
      projectId: "PVT_..."
      itemId: "PVTITEM_..."
      fieldId: "PVTTF_..."
      value: { singleSelectOptionId: "Sprint" }
    }) {
      projectV2Item { id }
    }
  }'
```

---

## GitHub Actions for Sprint Sync

### Daily Standup Report

```yaml
# .github/workflows/standup-report.yml
name: Daily Standup Report
on:
  schedule:
    - cron: '30 8 * * 1-5'  # 8:30 AM Mon-Fri

jobs:
  standup:
    runs-on: ubuntu-latest
    steps:
      - name: Generate Report
        run: |
          echo "## Daily Standup - $(date +%Y-%m-%d)" >> $GITHUB_STEP_SUMMARY
          echo "### In Progress" >> $GITHUB_STEP_SUMMARY
          gh issue list --assignee @me --state open --label "sprint-1" --json title,labels
```

---

## Quick Reference

### Common Commands

```bash
# List all issues in project
gh project item-list #PROJECT_NUMBER

# List issues by status
gh issue list --label "sprint-1" --state open

# Add issue to project
gh project item-add #PROJECT_NUMBER --issue #ISSUE_NUMBER

# View project
gh project view #PROJECT_NUMBER
```

### Labels Used

| Label | Purpose |
|-------|---------|
| `sprint-1` through `sprint-8` | Sprint assignment |
| `frontend` | Frontend work |
| `backend` | Backend work |
| `bug` | Bug fixes |
| `docs` | Documentation |

---

## GitHub Projects Setup Checklist

- [x] Create GitHub Project board (https://github.com/users/tomkabel/projects/5)
- [x] Add columns: To Do, In Progress, In Review, Done
- [ ] Add custom fields: Sprint, Story Points, Priority
- [ ] Create Sprint 1 iteration (Apr 1-7, 2026) - requires UI or GraphQL
- [x] Add all Sprint 1 stories to board (#54, #55, #56)
- [ ] Set up automation (optional)
- [ ] Create project view for current sprint
- [ ] Pin project to repo
- [ ] Add team members to project

---

## Tips

1. **Keep board clean**: Archive or close completed items
2. **Update daily**: Move items as work progresses
3. **Use labels**: Filter views by labels
4. **Review weekly**: Check for stale items
5. **Automate**: Use GitHub Actions for repetitive tasks