# GitHub Projects Board Setup - Sprint 3

## Sprint 3 Task Breakdown

**Sprint**: 3 - Downloads Dashboard  
**Dates**: April 15-21, 2026 (5 working days)  
**Team**: 4 developers

### Board Structure

| Column | Description |
|--------|-------------|
| **To Do** | Ready to work on, not started |
| **In Progress** | Currently working on |
| **In Review** | Pull request open, awaiting review |
| **Done** | Completed and merged |

---

## Task Breakdown by Story

### BACKLOG-08: Create downloads list page (3 points)

| Task | Description | Time | Status |
|------|-------------|------|--------|
| T-201 | Create GET /downloads route in pages.py | 30min | ⬜ |
| T-202 | Create pages/downloads.html template | 45min | ⬜ |
| T-203 | Query user's downloads from database | 30min | ⬜ |
| T-204 | Render download list with Jinja2 loop | 20min | ⬜ |
| T-205 | Add auth check, redirect if not logged in | 20min | ⬜ |
| T-206 | Create empty state message | 15min | ⬜ |
| T-207 | Add download button for completed jobs | 20min | ⬜ |
| T-208 | Test downloads list end-to-end | 30min | ⬜ |
| T-209 | Code review | 30min | ⬜ |

**Total estimated time**: ~4 hours

---

### BACKLOG-09: Create download form (2 points)

| Task | Description | Time | Status |
|------|-------------|------|--------|
| T-210 | Create partials/download_form.html | 30min | ⬜ |
| T-211 | Add POST /downloads HTMX handler | 30min | ⬜ |
| T-212 | Add URL validation | 20min | ⬜ |
| T-213 | Test form submission | 20min | ⬜ |
| T-214 | Verify new download appears in list | 15min | ⬜ |
| T-215 | Code review | 30min | ⬜ |

**Total estimated time**: ~2.5 hours

---

### BACKLOG-10: Implement job status display (2 points)

| Task | Description | Time | Status |
|------|-------------|------|--------|
| T-216 | Create partials/status_badge.html | 20min | ⬜ |
| T-217 | Style status badges with colors | 30min | ⬜ |
| T-218 | Add error message display for failed status | 20min | ⬜ |
| T-219 | Test each status type displays correctly | 20min | ⬜ |
| T-220 | Code review | 30min | ⬜ |

**Total estimated time**: ~2 hours

---

### BACKLOG-11: Add logout functionality (1 point)

| Task | Description | Time | Status |
|------|-------------|------|--------|
| T-221 | Add logout button to navbar | 15min | ⬜ |
| T-222 | Create POST /logout route | 20min | ⬜ |
| T-223 | Clear tokens (localStorage + cookies) | 15min | ⬜ |
| T-224 | Redirect to /login | 10min | ⬜ |
| T-225 | Test logout flow | 15min | ⬜ |
| T-226 | Code review | 30min | ⬜ |

**Total estimated time**: ~1.5 hours

---

## Task-to-Issue Mapping

| Task ID | Description | Story | Assignee |
|---------|-------------|-------|----------|
| T-201 | Create GET /downloads route | BACKLOG-08 | |
| T-202 | Create pages/downloads.html | BACKLOG-08 | |
| T-203 | Query user's downloads | BACKLOG-08 | |
| T-204 | Render download list | BACKLOG-08 | |
| T-205 | Add auth check | BACKLOG-08 | |
| T-206 | Create empty state | BACKLOG-08 | |
| T-207 | Add download button | BACKLOG-08 | |
| T-208 | Test downloads list | BACKLOG-08 | |
| T-209 | Code review | BACKLOG-08 | |
| T-210 | Create download_form.html | BACKLOG-09 | |
| T-211 | Add POST /downloads handler | BACKLOG-09 | |
| T-212 | Add URL validation | BACKLOG-09 | |
| T-213 | Test form submission | BACKLOG-09 | |
| T-214 | Verify new download in list | BACKLOG-09 | |
| T-215 | Code review | BACKLOG-09 | |
| T-216 | Create status_badge.html | BACKLOG-10 | |
| T-217 | Style status badges | BACKLOG-10 | |
| T-218 | Add error message display | BACKLOG-10 | |
| T-219 | Test status display | BACKLOG-10 | |
| T-220 | Code review | BACKLOG-10 | |
| T-221 | Add logout button to navbar | BACKLOG-11 | |
| T-222 | Create POST /logout route | BACKLOG-11 | |
| T-223 | Clear tokens | BACKLOG-11 | |
| T-224 | Redirect to /login | BACKLOG-11 | |
| T-225 | Test logout flow | BACKLOG-11 | |
| T-226 | Code review | BACKLOG-11 | |

---

## Definition of Done Checklist

For each story to be marked Done:

- [ ] All tasks completed
- [ ] Code compiles/runs without errors
- [ ] Features work as described in acceptance criteria
- [ ] PR reviewed and approved
- [ ] Merged to main branch
- [ ] Tested on local environment with docker-compose