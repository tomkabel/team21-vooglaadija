# Sprint 1: Foundation - Issue Templates

## Sprint 1 Issues (Week 1)

### Issue 1: Setup Jinja2 templates
```markdown
Title: [SPRINT-1] Setup Jinja2 templates in FastAPI
Labels: sprint-1, task, P0
Story Points: 2
Assignee: 
Milestone: Sprint 1 - Foundation

## Description
Configure Jinja2Templates in FastAPI main.py and create basic template directory structure.

## Tasks
- [ ] Update `app/main.py` to include Jinja2 configuration
- [ ] Create `app/templates/` directory
- [ ] Create `app/templates/base.html` skeleton
- [ ] Create `app/templates/pages/` directory
- [ ] Test template rendering with simple "Hello World" page

## Dependencies
- None

## Definition of Done
- [ ] Jinja2 configured in main.py
- [ ] Template directories created
- [ ] Can render simple template
- [ ] Code reviewed
- [ ] Merged to main
```

### Issue 2: Create base HTML layout
```markdown
Title: [SPRINT-1] Create base HTML layout with HTMX
Labels: sprint-1, task, P0
Story Points: 3
Assignee: 
Milestone: Sprint 1 - Foundation

## Description
Create base.html template with HTMX script, navbar, footer, and content area.

## Tasks
- [ ] Create `app/templates/base.html` with HTML5 structure
- [ ] Add HTMX script from CDN
- [ ] Add Tailwind CSS from CDN
- [ ] Create navbar partial
- [ ] Create footer partial
- [ ] Add content block area
- [ ] Test layout renders correctly

## Dependencies
- Depends on Issue 1

## Definition of Done
- [ ] Base template created
- [ ] HTMX loads without errors
- [ ] Tailwind CSS applies
- [ ] Navbar and footer render
- [ ] Code reviewed
- [ ] Merged to main
```

### Issue 3: Add basic CSS styling
```markdown
Title: [SPRINT-1] Add basic CSS styling
Labels: sprint-1, task, P1
Story Points: 1
Assignee: 
Milestone: Sprint 1 - Foundation

## Description
Add custom CSS styling and configure static files.

## Tasks
- [ ] Create `app/static/css/styles.css`
- [ ] Add basic styling (colors, spacing)
- [ ] Configure static file serving in FastAPI
- [ ] Link CSS in base.html
- [ ] Test styling applies

## Dependencies
- Depends on Issue 2

## Definition of Done
- [ ] Custom CSS file created
- [ ] Static files configured
- [ ] Styling applies to pages
- [ ] Code reviewed
- [ ] Merged to main
```

## How to Create These Issues

### Using GitHub CLI
```bash
# Create Issue 1
gh issue create --title "[SPRINT-1] Setup Jinja2 templates in FastAPI" \
  --body-file .github/ISSUE_TEMPLATES/sprint1-issue1.md \
  --label "sprint-1,task,P0" \
  --milestone "Sprint 1 - Foundation"

# Create Issue 2  
gh issue create --title "[SPRINT-1] Create base HTML layout with HTMX" \
  --body-file .github/ISSUE_TEMPLATES/sprint1-issue2.md \
  --label "sprint-1,task,P0" \
  --milestone "Sprint 1 - Foundation"

# Create Issue 3
gh issue create --title "[SPRINT-1] Add basic CSS styling" \
  --body-file .github/ISSUE_TEMPLATES/sprint1-issue3.md \
  --label "sprint-1,task,P1" \
  --milestone "Sprint 1 - Foundation"
```

### Using GitHub Web Interface
1. Go to Issues → New Issue
2. Select "Sprint Task" template
3. Fill in details from above
4. Add labels: sprint-1, task, P0/P1
5. Set milestone: "Sprint 1 - Foundation"
6. Assign to team member

## Sprint 1 Completion Checklist

### Before Sprint Start
- [ ] All issues created
- [ ] Issues assigned to team members
- [ ] Dependencies identified
- [ ] Milestone created
- [ ] Project board configured

### During Sprint
- [ ] Daily standups happening
- [ ] Issues moving through columns
- [ ] Code reviews happening
- [ ] Blockers being addressed

### End of Sprint
- [ ] All issues in "Done" column
- [ ] Code merged to main
- [ ] Sprint review completed
- [ ] Retrospective completed
- [ ] Velocity calculated
- [ ] Next sprint planned

## Sprint 1 Success Metrics
- **Goal**: 16 story points completed
- **Acceptance**: All 3 issues done
- **Quality**: Code reviewed, tests passing
- **Timing**: Completed within 1 week

## Notes for Team
- Start with simple templates
- Test frequently
- Ask for help early
- Focus on completing, not perfecting

