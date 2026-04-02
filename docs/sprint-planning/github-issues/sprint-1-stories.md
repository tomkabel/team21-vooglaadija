# GitHub Issues - Sprint 1 Stories

## Overview

This directory contains GitHub Issue templates for Sprint 1 stories. Use these as templates when creating issues in the repository.

---

## Issue Labels

Apply these labels to all Sprint 1 issues:

- `sprint-1`
- `frontend`
- `htmx`

Additional per-issue labels:
- `backend` - if API changes required
- `security` - if security considerations
- `docs` - if documentation only

---

## Story Issues

### BACKLOG-01: Set up Jinja2 templates in FastAPI

```markdown
## Story
As a frontend developer, I want FastAPI configured with Jinja2 templates so I can render HTML pages.

## Points: 2

## Acceptance Criteria
- [ ] Jinja2Templates imported and configured in main.py
- [ ] Template directory path correctly set to app/templates
- [ ] Static files mounted at /static path
- [ ] Simple test template renders successfully
- [ ] No errors in logs when accessing template routes

## Technical Notes
- Use Starlette's Jinja2Templates
- Set template folder to Path(__file__).parent / "templates"
- Use app.mount for static files mounting

## Dependencies
None

## Todo
- [ ] Create app/templates directory
- [ ] Add Jinja2Templates configuration to main.py
- [ ] Mount static files
- [ ] Create test index.html
- [ ] Verify renders at /test route
- [ ] Get code review
```

### BACKLOG-02: Create base HTML layout with HTMX

```markdown
## Story
As a user, I want a consistent base layout so all pages have consistent navigation and styling.

## Points: 3

## Acceptance Criteria
- [ ] base.html exists in app/templates/
- [ ] HTMX script included from CDN
- [ ] Bootstrap Icons or similar icon library included
- [ ] Navbar with placeholder links (Login, Register)
- [ ] Main content area using {% block content %}
- [ ] Footer with copyright
- [ ] Flash message display area
- [ ] Base layout renders without errors

## Technical Notes
- Include HTMX: https://unpkg.com/htmx.org@1.9.10/dist/htmx.min.js
- Use Bootstrap 5 CSS/JS via CDN for rapid development
- Structure: header > nav, main > content, footer

## Dependencies
- BACKLOG-01 (Jinja2 setup must be complete)

## Todo
- [ ] Create base.html template
- [ ] Add HTMX script tag
- [ ] Add Bootstrap CSS/JS CDN links
- [ ] Create navbar structure
- [ ] Create content block
- [ ] Create footer
- [ ] Add flash message partial
- [ ] Test with child template
- [ ] Get code review
```

### BACKLOG-03: Add basic CSS styling

```markdown
## Story
As a user, I want basic CSS styling so the application looks professional and is easy to use.

## Points: 1

## Acceptance Criteria
- [ ] styles.css created in app/static/css/
- [ ] Custom styles for navbar
- [ ] Container and layout utilities
- [ ] Button styles
- [ ] Form styling
- [ ] Alert/message styling
- [ ] Styles load correctly on pages

## Technical Notes
- Use Tailwind CSS via CDN for utility classes (simplest approach)
- Add custom styles in app/static/css/styles.css for overrides
- Focus on: navbar colors, button styles, form inputs, alert boxes

## Dependencies
- BACKLOG-02 (base layout must exist)

## Todo
- [ ] Add Tailwind CSS CDN to base.html
- [ ] Create app/static/css/ directory
- [ ] Create styles.css with custom variables
- [ ] Add navbar styling
- [ ] Add button styles
- [ ] Add form input styles
- [ ] Test styles on base template
- [ ] Get code review
```

---

## GitHub Issue Links

| Story ID | GitHub Issue | Points | Labels | Status |
|----------|--------------|--------|--------|--------|
| BACKLOG-01 | [#54](https://github.com/tomkabel/team21-vooglaadija/issues/54) | 2 | sprint-1, frontend, P0 | To Do |
| BACKLOG-02 | [#55](https://github.com/tomkabel/team21-vooglaadija/issues/55) | 3 | sprint-1, frontend, P0 | To Do |
| BACKLOG-03 | [#56](https://github.com/tomkabel/team21-vooglaadija/issues/56) | 1 | sprint-1, frontend, P1 | To Do |

## Project Board

**Project**: https://github.com/users/tomkabel/projects/5

**Milestone**: https://github.com/tomkabel/team21-vooglaadija/milestone/7

---

## Manual Setup Required

### Add Iteration Field (GitHub UI)

1. Go to Project Settings → Fields → New field
2. Field type: **Iteration**
3. Name: `Sprint 1`
4. Duration: 7 days
5. Start date: April 1, 2026

### Add Issues to Project (CLI)

```bash
# Add issue to project
gh project item-add 5 --issue 54
gh project item-add 5 --issue 55
gh project item-add 5 --issue 56
```

### Update Issue Status

Move issues to appropriate columns:
- BACKLOG-01, BACKLOG-02, BACKLOG-03 → "To Do"