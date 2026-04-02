# Project Sprint Overview

## YouTube Link Processor - Sprint Planning

Based on PROJECT_ROADMAP.md assessment (Updated: April 1, 2026)

---

## Project Status Summary

### Completed (Backend)
- FastAPI backend with async patterns
- JWT authentication (register, login, refresh)
- Redis queue for job processing
- Worker process for yt-dlp
- PostgreSQL database
- Docker compose setup
- Basic CI/CD with GitHub Actions

### In Progress
- None - Starting fresh sprint

### Not Started (Frontend)
- HTMX web UI
- Error handling
- Input validation
- Rate limiting (beyond auth endpoints)
- File management

---

## Recommended Sprint Sequence

| Sprint | Name | Dates | Focus |
|--------|------|-------|-------|
| 1 | Foundation | Apr 1-7 | HTMX + Templates setup |
| 2 | Authentication UI | Apr 8-14 | Login/Register pages |
| 3 | Downloads Dashboard | Apr 15-21 | Downloads list + forms |
| 4 | Job Status & Polling | Apr 22-28 | Real-time updates |
| 5 | Validation & Error Handling | Apr 29 - May 5 | Robust UX |
| 6 | Swagger & Documentation | May 6-12 | API docs |
| 7 | Testing & Polish | May 13-19 | Manual testing |
| 8 | AWS (Optional) | May 20-21 | Cloud deployment (2 days) |

**Note**: Sprint 8 (AWS) only if required by assignment. Abbreviated to 2 days due to project deadline (May 23).

---

## Sprint 1: Foundation

**Status**: Planned

**Goal**: Set up HTMX frontend infrastructure with Jinja2 templates, base layout, and basic styling

**Duration**: April 1-7, 2026 (5 working days)

**Capacity**: 18 story points (4 team members × 5 days × 6 hours × 0.6 focus)

### Sprint 1 Stories

| Story ID | Description | Points |
|----------|-------------|--------|
| FE-001 | Configure Jinja2 templates in main.py | 2 |
| FE-002 | Create base.html with navbar, footer, content area | 3 |
| FE-003 | Add HTMX script to base template | 1 |
| FE-004 | Create static CSS with basic styling | 3 |
| FE-005 | Create index.html home page | 2 |
| FE-006 | Create error.html error page template | 2 |
| FE-007 | Set up page routes in api/routes/pages.py | 3 |
| FE-008 | Create HTMX middleware helper | 2 |
| FE-009 | Verify templates render in browser | 2 |
| FE-010 | Project setup - create templates directory structure | 1 |

---

## Story Point Estimation Reference

### Modified Fibonacci Scale
- **1**: Simple task, well understood
- **2**: Small task, some uncertainty
- **3**: Normal task, clear scope
- **5**: Large task, some complexity
- **8**: Very large task, significant complexity
- **13**: Major feature, high uncertainty
- **20**: Epic, needs breakdown

### Velocity Guidelines
- Sprint 1: ~21 points (baseline)
- Sprint 2+: Adjust based on Sprint 1 actual velocity

---

## Definition of Done (All Sprints)

- [ ] Code follows project coding standards
- [ ] Code reviewed by at least one team member
- [ ] Tests passing (where applicable)
- [ ] Works locally with docker-compose
- [ ] Added to sprint retrospective notes

---

## Capacity Planning Example

For a 2-week sprint with 4 developers:

```
Team Size: 4 developers
Working Days: 10 days (2 weeks - weekends)
Hours per Day: 6 hours
Focus Factor: 0.7 (accounts for meetings, code review, etc.)

Total Hours = 4 × 10 × 6 × 0.7 = 168 hours
Story Points = ~21 (based on ~8 hours per point)
---

## Sprint 2: Authentication UI

**Status**: Planned

**Goal**: Users can register and login via web interface with proper form handling, CSRF protection, and user-friendly error messages.

**Duration**: April 8-14, 2026 (5 working days)

**Capacity**: 10 story points (4 team members × 5 days × 6 hours × 0.6 focus)

### Sprint 2 Stories

| Story ID | Description | Points |
|----------|-------------|--------|
| BACKLOG-04 | Create login page with HTMX form | 3 |
| BACKLOG-05 | Create register page with HTMX form | 3 |
| BACKLOG-06 | Add CSRF protection for forms | 2 |
| BACKLOG-07 | Handle auth errors with user feedback | 2 |

---

## Sprint 3: Downloads Dashboard

**Status**: Planned

**Goal**: Users can view their download history and create new download jobs via a web interface.

**Duration**: April 15-21, 2026 (5 working days)

**Capacity**: 8 story points

### Sprint 3 Stories

| Story ID | Description | Points |
|----------|-------------|--------|
| BACKLOG-08 | Create downloads list page | 3 |
| BACKLOG-09 | Create download form | 2 |
| BACKLOG-10 | Implement job status display | 2 |
| BACKLOG-11 | Add logout functionality | 1 |

### GitHub Issues

| Issue | Title |
|-------|-------|
| #61 | BACKLOG-08: Create downloads list page |
| #62 | BACKLOG-09: Create download form |
| #63 | BACKLOG-10: Implement job status display |
| #64 | BACKLOG-11: Add logout functionality |

---

## Sprint 4: Real-time Status Updates

**Status**: Planned

**Goal**: Job status updates automatically without page refresh using HTMX polling.

**Duration**: April 22-28, 2026 (5 working days)

**Capacity**: 7 story points

### Sprint 4 Stories

| Story ID | Description | Points |
|----------|-------------|--------|
| BACKLOG-12 | Implement status polling (every 3s) | 3 |
| BACKLOG-13 | Add loading indicators | 1 |
| BACKLOG-14 | Display errors for failed jobs | 2 |
| BACKLOG-15 | Add manual refresh button | 1 |

### GitHub Issues

| Issue | Title |
|-------|-------|
| #65 | BACKLOG-12: Implement status polling (every 3s) |
| #66 | BACKLOG-13: Add loading indicators |
| #67 | BACKLOG-14: Display errors for failed jobs |
| #68 | BACKLOG-15: Add manual refresh button |

---

## Next Steps

1. Team reviews Sprint 1 backlog
2. Assign story owners
3. Schedule sprint planning meeting
4. Set up task board (GitHub Projects or similar)
5. Define sprint start date (recommended: April 1, 2026)

---

*This document should be updated after each sprint with actual velocity and lessons learned.*