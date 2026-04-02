# GitHub Issues - Sprint 3 Stories

## Overview

This directory contains GitHub Issue templates for Sprint 3 stories.

---

## Issue Labels

Apply these labels to all Sprint 3 issues:

- `sprint-3`
- `frontend`
- `htmx`
- `downloads`

---

## Story Issues

### BACKLOG-08: Create downloads list page

```markdown
## Story
As a user, I want to see a list of my download jobs so I can track my download history.

## Points: 3

## Acceptance Criteria
- [ ] GET /downloads renders downloads.html template
- [ ] Only authenticated user's downloads are shown
- [ ] Downloads displayed as cards with status badges
- [ ] Unauthenticated users redirected to /login
- [ ] Empty state shown when no downloads exist
- [ ] Download cards show: name, status, created date
- [ ] Completed downloads have download button

## Technical Notes
- Query downloads filtered by current user_id
- Use Jinja2 loop to render download cards
- Include status badge partial in each card

## Dependencies
- Sprint 2 completion (auth pages)

## Todo
- [ ] Create GET /downloads route in pages.py
- [ ] Create pages/downloads.html template
- [ ] Query user's downloads from database
- [ ] Render download list with Jinja2 loop
- [ ] Add auth check, redirect if not logged in
- [ ] Create empty state message
- [ ] Add download button for completed jobs
- [ ] Test downloads list end-to-end
- [ ] Get code review
```

### BACKLOG-09: Create download form

```markdown
## Story
As a user, I want to submit a YouTube URL for download so I can queue a new download job.

## Points: 2

## Acceptance Criteria
- [ ] Download form has URL input field
- [ ] Form submits via HTMX (no page refresh)
- [ ] New download appears in list immediately
- [ ] URL validated before submission
- [ ] Success feedback shown after submission
- [ ] Form resets after successful submission

## Technical Notes
- POST /downloads creates new job via API
- Use hx-post, hx-target, hx-swap attributes
- Prepend new download card to list

## Dependencies
- BACKLOG-08 (downloads list page)

## Todo
- [ ] Create partials/download_form.html
- [ ] Add POST /downloads HTMX handler
- [ ] Add URL validation
- [ ] Test form submission
- [ ] Verify new download appears in list
- [ ] Get code review
```

### BACKLOG-10: Implement job status display

```markdown
## Story
As a user, I want to see the current status of my downloads so I know if they are processing or complete.

## Points: 2

## Acceptance Criteria
- [ ] Status badge shown on each download card
- [ ] Badge shows: pending, processing, completed, failed
- [ ] Status colors: yellow (pending), blue (processing), green (completed), red (failed)
- [ ] Error message shown for failed jobs

## Technical Notes
- Use partials/status_badge.html
- CSS classes for status colors
- Error field from download model

## Dependencies
- BACKLOG-08 (downloads list page)

## Todo
- [ ] Create partials/status_badge.html
- [ ] Style status badges with colors
- [ ] Add error message display for failed status
- [ ] Test each status type displays correctly
- [ ] Get code review
```

### BACKLOG-11: Add logout functionality

```markdown
## Story
As a user, I want to logout so I can sign out of my account.

## Points: 1

## Acceptance Criteria
- [ ] Logout button in navbar
- [ ] POST /logout clears session/tokens
- [ ] User redirected to /login page
- [ ] Cannot access /downloads after logout
- [ ] No errors on logout

## Technical Notes
- Delete access_token from localStorage
- Clear any session cookies
- Redirect to login page

## Dependencies
- Sprint 2 completion (auth pages)

## Todo
- [ ] Add logout button to navbar
- [ ] Create POST /logout route
- [ ] Clear tokens (localStorage + cookies)
- [ ] Redirect to /login
- [ ] Test logout flow
- [ ] Get code review
```

---

## GitHub Issue Links

| Story ID | GitHub Issue | Points | Labels | Status |
|----------|--------------|--------|--------|--------|
| BACKLOG-08 | [#61](https://github.com/tomkabel/team21-vooglaadija/issues/61) | 3 | sprint-3, frontend, downloads, P0 | To Do |
| BACKLOG-09 | [#62](https://github.com/tomkabel/team21-vooglaadija/issues/62) | 2 | sprint-3, frontend, downloads, P0 | To Do |
| BACKLOG-10 | [#63](https://github.com/tomkabel/team21-vooglaadija/issues/63) | 2 | sprint-3, frontend, downloads, P0 | To Do |
| BACKLOG-11 | [#64](https://github.com/tomkabel/team21-vooglaadija/issues/64) | 1 | sprint-3, frontend, downloads, P1 | To Do |

## Project Board

**Project**: https://github.com/users/tomkabel/projects/3

**Milestone**: https://github.com/tomkabel/team21-vooglaadija/milestone/8