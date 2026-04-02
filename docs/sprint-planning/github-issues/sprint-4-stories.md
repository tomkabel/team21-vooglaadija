# GitHub Issues - Sprint 4 Stories

## Overview

This directory contains GitHub Issue templates for Sprint 4 stories.

---

## Issue Labels

Apply these labels to all Sprint 4 issues:

- `sprint-4`
- `frontend`
- `htmx`
- `real-time`

---

## Story Issues

### BACKLOG-12: Implement status polling (every 3s)

```markdown
## Story
As a user, I want my download status to update automatically so I don't have to refresh the page.

## Points: 3

## Acceptance Criteria
- [ ] Status element polls GET /downloads/{id}/status every 3 seconds
- [ ] Status updates without page refresh
- [ ] Polling starts automatically for new downloads
- [ ] Polling continues until job reaches terminal state
- [ ] No duplicate polling for same job

## Technical Notes
- Use hx-trigger="every 3s" attribute
- Status route returns partial HTML for badge
- Replace entire status element on each poll

## Dependencies
- Sprint 3 completion (downloads list)

## Todo
- [ ] Create GET /downloads/{id}/status route
- [ ] Create status partial for polling response
- [ ] Add hx-trigger="every 3s" to status element
- [ ] Test polling on downloads page
- [ ] Verify polling stops on completion
- [ ] Get code review
```

### BACKLOG-13: Add loading indicators

```markdown
## Story
As a user, I want to see a loading indicator so I know my request is being processed.

## Points: 1

## Acceptance Criteria
- [ ] Spinner shown when status is "processing"
- [ ] Loading indicator matches design system
- [ ] Indicator shows during page load
- [ ] Indicator shows during form submission

## Technical Notes
- Use htmx-indicator class
- CSS to show/hide based on htmx-request class
- Use CSS animation for spinner

## Dependencies
- BACKLOG-12 (status polling)

## Todo
- [ ] Add spinner CSS animation
- [ ] Create loading indicator HTML
- [ ] Add htmx-indicator class styling
- [ ] Test indicator shows during processing
- [ ] Get code review
```

### BACKLOG-14: Display errors for failed jobs

```markdown
## Story
As a user, I want to see error messages when my download fails so I understand what went wrong.

## Points: 2

## Acceptance Criteria
- [ ] Error message shown when status is "failed"
- [ ] Error text displayed in red
- [ ] Error includes actionable information if possible
- [ ] Error is user-friendly (not technical)

## Technical Notes
- Display download.error field
- Style error text in red
- Consider adding "Retry" button

## Dependencies
- BACKLOG-12 (status polling)

## Todo
- [ ] Style error text in red
- [ ] Display download.error message
- [ ] Add retry button for failed jobs
- [ ] Test failed job error display
- [ ] Get code review
```

### BACKLOG-15: Add manual refresh button

```markdown
## Story
As a user, I want a manual refresh button so I can force a status update when needed.

## Points: 1

## Acceptance Criteria
- [ ] Refresh button on downloads list
- [ ] Button triggers hx-get on status elements
- [ ] Button has appropriate icon
- [ ] Button does not interrupt polling

## Technical Notes
- Use hx-get with hx-trigger="click"
- Use refresh icon (🔄)
- Combine with automatic polling

## Dependencies
- Sprint 3 completion (downloads list)

## Todo
- [ ] Add refresh button to downloads page
- [ ] Connect button to hx-get for status refresh
- [ ] Add refresh icon
- [ ] Test button works alongside polling
- [ ] Get code review
```

---

## GitHub Issue Links

| Story ID | GitHub Issue | Points | Labels | Status |
|----------|--------------|--------|--------|--------|
| BACKLOG-12 | [#65](https://github.com/tomkabel/team21-vooglaadija/issues/65) | 3 | sprint-4, frontend, real-time, P0 | To Do |
| BACKLOG-13 | [#66](https://github.com/tomkabel/team21-vooglaadija/issues/66) | 1 | sprint-4, frontend, real-time, P1 | To Do |
| BACKLOG-14 | [#67](https://github.com/tomkabel/team21-vooglaadija/issues/67) | 2 | sprint-4, frontend, real-time, P0 | To Do |
| BACKLOG-15 | [#68](https://github.com/tomkabel/team21-vooglaadija/issues/68) | 1 | sprint-4, frontend, real-time, P1 | To Do |

## Project Board

**Project**: https://github.com/users/tomkabel/projects/3

**Milestone**: https://github.com/tomkabel/team21-vooglaadija/milestone/8