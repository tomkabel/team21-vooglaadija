# GitHub Issues - Sprint 2 Stories

## Overview

This directory contains GitHub Issue templates for Sprint 2 stories.

---

## Issue Labels

Apply these labels to all Sprint 2 issues:

- `sprint-2`
- `frontend`
- `htmx`
- `auth`

---

## Story Issues

### BACKLOG-04: Create login page with HTMX form

```markdown
## Story
As a user, I want to login via a web interface so I can access my downloads dashboard.

## Points: 3

## Acceptance Criteria
- [ ] GET /login renders login.html template
- [ ] Login form has email and password fields
- [ ] HTMX form posts to /login endpoint
- [ ] Invalid credentials show error message
- [ ] Valid credentials redirect to /downloads
- [ ] CSRF token included in form
- [ ] Form resets after successful submission
- [ ] Flash messages display for errors

## Technical Notes
- Use existing auth_service.verify_password()
- Store JWT in localStorage after successful login
- Redirect using hx-redirect header or JavaScript

## Dependencies
- Sprint 1 completion (Jinja2 templates, base layout)

## Todo
- [ ] Create GET /login route in pages.py
- [ ] Create pages/login.html template
- [ ] Add email/password form fields
- [ ] Add hidden CSRF token field
- [ ] Create POST /login HTMX handler
- [ ] Add error message display area
- [ ] Add redirect on success
- [ ] Test login flow end-to-end
- [ ] Get code review
```

### BACKLOG-05: Create register page with HTMX form

```markdown
## Story
As a new user, I want to register via a web interface so I can create an account.

## Points: 3

## Acceptance Criteria
- [ ] GET /register renders register.html template
- [ ] Register form has email, password, confirm password fields
- [ ] HTMX form posts to /register endpoint
- [ ] Duplicate email shows error message
- [ ] Password mismatch shows error message
- [ ] Successful registration shows confirmation and redirects to login
- [ ] CSRF token included in form
- [ ] Form validation on client and server side

## Technical Notes
- Use existing auth_service.create_user()
- Validate password length (min 8 chars)
- Validate email format
- Show password requirements

## Dependencies
- Sprint 1 completion (Jinja2 templates, base layout)

## Todo
- [ ] Create GET /register route in pages.py
- [ ] Create pages/register.html template
- [ ] Add email, password, confirm password fields
- [ ] Add hidden CSRF token field
- [ ] Create POST /register HTMX handler
- [ ] Add validation for duplicate email
- [ ] Add validation for password mismatch
- [ ] Add success message display
- [ ] Test registration flow end-to-end
- [ ] Get code review
```

### BACKLOG-06: Add CSRF protection for forms

```markdown
## Story
As a security-conscious developer, I want CSRF protection on all forms so we prevent cross-site request forgery attacks.

## Points: 2

## Acceptance Criteria
- [ ] CSRF middleware generates tokens for all responses
- [ ] All form submissions require valid CSRF token
- [ ] Invalid/missing CSRF token returns 400 error
- [ ] CSRF token rotates on each session
- [ ] Token stored in httpOnly cookie
- [ ] All HTMX forms include csrf_token field

## Technical Notes
- Use python-csrf library or custom implementation
- Token passed via cookie AND form field (double-submit)
- Exempt health check and static file endpoints

## Dependencies
- BACKLOG-04 (login page)
- BACKLOG-05 (register page)

## Todo
- [ ] Implement CSRF middleware
- [ ] Add token generation function
- [ ] Add token validation on POST requests
- [ ] Update login form to include CSRF token
- [ ] Update register form to include CSRF token
- [ ] Add error handling for invalid CSRF
- [ ] Test CSRF protection with forged request
- [ ] Get code review
```

### BACKLOG-07: Handle auth errors with user feedback

```markdown
## Story
As a user, I want clear error messages when authentication fails so I understand what went wrong.

## Points: 2

## Acceptance Criteria
- [ ] Invalid email shows "Email not found"
- [ ] Invalid password shows "Incorrect password"
- [ ] Duplicate registration shows "Email already registered"
- [ ] Weak password shows specific requirements
- [ ] All errors use friendly, non-technical language
- [ ] Errors display near relevant form field
- [ ] No error exposes sensitive system information

## Technical Notes
- Use specific error messages, not generic "Invalid credentials"
- Log detailed errors server-side, show generic to user
- Consider accessibility for error announcements

## Dependencies
- BACKLOG-04 (login page)
- BACKLOG-05 (register page)
- BACKLOG-06 (CSRF protection)

## Todo
- [ ] Add specific error messages in auth_service
- [ ] Add error message partial template
- [ ] Style error messages with red text
- [ ] Add aria-live region for screen readers
- [ ] Test each error case displays correctly
- [ ] Get code review
```

---

## File Locations

After creating issues in GitHub, track them in the sprint board:

| GitHub Issue | Story ID | Points | Column |
|--------------|----------|--------|--------|
| #57 | BACKLOG-04 | 3 | To Do |
| #58 | BACKLOG-05 | 3 | To Do |
| #59 | BACKLOG-06 | 2 | To Do |
| #60 | BACKLOG-07 | 2 | To Do |

## Project Board

**Project**: https://github.com/users/tomkabel/projects/3

**Milestone**: https://github.com/tomkabel/team21-vooglaadija/milestone/8

---

## Issue Creation Commands

```bash
# Example: Create BACKLOG-04 issue (already created)
# gh issue create \
#   --title "[BACKLOG-04] Create login page with HTMX form" \
#   --body "$(cat BACKLOG-04.md)" \
#   --label "sprint-2" \
#   --label "frontend" \
#   --label "auth" \
#   --assignee "@me"

# Add to GitHub Project (if using projects)
gh project item-add 3 --issue 57
gh project item-add 3 --issue 58
gh project item-add 3 --issue 59
gh project item-add 3 --issue 60

# Add to milestone
gh issue edit 57 --milestone "Sprint 2: Auth UI"
```

---

## Security Considerations

1. **CSRF**: Use double-submit cookie pattern
2. **XSS**: Sanitize all user inputs
3. **Password**: Never log passwords, enforce complexity
4. **Session**: Use secure, httpOnly cookies in production
5. **JWT**: Consider using httpOnly cookies instead of localStorage