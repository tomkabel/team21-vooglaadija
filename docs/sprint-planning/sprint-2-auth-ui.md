# Sprint 2: Authentication UI

**Sprint Goal**: Users can register and login via web interface with proper form handling, CSRF protection, and user-friendly error messages.

**Duration**: April 8-14, 2026 (5 working days)

**Team**: 4 developers, 6 hours/day, Focus Factor 0.6

**Capacity Calculation**: 4 × 5 days × 6 hours × 0.6 = **72 hours** ≈ **18 story points**

---

## Sprint Backlog

| Story ID | Description | Points | Owner | Dependencies |
|----------|-------------|--------|-------|--------------|
| BACKLOG-04 | Create login page with HTMX form | 3 | TBD | Sprint 1 |
| BACKLOG-05 | Create register page with HTMX form | 3 | TBD | Sprint 1 |
| BACKLOG-06 | Add CSRF protection for forms | 2 | TBD | BACKLOG-04, BACKLOG-05 |
| BACKLOG-07 | Handle auth errors with user feedback | 2 | TBD | BACKLOG-04, BACKLOG-05 |

**Total Committed**: 10 points

---

## Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| CSRF tokens not working | Medium | High | Use python-csrf or implement custom token |
| Form submission loops | Medium | Medium | Add hx-on::after-request to reset form |
| Session management issues | High | High | Use existing JWT, store in localStorage |
| JWT stored in browser | Medium | High | Use httpOnly cookie alternative |
| Error messages too generic | Medium | Low | Write user-friendly, specific messages |
| Flash messages not displaying | Low | Medium | Test HTMX swap with flash partial |

---

## Definition of Done

- [ ] Login page renders correctly at /login
- [ ] Register page renders correctly at /register
- [ ] Valid login redirects to /downloads dashboard
- [ ] Valid registration shows success message and redirects to login
- [ ] Invalid credentials show specific error message
- [ ] Invalid registration (duplicate email) shows error
- [ ] CSRF protection blocks forged form submissions
- [ ] CSRF token included in all forms
- [ ] Flash messages display on form submission
- [ ] Forms reset after successful submission
- [ ] Code reviewed by at least one team member
- [ ] Tested with docker-compose locally

---

## Technical Notes

### Page Routes to Create

```python
# app/api/routes/pages.py
@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("pages/login.html", {"request": request})

@router.post("/login")
async def login_submit(request: Request, form_data: LoginForm):
    # Verify credentials, set flash message
    # Return redirect or error HTML

@router.get("/register")
async def register_page(request: Request):
    return templates.TemplateResponse("pages/register.html", {"request": request})

@router.post("/register")
async def register_submit(request: Request, form_data: RegisterForm):
    # Create user, set flash message
    # Return redirect or error HTML
```

### CSRF Implementation

```python
# app/middleware/csrf.py
class CSRFMiddleware:
    async def __call__(self, request: Request, call_next):
        response = await call_next(request)
        if request.method in ("GET", "HEAD", "OPTIONS"):
            token = generate_csrf_token()
            response.set_cookie("csrf_token", token, httponly=True)
        return response
```

### HTMX Form Handling

```html
<!-- Login form example -->
<form hx-post="/login"
      hx-target="#auth-form"
      hx-swap="outerHTML"
      hx-on::after-request="if(event.detail.successful) this.reset()">
    <input type="hidden" name="csrf_token" value="{{ csrf_token }}">
    <input type="email" name="email" required>
    <input type="password" name="password" required>
    <button type="submit">Login</button>
</form>
<div id="auth-form"></div>
```

### File Structure

```
app/
├── templates/
│   ├── pages/
│   │   ├── login.html
│   │   └── register.html
│   └── partials/
│       └── flash_messages.html
├── middleware/
│   └── csrf.py
└── api/routes/
    └── pages.py
```

---

## GitHub Artifacts

| Artifact | Link |
|----------|------|
| **Milestone** | https://github.com/tomkabel/team21-vooglaadija/milestone/8 |
| **Project Board** | https://github.com/users/tomkabel/projects/3 |
| **Issue: BACKLOG-04** | https://github.com/tomkabel/team21-vooglaadija/issues/57 |
| **Issue: BACKLOG-05** | https://github.com/tomkabel/team21-vooglaadija/issues/58 |
| **Issue: BACKLOG-06** | https://github.com/tomkabel/team21-vooglaadija/issues/59 |
| **Issue: BACKLOG-07** | https://github.com/tomkabel/team21-vooglaadija/issues/60 |

---

## Related Roadmap Items

This sprint addresses **Week 2: Authentication UI** from PROJECT_ROADMAP.md.

**Time Estimate from Roadmap**: 6-8 hours per person → Adjusted to 10 points for team coordination

---

## Previous Sprint Retrospective Actions

| Action | Owner | Status |
|--------|-------|--------|
| | | |

---

## Next Sprint Preview

Following Sprint 2, the team should proceed to **Sprint 3: Downloads Dashboard** (April 15-21) which includes:
- Downloads list page
- Create download form
- Job status display
- Logout functionality