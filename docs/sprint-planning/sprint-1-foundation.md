# Sprint 1: Foundation - HTMX Frontend Setup

**Sprint Goal**: Set up HTMX frontend infrastructure with Jinja2 templates, base layout, and basic styling to enable subsequent frontend development sprints.

**Duration**: April 1-7, 2026 (5 working days)

**Team**: 4 developers, 6 hours/day, Focus Factor 0.6

**Capacity Calculation**: 4 × 5 days × 6 hours × 0.6 = **72 hours** ≈ **18 story points**

---

## Sprint Backlog

| Story ID | Description | Points | Owner | Dependencies |
|----------|-------------|--------|-------|--------------|
| FE-001 | Configure Jinja2 templates in main.py | 2 | TBD | None |
| FE-002 | Create base.html with navbar, footer, content area | 3 | TBD | FE-001 |
| FE-003 | Add HTMX script to base template | 1 | TBD | FE-002 |
| FE-004 | Create static CSS with basic styling | 3 | TBD | FE-002 |
| FE-005 | Create index.html home page | 2 | TBD | FE-002 |
| FE-006 | Create error.html error page template | 2 | TBD | FE-002 |
| FE-007 | Set up page routes in api/routes/pages.py | 3 | TBD | FE-001 |
| FE-008 | Create HTMX middleware helper | 2 | TBD | FE-003 |
| FE-009 | Verify templates render in browser | 2 | TBD | FE-007 |
| FE-010 | Project setup - create templates directory structure | 1 | TBD | None |

**Total Committed**: 16 points

---

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Jinja2 configuration issues | Medium | High | Research FastAPI template setup beforehand |
| CSS framework selection debate | Medium | Medium | Use Tailwind CDN, avoid custom framework |
| Team unfamiliar with HTMX | High | Medium | Assign FE-003 as pair programming task |
| Static files not loading | Low | High | Test early in sprint |
| Short sprint (5 days) | - | High | Focus only on committed stories |

---

## Definition of Done

- [ ] Jinja2 templates render without errors
- [ ] HTMX script loads in browser console
- [ ] Base layout displays navbar, content area, footer
- [ ] Basic CSS styling applies to pages
- [ ] Index page accessible at root URL
- [ ] Error page template works for 404/500
- [ ] Code reviewed by at least one team member
- [ ] Changes tested locally with docker-compose

---

## Technical Notes

### File Structure to Create

```
app/templates/
├── base.html
├── pages/
│   ├── index.html
│   └── error.html
└── static/
    └── css/
        └── styles.css
```

### Key Implementation Details

1. **Jinja2 Setup** (main.py):
   - Add Jinja2Templates from starlette
   - Configure template directory path
   - Add static file serving

2. **Base Template** (base.html):
   - Include HTMX from CDN
   - Include Bootstrap Icons or similar
   - Create responsive navbar placeholder
   - Add content block for child templates
   - Add flash message display area

3. **CSS Styling** (styles.css):
   - Reset/Normalize
   - Typography basics
   - Navbar styling
   - Container/layout utilities
   - Button styles

---

## GitHub Artifacts

| Artifact | Link |
|----------|------|
| **Milestone** | https://github.com/tomkabel/team21-vooglaadija/milestone/7 |
| **Project Board** | https://github.com/users/tomkabel/projects/5 |
| **Issue: BACKLOG-01** | https://github.com/tomkabel/team21-vooglaadija/issues/54 |
| **Issue: BACKLOG-02** | https://github.com/tomkabel/team21-vooglaadija/issues/55 |
| **Issue: BACKLOG-03** | https://github.com/tomkabel/team21-vooglaadija/issues/56 |

## Related Roadmap Items

This sprint addresses **Week 1: Foundation** from PROJECT_ROADMAP.md.

**Time Estimate from Roadmap**: 4-6 hours per person → Adjusted to 16 points for team coordination

---

## Next Sprint Preview

Following Sprint 1, the team should proceed to **Sprint 2: Authentication UI** (April 8-14) which includes:
- Login page with form
- Register page with form
- CSRF protection
- Auth error handling

**Sprint 2 Planning Documents**:
- [sprint-2-auth-ui.md](./sprint-2-auth-ui.md) - Detailed sprint plan
- [sprint-2-planning-agenda.md](./sprint-2-planning-agenda.md) - Planning meeting agenda