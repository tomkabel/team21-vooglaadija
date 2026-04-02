# Sprint 4: Real-time Status Updates

**Sprint Goal**: Job status updates automatically without page refresh using HTMX polling.

**Duration**: April 22-28, 2026 (5 working days)

**Team**: 4 developers, 6 hours/day, Focus Factor 0.6

**Capacity Calculation**: 4 × 5 days × 6 hours × 0.6 = **72 hours** ≈ **18 story points**

---

## Sprint Backlog

| Story ID | Description | Points | Owner | Dependencies |
|----------|-------------|--------|-------|--------------|
| BACKLOG-12 | Implement status polling (every 3s) | 3 | TBD | Sprint 3 |
| BACKLOG-13 | Add loading indicators | 1 | TBD | BACKLOG-12 |
| BACKLOG-14 | Display errors for failed jobs | 2 | TBD | BACKLOG-12 |
| BACKLOG-15 | Add manual refresh button | 1 | TBD | Sprint 3 |

**Total Committed**: 7 points

---

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Polling too frequent | Medium | Medium | Use 3-5 second interval, not less |
| Status not updating | Medium | Medium | Verify worker is processing jobs |
| Memory leaks from polling | Low | Medium | Stop polling when job completes |
| Server load from polling | Medium | Medium | Limit polling to active jobs only |
| Race conditions | Low | Low | Use database transactions |

---

## Definition of Done

- [ ] Status element polls GET /downloads/{id}/status every 3 seconds
- [ ] Loading spinner shows when status is "processing"
- [ ] Completed jobs show green badge and stop polling
- [ ] Failed jobs show error message in red
- [ ] Manual refresh button triggers immediate status update
- [ ] Polling stops when job reaches terminal state (completed/failed)
- [ ] New downloads also start polling automatically
- [ ] Code reviewed by at least one team member
- [ ] Tested with docker-compose locally

---

## Technical Notes

### Status Polling Endpoint

```python
@router.get("/downloads/{download_id}/status")
async def get_download_status(request: Request, download_id: str):
    download = await get_download(download_id)
    return templates.TemplateResponse("partials/status_badge.html", {
        "request": request,
        "download": download
    })
```

### HTMX Polling Pattern

```html
<div hx-get="/downloads/{{ download.id }}/status"
     hx-trigger="every 3s"
     hx-swap="outerHTML"
     hx-target="this"
     id="status-{{ download.id }}">
    {% include "partials/status_badge.html" %}
</div>
```

### Stop Polling on Completion

```html
<script>
document.body.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.detail.target.classList.contains('status-completed') ||
        evt.detail.target.classList.contains('status-failed')) {
        // Polling will naturally stop since element is replaced
    }
});
</script>
```

### Loading Indicator

```html
<div class="htmx-indicator">
    <span class="spinner"></span>
    Processing...
</div>

<style>
.htmx-indicator { display: none; }
.htmx-request .htmx-indicator { display: inline; }
</style>
```

### Status Badge States

```html
<!-- partials/status_badge.html -->
<span class="status-badge status-{{ download.status }}">
    {% if download.status == 'pending' %}⏳ Pending{% endif %}
    {% if download.status == 'processing' %}⚙️ Processing{% endif %}
    {% if download.status == 'completed' %}✅ Completed{% endif %}
    {% if download.status == 'failed' %}❌ Failed: {{ download.error }}{% endif %}
</span>
```

---

## GitHub Artifacts

| Artifact | Link |
|----------|------|
| **Milestone** | https://github.com/tomkabel/team21-vooglaadija/milestone/10 |
| **Project Board** | https://github.com/users/tomkabel/projects/3 |
| **Issue: BACKLOG-12** | https://github.com/tomkabel/team21-vooglaadija/issues/65 |
| **Issue: BACKLOG-13** | https://github.com/tomkabel/team21-vooglaadija/issues/66 |
| **Issue: BACKLOG-14** | https://github.com/tomkabel/team21-vooglaadija/issues/67 |
| **Issue: BACKLOG-15** | https://github.com/tomkabel/team21-vooglaadija/issues/68 |

---

## Related Roadmap Items

This sprint addresses **Week 4: Job Status & Polling** from PROJECT_ROADMAP.md.

**Time Estimate from Roadmap**: 4-6 hours per person → Adjusted to 7 points for team coordination

---

## Previous Sprint Actions

| Action | Owner | Status |
|--------|-------|--------|
| Verify auth state persists | Team | Sprint 3 |
| Check download list displays correctly | Team | Sprint 3 |

---

## Next Sprint Preview

Following Sprint 4, the team should proceed to **Sprint 5: Validation & Error Handling** (April 29 - May 5) which includes:
- YouTube URL validation
- Clear error messages
- Empty states
- Form validation improvements