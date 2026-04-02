# GitHub Projects Board Setup - Sprint 2

## Sprint 2 Task Breakdown

**Sprint**: 2 - Authentication UI  
**Dates**: April 8-14, 2026 (5 working days)  
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

### BACKLOG-04: Create login page with HTMX form (3 points)

| Task | Description | Time | Status |
|------|-------------|------|--------|
| T-101 | Create GET /login route in pages.py | 20min | ⬜ |
| T-102 | Create pages/login.html template | 30min | ⬜ |
| T-103 | Add email/password form fields | 15min | ⬜ |
| T-104 | Add hidden CSRF token field | 10min | ⬜ |
| T-105 | Create POST /login HTMX handler | 30min | ⬜ |
| T-106 | Add error message display area | 15min | ⬜ |
| T-107 | Add redirect on success (htmx-redirect) | 15min | ⬜ |
| T-108 | Store JWT in localStorage | 20min | ⬜ |
| T-109 | Test login flow end-to-end | 30min | ⬜ |
| T-110 | Code review | 30min | ⬜ |

**Total estimated time**: ~3 hours

---

### BACKLOG-05: Create register page with HTMX form (3 points)

| Task | Description | Time | Status |
|------|-------------|------|--------|
| T-111 | Create GET /register route in pages.py | 20min | ⬜ |
| T-112 | Create pages/register.html template | 30min | ⬜ |
| T-113 | Add email, password, confirm password fields | 20min | ⬜ |
| T-114 | Add hidden CSRF token field | 10min | ⬜ |
| T-115 | Create POST /register HTMX handler | 30min | ⬜ |
| T-116 | Add password validation (length, complexity) | 20min | ⬜ |
| T-117 | Add password mismatch validation | 15min | ⬜ |
| T-118 | Add duplicate email check | 15min | ⬜ |
| T-119 | Add success message display | 15min | ⬜ |
| T-120 | Test registration flow end-to-end | 30min | ⬜ |
| T-121 | Code review | 30min | ⬜ |

**Total estimated time**: ~3.5 hours

---

### BACKLOG-06: Add CSRF protection for forms (2 points)

| Task | Description | Time | Status |
|------|-------------|------|--------|
| T-122 | Research CSRF implementation options | 30min | ⬜ |
| T-123 | Create CSRF middleware class | 45min | ⬜ |
| T-124 | Implement token generation function | 20min | ⬜ |
| T-125 | Implement token validation on POST | 30min | ⬜ |
| T-126 | Add token to cookie (httpOnly) | 15min | ⬜ |
| T-127 | Exempt static files and health checks | 10min | ⬜ |
| T-128 | Update base.html to expose csrf_token | 15min | ⬜ |
| T-129 | Test CSRF with forged request | 30min | ⬜ |
| T-130 | Code review | 30min | ⬜ |

**Total estimated time**: ~3 hours

---

### BACKLOG-07: Handle auth errors with user feedback (2 points)

| Task | Description | Time | Status |
|------|-------------|------|--------|
| T-131 | Add specific error messages in auth_service | 30min | ⬜ |
| T-132 | Create error message partial template | 20min | ⬜ |
| T-133 | Style error messages (red text, icons) | 15min | ⬜ |
| T-134 | Add aria-live region for screen readers | 15min | ⬜ |
| T-135 | Update login form error display | 15min | ⬜ |
| T-136 | Update register form error display | 15min | ⬜ |
| T-137 | Test each error case | 30min | ⬜ |
| T-138 | Code review | 30min | ⬜ |

**Total estimated time**: ~2.5 hours

---

## GitHub Project Setup Instructions

### Create Sprint 2 Iteration

```bash
# Via GitHub UI:
# Project Settings > Iterations > Add iteration
# Name: Sprint 2
# Start date: 2026-04-08
# Duration: 7 days
```

### Adding Issues to Project

```bash
# Add individual issues
gh project item-add 5 --issue #ISSUE_NUMBER

# List project items
gh project item-list 5
```

---

## Task-to-Issue Mapping

| Task ID | Description | Story | Assignee |
|---------|-------------|-------|----------|
| T-101 | Create GET /login route | BACKLOG-04 | |
| T-102 | Create pages/login.html | BACKLOG-04 | |
| T-103 | Add email/password fields | BACKLOG-04 | |
| T-104 | Add CSRF token field | BACKLOG-04 | |
| T-105 | Create POST /login handler | BACKLOG-04 | |
| T-106 | Add error display area | BACKLOG-04 | |
| T-107 | Add success redirect | BACKLOG-04 | |
| T-108 | Store JWT in localStorage | BACKLOG-04 | |
| T-109 | Test login flow | BACKLOG-04 | |
| T-110 | Code review | BACKLOG-04 | |
| T-111 | Create GET /register route | BACKLOG-05 | |
| T-112 | Create pages/register.html | BACKLOG-05 | |
| T-113 | Add registration fields | BACKLOG-05 | |
| T-114 | Add CSRF token field | BACKLOG-05 | |
| T-115 | Create POST /register handler | BACKLOG-05 | |
| T-116 | Password validation | BACKLOG-05 | |
| T-117 | Password mismatch validation | BACKLOG-05 | |
| T-118 | Duplicate email check | BACKLOG-05 | |
| T-119 | Success message | BACKLOG-05 | |
| T-120 | Test registration flow | BACKLOG-05 | |
| T-121 | Code review | BACKLOG-05 | |
| T-122 | Research CSRF options | BACKLOG-06 | |
| T-123 | Create CSRF middleware | BACKLOG-06 | |
| T-124 | Token generation | BACKLOG-06 | |
| T-125 | Token validation | BACKLOG-06 | |
| T-126 | Token cookie | BACKLOG-06 | |
| T-127 | Exempt endpoints | BACKLOG-06 | |
| T-128 | Update base.html | BACKLOG-06 | |
| T-129 | Test CSRF | BACKLOG-06 | |
| T-130 | Code review | BACKLOG-06 | |
| T-131 | Error messages in service | BACKLOG-07 | |
| T-132 | Error partial template | BACKLOG-07 | |
| T-133 | Style error messages | BACKLOG-07 | |
| T-134 | Add aria-live region | BACKLOG-07 | |
| T-135 | Login error display | BACKLOG-07 | |
| T-136 | Register error display | BACKLOG-07 | |
| T-137 | Test error cases | BACKLOG-07 | |
| T-138 | Code review | BACKLOG-07 | |

---

## Definition of Done Checklist

For each story to be marked Done:

- [ ] All tasks completed
- [ ] Code compiles/runs without errors
- [ ] Features work as described in acceptance criteria
- [ ] PR reviewed and approved
- [ ] Merged to main branch
- [ ] Tested on local environment with docker-compose
- [ ] All forms have CSRF protection
- [ ] Error messages are user-friendly