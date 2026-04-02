# GitHub Projects Board Setup - Sprint 4

## Sprint 4 Task Breakdown

**Sprint**: 4 - Real-time Status Updates  
**Dates**: April 22-28, 2026 (5 working days)  
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

### BACKLOG-12: Implement status polling (every 3s) (3 points)

| Task | Description | Time | Status |
|------|-------------|------|--------|
| T-301 | Create GET /downloads/{id}/status route | 30min | ⬜ |
| T-302 | Create status partial for polling response | 20min | ⬜ |
| T-303 | Add hx-trigger="every 3s" to status element | 20min | ⬜ |
| T-304 | Test polling on downloads page | 30min | ⬜ |
| T-305 | Verify polling stops on completion | 20min | ⬜ |
| T-306 | Code review | 30min | ⬜ |

**Total estimated time**: ~2.5 hours

---

### BACKLOG-13: Add loading indicators (1 point)

| Task | Description | Time | Status |
|------|-------------|------|--------|
| T-307 | Add spinner CSS animation | 20min | ⬜ |
| T-308 | Create loading indicator HTML | 15min | ⬜ |
| T-309 | Add htmx-indicator class styling | 15min | ⬜ |
| T-310 | Test indicator shows during processing | 15min | ⬜ |
| T-311 | Code review | 30min | ⬜ |

**Total estimated time**: ~1.5 hours

---

### BACKLOG-14: Display errors for failed jobs (2 points)

| Task | Description | Time | Status |
|------|-------------|------|--------|
| T-312 | Style error text in red | 15min | ⬜ |
| T-313 | Display download.error message | 20min | ⬜ |
| T-314 | Add retry button for failed jobs | 25min | ⬜ |
| T-315 | Test failed job error display | 20min | ⬜ |
| T-316 | Code review | 30min | ⬜ |

**Total estimated time**: ~2 hours

---

### BACKLOG-15: Add manual refresh button (1 point)

| Task | Description | Time | Status |
|------|-------------|------|--------|
| T-317 | Add refresh button to downloads page | 15min | ⬜ |
| T-318 | Connect button to hx-get for status refresh | 20min | ⬜ |
| T-319 | Add refresh icon | 10min | ⬜ |
| T-320 | Test button works alongside polling | 15min | ⬜ |
| T-321 | Code review | 30min | ⬜ |

**Total estimated time**: ~1.5 hours

---

## Task-to-Issue Mapping

| Task ID | Description | Story | Assignee |
|---------|-------------|-------|----------|
| T-301 | Create status route | BACKLOG-12 | |
| T-302 | Create status partial | BACKLOG-12 | |
| T-303 | Add polling trigger | BACKLOG-12 | |
| T-304 | Test polling | BACKLOG-12 | |
| T-305 | Verify polling stops | BACKLOG-12 | |
| T-306 | Code review | BACKLOG-12 | |
| T-307 | Add spinner CSS | BACKLOG-13 | |
| T-308 | Create indicator HTML | BACKLOG-13 | |
| T-309 | Style htmx-indicator | BACKLOG-13 | |
| T-310 | Test indicator | BACKLOG-13 | |
| T-311 | Code review | BACKLOG-13 | |
| T-312 | Style error text | BACKLOG-14 | |
| T-313 | Display error message | BACKLOG-14 | |
| T-314 | Add retry button | BACKLOG-14 | |
| T-315 | Test error display | BACKLOG-14 | |
| T-316 | Code review | BACKLOG-14 | |
| T-317 | Add refresh button | BACKLOG-15 | |
| T-318 | Connect to hx-get | BACKLOG-15 | |
| T-319 | Add refresh icon | BACKLOG-15 | |
| T-320 | Test button + polling | BACKLOG-15 | |
| T-321 | Code review | BACKLOG-15 | |

---

## Definition of Done Checklist

For each story to be marked Done:

- [ ] All tasks completed
- [ ] Code compiles/runs without errors
- [ ] Features work as described in acceptance criteria
- [ ] PR reviewed and approved
- [ ] Merged to main branch
- [ ] Tested on local environment with docker-compose
- [ ] Polling performs without issues
- [ ] Loading indicators display correctly