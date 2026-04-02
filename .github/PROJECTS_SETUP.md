# GitHub Projects Setup

## Project Board Structure

Create a GitHub Project with these columns:

### Status Columns
1. **Backlog** - All upcoming tasks
2. **Sprint Backlog** - Current sprint tasks
3. **To Do** - Ready for work
4. **In Progress** - Currently being worked on
5. **In Review** - Code review needed
6. **Done** - Completed this sprint
7. **Closed** - Completed in previous sprints

### Views
1. **Board View** - Kanban board
2. **Roadmap View** - Timeline of sprints
3. **Table View** - All items with filters

## Labels to Create

### Priority
- P0 - Critical
- P1 - High
- P2 - Medium
- P3 - Low

### Type
- feature
- bug
- task
- documentation
- infrastructure

### Sprint
- sprint-1
- sprint-2
- sprint-3
- sprint-4
- sprint-5
- sprint-6
- sprint-7
- sprint-8

### Status
- blocked
- needs-review
- ready-for-testing

## Milestones

Create milestones for each sprint:
- Sprint 1 - Foundation (Week 1)
- Sprint 2 - Auth UI (Week 2)
- Sprint 3 - Downloads Dashboard (Week 3)
- Sprint 4 - Real-time Updates (Week 4)
- Sprint 5 - Validation (Week 5)
- Sprint 6 - Documentation (Week 6)
- Sprint 7 - Testing (Week 7)
- Sprint 8 - AWS Deployment (Week 8)

## Automation Rules

Set up these automation rules:

1. **When issue is created with "sprint-1" label** → Move to "Sprint Backlog"
2. **When issue is assigned** → Move to "To Do"
3. **When issue label changes to "in-progress"** → Move to "In Progress"
4. **When issue label changes to "needs-review"** → Move to "In Review"
5. **When issue is closed** → Move to "Done"
6. **When sprint ends** → Move all "Done" to "Closed"

## Daily Workflow

### Morning Standup
1. Check "In Progress" column
2. Update status in issue comments
3. Move blocked items to "Blocked" column

### During Day
1. Pick task from "To Do"
2. Add "in-progress" label
3. Create branch: `git checkout -b feature/issue-number-description`
4. Work on task
5. When ready for review: add "needs-review" label

### Code Review
1. Reviewer checks "In Review" column
2. Reviews code
3. If approved: remove "needs-review", add "ready-for-merge"
4. If changes needed: add comments, move back to "In Progress"

### End of Day
1. Update issue status
2. Move completed tasks to "In Review" or "Done"
3. Plan next day tasks

## Sprint Planning Workflow

### Before Sprint
1. Create milestone for sprint
2. Create issues for all stories
3. Add sprint label (e.g., "sprint-1")
4. Add story point estimates
5. Assign initial owners

### Sprint Planning Meeting
1. Review backlog items
2. Discuss dependencies
3. Assign tasks
4. Move selected items to "Sprint Backlog"

### Sprint Review
1. Review all "Done" items
2. Demo completed features
3. Update velocity tracking
4. Move "Done" to "Closed"

### Retrospective
1. What went well?
2. What could be improved?
3. Action items for next sprint

## GitHub Actions Integration

Create `.github/workflows/sprint-automation.yml`:

```yaml
name: Sprint Automation

on:
  issues:
    types: [labeled, unlabeled, assigned, closed]
  pull_request:
    types: [opened, closed, labeled, unlabeled]

jobs:
  update-project:
    runs-on: ubuntu-latest
    steps:
      - name: Update Project Board
        uses: actions/github-script@v6
        with:
          script: |
            // Automation logic here
```

## Reporting

### Daily Reports
- Burndown chart
- Velocity tracking
- Blocked items

### Sprint Reports
- Completed vs planned
- Velocity trend
- Bug count
- Code review time

## Quick Start Commands

```bash
# Create issue for sprint task
gh issue create --title "[SPRINT-1] Setup Jinja2 templates" \
  --body-file .github/ISSUE_TEMPLATE/sprint-task.md \
  --label "sprint-1,task,P0" \
  --assignee @username

# Move issue to project
gh issue edit 123 --add-project "YouTube Link Processor"

# Create milestone
gh api repos/:owner/:repo/milestones --field title="Sprint 1" \
  --field description="Foundation sprint" \
  --field due_on="2024-01-15T00:00:00Z"

# List sprint issues
gh issue list --label "sprint-1" --state open
```

## Template Issues

Copy these to get started quickly:

### Sprint 1 Issues
```markdown
Title: [SPRINT-1] Setup Jinja2 templates in FastAPI
Labels: sprint-1, task, P0
Points: 2
Description: Configure Jinja2Templates in main.py and create basic template structure
```

```markdown
Title: [SPRINT-1] Create base HTML layout with HTMX
Labels: sprint-1, task, P0
Points: 3
Description: Create base.html with HTMX script, navbar, footer, and content area
```

```markdown
Title: [SPRINT-1] Add basic CSS styling
Labels: sprint-1, task, P1
Points: 1
Description: Add Tailwind CSS via CDN and custom styles.css
```

## Tips

1. **Keep issues small** - 1-3 points max
2. **Update daily** - Status should reflect reality
3. **Use labels consistently** - Makes filtering easy
4. **Link PRs to issues** - `Closes #123` in PR description
5. **Review regularly** - Dont let issues stagnate

