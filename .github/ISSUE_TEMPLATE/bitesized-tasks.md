# Good First Issues for New Contributors

> Collection of bite-sized tasks perfect for new project members and junior developers.

---

## Issue 1: Add Empty State Illustration to Downloads List

**Labels:** `good first issue` `frontend` `enhancement`

### Description

Currently, when a user has no downloads, the downloads list appears empty without any visual indication. This can be confusing for new users who haven't created any downloads yet.

### Expected Behavior

Show a friendly empty state with an illustration/icon and helpful message guiding users to add their first download.

### Files to Modify

- `app/templates/partials/_download_list.html`

### Implementation Hint

```jinja2
{% if jobs|length == 0 %}
<div class="empty-state">
  <!-- Add icon and friendly message -->
</div>
{% else %}
... existing list code ...
{% endif %}
```

### Requirements

- [ ] Show a friendly message like "No downloads yet"
- [ ] Add an appropriate icon (use existing SVG icons from the project)
- [ ] Make it visually consistent with the existing design (dark theme, amber accents)
- [ ] Add hover state guidance to encourage adding first download

---

## Issue 2: Add Password Strength Indicator on Registration

**Labels:** `good first issue` `frontend` `enhancement`

### Description

Help users create stronger passwords by showing visual feedback on the registration form as they type.

### Expected Behavior

Display a visual indicator showing password strength based on:
- Minimum 8 characters
- Contains at least one number
- Contains at least one special character

### Files to Modify

- `app/templates/register.html`
- `frontend/css/src/styles.css` (add new CSS classes if needed)

### Implementation Approach

1. Add a JavaScript function that checks password strength
2. Show a color-coded bar or text indicator below the password field
3. Use existing Tailwind colors: `jade-400` (strong), `amber-400` (medium), `coral-400` (weak)

### Requirements

- [ ] Validate password length (minimum 8 characters)
- [ ] Check for numbers in password
- [ ] Check for special characters in password
- [ ] Show visual feedback (color bar or text)
- [ ] Update feedback in real-time as user types

---

## Issue 3: Improve Form Validation Error Messages

**Labels:** `good first issue` `frontend` `accessibility`

### Description

Make validation errors more user-friendly with inline error messages that are properly announced to screen readers.

### Expected Behavior

When a user submits invalid form data, show clear inline error messages that help them fix the issue.

### Files to Modify

- `app/templates/login.html`
- `app/templates/register.html`

### Implementation Approach

1. Add proper HTML5 validation attributes (`minlength`, `pattern`, `required`)
2. Add `aria-describedby` to link inputs to their error messages
3. Style error messages with existing `.error-box` class or create similar

### Requirements

- [ ] Add HTML5 validation to email field (valid email format)
- [ ] Add minlength validation to password field
- [ ] Display inline error messages below fields
- [ ] Ensure errors are accessible (proper ARIA attributes)
- [ ] Style errors consistently with existing design

---

## Issue 4: Add Keyboard Shortcuts for Common Actions

**Labels:** `frontend` `ux` `enhancement`

### Description

Add keyboard shortcuts to improve user experience for power users.

### Expected Behavior

- `Ctrl + Enter` to submit forms
- `Escape` to close any open confirmations

### Files to Modify

- `app/templates/dashboard.html` (or create new JS file in `app/static/js/`)

### Implementation Approach

Add a JavaScript event listener for keyboard events:

```javascript
document.addEventListener('keydown', (e) => {
  // Ctrl+Enter to submit forms
  if (e.ctrlKey && e.key === 'Enter') {
    const form = document.activeElement.closest('form');
    if (form) form.submit();
  }
});
```

### Requirements

- [ ] Add Ctrl+Enter to submit the download form
- [ ] Add Escape to dismiss delete confirmations
- [ ] Ensure shortcuts don't interfere with normal typing

---

## Issue 5: Replace Inline Styles in toast.js with Tailwind Classes

**Labels:** `good first issue` `frontend` `refactoring`

### Description

The `toast.js` file currently uses JavaScript inline styles (`style.cssText`). This should be refactored to use CSS classes for better maintainability.

### Files to Modify

- `app/static/js/toast.js`
- `frontend/css/src/styles.css`

### Implementation Approach

1. Define CSS classes for toast types in `styles.css`:
   ```css
   .toast { /* base styles */ }
   .toast-success { @apply bg-jade-500; }
   .toast-error { @apply bg-coral-500; }
   ```

2. Update `toast.js` to use `classList.add()` instead of inline styles

### Requirements

- [ ] Create CSS classes for toast styles (success, error, warning, info)
- [ ] Update toast.js to use class-based styling
- [ ] Maintain existing animation behavior
- [ ] Ensure toast colors match design system

---

## Issue 6: Improve Mobile Responsiveness for Dashboard

**Labels:** `frontend` `responsive` `bug`

### Description

Review and fix mobile layout issues on smaller screens in the dashboard.

### Areas to Check

- Download input form on mobile
- Download rows with long URLs
- Stats cards layout on small screens

### Files to Modify

- `app/templates/dashboard.html`
- `frontend/css/src/styles.css`

### Requirements

- [ ] Test on mobile viewport (375px width)
- [ ] Fix any overflow issues with long URLs (truncation)
- [ ] Ensure buttons are tappable on mobile (minimum 44px touch target)
- [ ] Check form spacing on small screens

---

## Issue 7: Add URL Format Validation for Downloads

**Labels:** `backend` `validation` `security`

### Description

Validate that URLs are proper YouTube links before submitting to the backend. Currently, validation happens server-side, but client-side validation would provide better UX.

### Expected Behavior

When user pastes a URL, validate it's a YouTube link before submission.

### Files to Modify

- `app/schemas/` (add Pydantic validator)
- `app/api/routes/downloads.py`
- `app/utils/validators.py`

### Implementation Approach

Add a Pydantic validator for YouTube URL patterns:

```python
@field_validator('url')
@classmethod
def validate_youtube_url(cls, v: str) -> str:
    # Use existing validator in app/utils/validators.py
    if not is_valid_youtube_url(v):
        raise ValueError('Invalid YouTube URL')
    return v
```

### Requirements

- [ ] Reuse existing URL validation from `app/utils/validators.py`
- [ ] Add proper error message for invalid URLs
- [ ] Test with valid YouTube URLs (youtube.com, youtu.be, etc.)

---

## Issue 8: Add Unit Tests for URL Validation

**Labels:** `good first issue` `testing` `backend`

### Description

Write unit tests for the YouTube URL validation logic.

### Files to Modify

- `tests/test_utils/test_validators.py` (or create if doesn't exist)

### Test Cases to Cover

- Valid YouTube URLs:
  - `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
  - `https://youtu.be/dQw4w9WgXcQ`
  - `https://www.youtube.com/playlist?list=PL123`
  - `https://youtube-nocookie.com/embed/dQw4w9WgXcQ`

- Invalid URLs:
  - `https://example.com/video`
  - `https://youtube.com.evil.com malicious`
  - Plain text strings

### Requirements

- [ ] Test valid YouTube URLs
- [ ] Test invalid/attack URLs
- [ ] Follow existing test patterns in the project

---

## Issue 9: Add Rate Limit Headers to API Responses

**Labels:** `backend` `api` `enhancement`

### Description

Add rate limit information headers to API responses so clients know their current status.

### Expected Headers

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1640000000
```

### Files to Modify

- `app/api/middleware.py`
- `app/api/dependencies/` (check existing dependencies)

### Implementation Approach

Extend the existing slowapi integration to include rate limit headers in responses.

### Requirements

- [ ] Add X-RateLimit-Limit header
- [ ] Add X-RateLimit-Remaining header
- [ ] Add X-RateLimit-Reset header
- [ ] Test headers appear in API responses

---

## Issue 10: Add GitHub Issue Templates

**Labels:** `good first issue` `documentation` `meta`

### Description

Create standardized issue templates for bug reports and feature requests.

### Files to Create

- `.github/ISSUE_TEMPLATE/bug_report.md`
- `.github/ISSUE_TEMPLATE/feature_request.md`

### Template Requirements

**Bug Report:**
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, browser, etc.)

**Feature Request:**
- Description of the feature
- Why it's needed
- Possible implementation approach

---

## Issue 11: Add Pre-commit Hook for Code Formatting

**Labels:** `good first issue` `devops` `tooling`

### Description

Set up pre-commit hooks to automatically format code before commits.

### Files to Create/Modify

- `.pre-commit-config.yaml` (create)
- `pyproject.toml` (add configuration)

### Implementation Approach

Use existing tools in the project:

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.0
    hooks:
      - ruff
      - ruff-format
```

### Requirements

- [ ] Add ruff for Python formatting
- [ ] Add trailing whitespace check
- [ ] Document how to enable pre-commit in README

---

## Issue 12: Add Loading Skeleton for Downloads List

**Labels:** `frontend` `ux` `enhancement`

### Description

Show animated skeleton placeholders while downloads are loading to improve perceived performance.

### Files to Modify

- `app/templates/partials/_download_list.html`
- `frontend/css/src/styles.css`

### Implementation Approach

Create skeleton components that match the download row design:

```html
<div class="download-row skeleton">
  <div class="skeleton-icon"></div>
  <div class="skeleton-text"></div>
</div>
```

### Requirements

- [ ] Create skeleton UI matching download row design
- [ ] Add CSS animation for loading effect
- [ ] Show skeletons during initial page load
- [ ] Ensure skeletons disappear once data loads

---

## Quick Wins (Can Be Done in <1 Hour)

These are small tasks that can be quickly completed:

1. **Update copyright year** in footer (base.html uses `current_year` - verify it's working)
2. **Add placeholder text** improvements on input fields
3. **Add hover tooltips** to action buttons using `title` attribute
4. **Fix any typos** in templates - search for common misspellings

---

## Getting Started

1. Fork the repository
2. Create a branch: `git checkout -b fix/issue-number`
3. Make your changes
4. Run tests: `hatch run test:unit`
5. Submit a pull request

For questions, check the README.md or ask in the repository discussions.
