# 📋 YouTube Link Processor - Realistic Roadmap

## Practical Guide for a Working Group Project

---

## 🎯 Project Requirements (What You Actually Need)

| Requirement | What "Done" Looks Like |
|-------------|------------------------|
| **Frontend** | Working HTMX web UI with login, register, downloads list |
| **Backend** | FastAPI running, handles requests |
| **API** | REST endpoints with Swagger docs |
| **Authentication** | JWT login/register (self-hosted is fine) |
| **AWS/Cloud** | Only if assignment requires it |

**That's it.** Nothing more needed for a passing grade.

---

## 📊 Current State Assessment

### What's Working ✅
- FastAPI backend with async patterns
- JWT authentication (register, login, refresh)
- Redis queue for job processing
- Worker process for yt-dlp
- PostgreSQL database
- Docker compose setup
- Basic CI/CD with GitHub Actions

### What's Missing ❌
- **Frontend** - No web UI at all
- **Error handling** - Minimal user feedback
- **Input validation** - Can submit anything
- **Rate limiting** - Only on auth endpoints
- **File management** - Local storage only

---

## 🗓️ Realistic 8-Week Timeline

### Week 1: Foundation
**Goal:** Get HTMX running with basic templates

| Task | Deliverable |
|------|-------------|
| Set up Jinja2 templates | Template engine works |
| Create base layout | Navbar, footer, content area |
| Add HTMX script | HTMX loads in browser |
| Create static CSS | Basic styling |

**Files to create:**
```
app/templates/
├── base.html
├── pages/
│   ├── index.html
│   └── error.html
└── static/
    └── css/
        └── styles.css
```

**Time estimate:** 4-6 hours

---

### Week 2: Authentication UI
**Goal:** Login and register pages work

| Task | Deliverable |
|------|-------------|
| Create login page | Form submits, shows errors |
| Create register page | Form submits, shows errors |
| Add CSRF protection | Security (required) |
| Handle auth errors | Proper error messages |

**Key code needed:**
```python
# app/api/routes/pages.py
@router.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("pages/login.html", {"request": request})

@router.post("/login")
async def login_submit(request: Request, form_data: LoginForm):
    # Process form, return HTML or redirect
```

**Time estimate:** 6-8 hours

---

### Week 3: Downloads Dashboard
**Goal:** Users can see their downloads

| Task | Deliverable |
|------|-------------|
| Downloads list page | Shows user's jobs |
| Create download form | Submit YouTube URL |
| Job status display | Shows pending/processing/completed |
| Logout functionality | Works properly |

**HTMX pattern:**
```html
<!-- List downloads -->
<div hx-get="/downloads" hx-trigger="load" hx-target="#downloads-list">
    Loading...
</div>

<!-- Create new -->
<form hx-post="/downloads" hx-target="#downloads-list" hx-swap="beforeend">
    <input type="url" name="url" required>
    <button>Download</button>
</form>
```

**Time estimate:** 8-10 hours

---

### Week 4: Job Status & Polling
**Goal:** Real-time status updates

| Task | Deliverable |
|------|-------------|
| Status polling | Updates every 2-3 seconds |
| Loading indicators | Shows during processing |
| Error display | Shows when jobs fail |
| Refresh button | Manual refresh option |

**HTMX polling:**
```html
<div hx-get="/downloads/{id}/status" 
     hx-trigger="every 3s" 
     hx-swap="outerHTML">
    Status: {{ download.status }}
</div>
```

**Time estimate:** 4-6 hours

---

### Week 5: Validation & Error Handling
**Goal:** Robust user experience

| Task | Deliverable |
|------|-------------|
| URL validation | Only YouTube URLs accepted |
| Error messages | Clear, helpful feedback |
| Empty states | "No downloads yet" message |
| Form validation | Required fields, formats |

**Validation code:**
```python
@router.post("/downloads")
async def create_download(data: DownloadCreate):
    # Validate YouTube URL
    if not is_valid_youtube_url(data.url):
        raise HTTPException(400, "Please enter a valid YouTube URL")
    
    # Check user download quota
    user_downloads = await get_user_download_count(current_user.id)
    if user_downloads >= MAX_DOWNLOADS_PER_USER:
        raise HTTPException(400, "Download limit reached (10/day)")
    
    # Proceed...
```

**Time estimate:** 6-8 hours

---

### Week 6: Swagger & Documentation
**Goal:** Professional API docs

| Task | Deliverable |
|------|-------------|
| Enhance Swagger | Better descriptions, examples |
| Add response examples | Shows what API returns |
| Document auth flow | How to get and use tokens |
| Add rate limit docs | What's allowed |

**Quick win - just update main.py:**
```python
app = FastAPI(
    title="YouTube Link Processor",
    description="""
    API for extracting and downloading YouTube media.
    
    ## Quick Start
    1. Register: POST /auth/register
    2. Login: POST /auth/login  
    3. Create download: POST /downloads
    """,
    version="1.0.0",
)
```

**Time estimate:** 2-3 hours

---

### Week 7: Testing & Polish
**Goal:** Working demo

| Task | Deliverable |
|------|-------------|
| Manual testing | All flows work |
| Edge cases | Invalid URLs, expired sessions |
| Error pages | 404, 500 pages |
| Demo script | Walk through features |

**Manual test checklist:**
- [ ] Register new user
- [ ] Login with wrong password (error shows)
- [ ] Login with correct password (redirects)
- [ ] Create download with invalid URL (error shows)
- [ ] Create download with valid URL (appears in list)
- [ ] Wait for processing (status updates)
- [ ] Download completed file
- [ ] Logout (redirects to login)

**Time estimate:** 6-8 hours

---

### Week 8: AWS (Only If Required)
**Goal:** Cloud deployment

**Skip this entirely unless AWS is required by your assignment.**

If required, use the simplest approach:

### Option A: AWS Lightsail (Easiest)
- $5/month fixed price
- Includes Docker, PostgreSQL
- One-click apps

### Option B: EC2 (Recommended)
- t3.micro (free tier eligible)
- Install Docker, run docker-compose
- $0/month for 12 months

### Option C: ECS Fargate (If Required)
- 1 task (not 2)
- Minimal resources
- ~$20-30/month

**What NOT to do:**
- ❌ Terraform (too complex)
- ❌ Cognito (overkill)
- ❌ RDS Aurora (use EC2 PostgreSQL)
- ❌ ElastiCache (use Redis on EC2)

**Time estimate:** 8-12 hours for full setup

---

## 📁 File Structure (What You'll Actually Create)

```
team21-vooglaadija/
├── app/
│   ├── main.py                    # Add template config
│   ├── api/routes/
│   │   ├── pages.py               # NEW: Page routes
│   │   └── downloads.py           # Add HTMX responses
│   ├── templates/                 # NEW
│   │   ├── base.html
│   │   ├── partials/
│   │   │   ├── navbar.html
│   │   │   ├── download_card.html
│   │   │   ├── download_form.html
│   │   │   └── status_badge.html
│   │   └── pages/
│   │       ├── index.html
│   │       ├── login.html
│   │       ├── register.html
│   │       └── downloads.html
│   ├── static/                    # NEW
│   │   └── css/
│   │       └── styles.css
│   └── middleware/
│       └── htmx.py                # NEW: HTMX helpers
├── tests/
│   └── test_frontend/             # NEW (optional)
└── PROJECT_ROADMAP.md             # This file
```

---

## 💰 Cost Analysis

### Local Development ($0)
| Item | Cost |
|------|------|
| Docker | Free |
| PostgreSQL | Free |
| Redis | Free |
| **Total** | **$0** |

### If AWS Required ($0-30/month)
| Approach | Monthly Cost |
|----------|--------------|
| EC2 Free Tier | $0 |
| Lightsail | $5 |
| ECS Fargate (minimal) | $20-30 |
| **Recommended** | **EC2 Free Tier** |

---

## ✅ Weekly Checklist

### Week 1
- [ ] Jinja2 configured in main.py
- [ ] base.html created with HTMX
- [ ] Basic CSS styling works
- [ ] Can access templates in browser

### Week 2
- [ ] Login page renders
- [ ] Register page renders
- [ ] Forms submit to backend
- [ ] Errors display properly

### Week 3
- [ ] Downloads list shows jobs
- [ ] Create download form works
- [ ] New downloads appear in list
- [ ] Logout works

### Week 4
- [ ] Status auto-updates
- [ ] Loading indicators show
- [ ] Errors display for failed jobs
- [ ] Manual refresh works

### Week 5
- [ ] Invalid URLs rejected
- [ ] Error messages are clear
- [ ] Empty states show
- [ ] Form validation works

### Week 6
- [ ] Swagger docs look good
- [ ] Examples are accurate
- [ ] Auth flow documented

### Week 7
- [ ] All manual tests pass
- [ ] Edge cases handled
- [ ] Demo prepared

### Week 8 (if AWS required)
- [ ] Deployed to cloud
- [ ] Works in production
- [ ] Demo runs smoothly

---

## 🔧 Quick Reference

### HTMX Patterns

**Swap into list:**
```html
hx-target="#downloads-list"
hx-swap="afterbegin"  <!-- add to top -->
<!-- or -->
hx-swap="beforeend"   <!-- add to bottom -->
```

**Polling:**
```html
hx-get="/status"
hx-trigger="every 2s"
```

**Loading indicator:**
```html
<div class="htmx-indicator">Loading...</div>
<!-- or -->
<button hx-disabled-elt="this">Processing...</button>
```

**Error handling:**
```html
hx-on::after-request="if(!event.detail.successful) alert('Error')"
```

### Common Issues

| Problem | Solution |
|---------|----------|
| HTMX not loading | Check script src, check console |
| Forms not submitting | Add hx-on:submit or check network |
| CSRF errors | Include CSRF token in form |
| Polling stops | Check if job completed |
| Styles not applying | Check static file path |

---

## 📚 Resources

- [HTMX Docs](https://htmx.org/docs/) - Start here
- [FastAPI Templates](https://fastapi.tiangolo.com/advanced/templates/) - Jinja2 setup
- [TestDriven.io HTMX Course](https://testdriven.io/courses/fastapi-htmx/) - Free course

---

## 🎯 Success Criteria

**Minimum viable product:**
- [ ] User can register and login
- [ ] User can create download job
- [ ] User can see list of downloads
- [ ] User can download completed files
- [ ] API has Swagger documentation

**Nice to have:**
- [ ] Status polling
- [ ] Error handling
- [ ] Input validation
- [ ] Basic styling

**Not required:**
- AWS deployment (unless specified)
- Cognito
- Terraform
- AI/ML features
- Advanced monitoring

---

*This roadmap is designed to get you to a working demo with minimum stress.*
*Focus on completing one week at a time.*
*Don't add features - finish what you started.*