# GitHub Projects Roadmap Configuration

## Project Views

### 1. Board View (Kanban)
```
Columns:
├── Backlog (Future sprints)
├── Sprint Backlog (Current sprint)
├── To Do (Ready for work)
├── In Progress (Active work)
├── In Review (Code review)
├── Done (Completed)
└── Closed (Archived)
```

### 2. Roadmap View (Timeline)
```
Timeline bars for each sprint:
┌─────────────────────────────────────┐
│ Sprint 1: Foundation                │
│  Week 1                             │
├─────────────────────────────────────┤
│ Sprint 2: Auth UI                   │
│  Week 2                             │
├─────────────────────────────────────┤
│ Sprint 3: Downloads Dashboard       │
│  Week 3                             │
└─────────────────────────────────────┘
```

### 3. Table View (Spreadsheet)
```
Filters:
- By sprint label
- By priority
- By assignee
- By status
```

## Field Configuration

### Custom Fields
1. **Story Points** (Number)
   - Values: 1, 2, 3, 5, 8, 13, 20

2. **Priority** (Single select)
   - P0 - Critical
   - P1 - High  
   - P2 - Medium
   - P3 - Low

3. **Status** (Single select)
   - Not Started
   - In Progress
   - In Review
   - Done
   - Blocked

4. **Sprint** (Single select)
   - Sprint 1
   - Sprint 2
   - Sprint 3
   - Sprint 4
   - Sprint 5
   - Sprint 6
   - Sprint 7
   - Sprint 8

5. **Type** (Single select)
   - Feature
   - Bug
   - Task
   - Documentation
   - Infrastructure

## Automation Rules

### Issue Creation
```yaml
rules:
  - when: issue.opened
    if: contains(labels, "sprint-1")
    then: 
      - set_field: Status = "Not Started"
      - add_to_column: "Sprint Backlog"
```

### Status Updates
```yaml
rules:
  - when: issue.labeled
    if: label.name == "in-progress"
    then:
      - set_field: Status = "In Progress"
      - move_to_column: "In Progress"
  
  - when: issue.labeled  
    if: label.name == "needs-review"
    then:
      - set_field: Status = "In Review"
      - move_to_column: "In Review"
```

### Sprint Transitions
```yaml
rules:
  - when: milestone.closed
    then:
      - for_each: issue in milestone
        if: field.Status == "Done"
        then:
          - add_label: "closed"
          - move_to_column: "Closed"
```

## Views Configuration

### Board View Filters
```yaml
filters:
  - field: Sprint
    operator: equals
    value: "Sprint 1"
  - field: Status
    operator: not_equals
    value: "Closed"
```

### Roadmap View Settings
```yaml
timeline:
  start_field: "Sprint Start Date"
  end_field: "Sprint End Date"
  group_by: "Sprint"
  show_dependencies: true
```

### Table View Columns
```yaml
columns:
  - Title
  - Status
  - Story Points
  - Priority
  - Sprint
  - Assignee
  - Last Updated
```

## GitHub CLI Commands

### Project Setup
```bash
# Create project
gh project create --owner team21-vooglaadija \
  --title "YouTube Link Processor" \
  --description "8-week sprint plan" \
  --public

# Create views
# Note: GitHub CLI does not support creating project views.
# Create the Board, Roadmap, and Table views via the GitHub Projects web UI:
#   1. Open your project at https://github.com/orgs/{org}/projects/{number}
#   2. Click the view dropdown (top-left) → "New view"
#   3. Choose layout: Board (kanban), Roadmap (timeline), or Table (spreadsheet)
#   4. Name the view and configure filters/grouping as needed
#
# Alternatively, create views programmatically via the GraphQL API:
#   mutation {
#     createProjectView(input: {projectId: "PROJECT_ID", name: "Board", layout: BOARD_LAYOUT}) {
#       projectView { id name }
#     }
#   }
```

### Field Creation
```bash
# Create story points field
gh project field create --project-number 1 \
  --name "Story Points" \
  --data-type NUMBER

# Create priority field
gh project field create --project-number 1 \
  --name "Priority" \
  --data-type SINGLE_SELECT \
  --options "P0-Critical,P1-High,P2-Medium,P3-Low"
```

### Bulk Import Issues
```bash
# Import sprint 1 issues
cat > sprint1-issues.csv << EOF
Title,Description,Story Points,Priority,Sprint
"[SPRINT-1] Setup Jinja2 templates","Configure Jinja2 in FastAPI",2,P0,Sprint 1
"[SPRINT-1] Create base HTML layout","Create base.html with HTMX",3,P0,Sprint 1
"[SPRINT-1] Add basic CSS styling","Add Tailwind CSS",1,P1,Sprint 1
EOF

# Import to project
gh project item-add --project-number 1 --owner team21-vooglaadija \
  --format csv --file sprint1-issues.csv
```

## Webhook Configuration

### GitHub Actions Workflow
```yaml
# .github/workflows/project-sync.yml
name: Project Sync

on:
  issues:
    types: [opened, labeled, assigned, closed]
  pull_request:
    types: [opened, closed, labeled]

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Update Project Status
        uses: actions/github-script@v6
        with:
          script: |
            const issue = context.payload.issue || context.payload.pull_request;
            const projectId = "PROJECT_ID";
            
            // Update project item based on event
            await github.rest.projects.updateCard({
              card_id: issue.project_card_id,
              column_id: getColumnId(issue.state, issue.labels)
            });
```

### Status Badges
```markdown
![Sprint 1 Progress](https://img.shields.io/badge/Sprint_1-6%2F16_points-green)
![Overall Progress](https://img.shields.io/badge/Overall-6%2F85_points-blue)
![Velocity](https://img.shields.io/badge/Velocity-18_points%2Fsprint-orange)
```

## Reporting Scripts

### Burndown Chart Generator
```python
# scripts/burndown.py
import matplotlib.pyplot as plt

sprints = ["Sprint 1", "Sprint 2", "Sprint 3"]
planned = [16, 18, 17]
completed = [6, 0, 0]  # Update weekly

plt.plot(sprints, planned, label="Planned")
plt.plot(sprints, completed, label="Completed")
plt.title("Burndown Chart")
plt.xlabel("Sprint")
plt.ylabel("Story Points")
plt.legend()
plt.savefig("burndown.png")
```

### Velocity Calculator
```bash
# scripts/velocity.sh
#!/bin/bash
# Calculate velocity from last 3 sprints
SPRINT1_COMPLETED=16
SPRINT2_COMPLETED=18
SPRINT3_COMPLETED=17

VELOCITY=$(( ($SPRINT1_COMPLETED + $SPRINT2_COMPLETED + $SPRINT3_COMPLETED) / 3 ))
echo "Average Velocity: $VELOCITY points/sprint"
```

## Quick Links

- **Project Board**: https://github.com/orgs/team21-vooglaadija/projects/1
- **Roadmap**: https://github.com/orgs/team21-vooglaadija/projects/1/views/2
- **Issues**: https://github.com/team21-vooglaadija/vooglaadija/issues
- **Milestones**: https://github.com/team21-vooglaadija/vooglaadija/milestones

## Maintenance

### Weekly Tasks
1. Update issue statuses
2. Review blocked items
3. Update burndown chart
4. Check velocity

### Monthly Tasks
1. Review automation rules
2. Clean up closed items
3. Update field options
4. Backup project data

## Troubleshooting

### Common Issues
1. **Issues not appearing in project**
   - Check project permissions
   - Verify issue has correct labels
   - Check automation rules

2. **Roadmap not showing dates**
   - Ensure issues have start/end dates
   - Check field configuration
   - Verify timeline settings

3. **Automation not working**
   - Check webhook deliveries
   - Review rule conditions
   - Verify GitHub Actions permissions

