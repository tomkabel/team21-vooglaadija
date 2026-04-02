# Sprint 3: Downloads Dashboard

**Sprint Goal**: Users can view their download history and create new download jobs via a web interface.

**Duration**: April 15-21, 2026 (5 working days)

**Team**: 4 developers, 6 hours/day, Focus Factor 0.6

**Capacity Calculation**: 4 × 5 days × 6 hours × 0.6 = **72 hours** ≈ **18 story points**

---

## Sprint Backlog

| Story ID | Description | Points | Owner | Dependencies |
|----------|-------------|--------|-------|--------------|
| BACKLOG-08 | Create downloads list page | 3 | TBD | Sprint 2 |
| BACKLOG-09 | Create download form | 2 | TBD | BACKLOG-08 |
| BACKLOG-10 | Implement job status display | 2 | TBD | BACKLOG-08 |
| BACKLOG-11 | Add logout functionality | 1 | TBD | Sprint 2 |

**Total Committed**: 8 points

---

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Downloads not showing | Medium | Medium | Check database query, add debug logging |
| HTMX form not submitting | Medium | High | Check HTMX attributes in network tab |
| Pagination needed | Low | Low | Add pagination later (Sprint 5) |
| Authentication state lost | Medium | High | Verify JWT stored correctly in localStorage |
| File download not working | Low | Medium | Test with completed job |

---

## Definition of Done

- [ ] Downloads list page renders at /downloads
- [ ] Only authenticated user's downloads shown
- [ ] Downloads displayed as cards with status badges
- [ ] Create download form submits via HTMX
- [ ] New downloads appear in list immediately after creation
- [ ] Logout button clears session and redirects to login
- [ ] Unauthenticated users redirected to /login
- [ ] Empty state shown when no downloads exist
- [ ] Code reviewed by at least one team member
- [ ] Tested with docker-compose locally

---

## Technical Notes

### Page Route

```python
# app/api/routes/pages.py
@router.get("/downloads")
async def downloads_page(request: Request):
    # Check auth, redirect if not logged in
    user = await get_current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=302)
    
    downloads = await get_user_downloads(user.id)
    return templates.TemplateResponse("pages/downloads.html", {
        "request": request,
        "downloads": downloads,
        "user": user
    })
```

### Download Card Partial

```html
<!-- partials/download_card.html -->
<div class="download-card" id="download-{{ download.id }}">
    <h3>{{ download.file_name or download.url }}</h3>
    <span class="status-badge status-{{ download.status }}">
        {{ download.status }}
    </span>
    <p>Created: {{ download.created_at }}</p>
    {% if download.status == 'completed' %}
    <a href="/downloads/{{ download.id }}/file" class="btn-download">Download</a>
    {% endif %}
</div>
```

### HTMX Form for Creating Download

```html
<!-- partials/download_form.html -->
<form hx-post="/downloads"
      hx-target="#downloads-list"
      hx-swap="afterbegin"
      hx-on::after-request="this.reset()">
    <input type="url" name="url" placeholder="YouTube URL" required>
    <button type="submit">Add Download</button>
</form>
```

### Logout Handler

```python
@router.post("/logout")
async def logout(request: Request):
    response = RedirectResponse("/login", status_code=302)
    response.delete_cookie("access_token")
    return response
```

### File Structure

```
app/
├── templates/
│   ├── pages/
│   │   └── downloads.html
│   └── partials/
│       ├── download_card.html
│       ├── download_form.html
│       └── status_badge.html
```

---

## GitHub Artifacts

| Artifact | Link |
|----------|------|
| **Milestone** | https://github.com/tomkabel/team21-vooglaadija/milestone/9 |
| **Project Board** | https://github.com/users/tomkabel/projects/3 |
| **Issue: BACKLOG-08** | https://github.com/tomkabel/team21-vooglaadija/issues/61 |
| **Issue: BACKLOG-09** | https://github.com/tomkabel/team21-vooglaadija/issues/62 |
| **Issue: BACKLOG-10** | https://github.com/tomkabel/team21-vooglaadija/issues/63 |
| **Issue: BACKLOG-11** | https://github.com/tomkabel/team21-vooglaadija/issues/64 |

---

## Related Roadmap Items

This sprint addresses **Week 3: Downloads Dashboard** from PROJECT_ROADMAP.md.

**Time Estimate from Roadmap**: 8-10 hours per person → Adjusted to 8 points for team coordination

---

## Previous Sprint Actions

| Action | Owner | Status |
|--------|-------|--------|
| Continue CSRF token in all forms | Team | Ongoing |
| Consistent error message styling | Team | Ongoing |

---

## Next Sprint Preview

Following Sprint 3, the team should proceed to **Sprint 4: Real-time Status Updates** (April 22-28) which includes:
- Status polling every 3 seconds
- Loading indicators
- Error display for failed jobs
- Manual refresh button