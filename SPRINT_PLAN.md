# YouTube Link Processor - Sprint Plan

## Project Overview

**Project**: YouTube Link Processor  
**Team Size**: 4 developers  
**Sprint Duration**: 1 week per sprint (5 working days)  
**Total Sprints**: 8 sprints  
**Start Date**: April 1, 2026  
**End Date**: May 21, 2026 (Sprint 8 is 2 days; project deadline May 23)

---

## Capacity Planning

**Team Configuration**:
- 4 developers
- 6 hours/day available per person
- 5 days per week
- Focus Factor: 0.6 (accounting for meetings, code reviews, unexpected issues)

**Calculation**:
```
Capacity = Team Size × Days × Hours × Focus Factor
         = 4 × 5 × 6 × 0.6
         = 72 hours per sprint
```

**Story Point Conversion**: 
- 1 point = ~4 hours of work
- Sprint Capacity = 72 / 4 = **18 story points**

---

## Product Backlog

| ID | Story | Points | Priority |
|----|-------|--------|----------|
| BACKLOG-01 | Set up Jinja2 templates in FastAPI | 2 | P0 |
| BACKLOG-02 | Create base HTML layout with HTMX | 3 | P0 |
| BACKLOG-03 | Add basic CSS styling | 1 | P1 |
| BACKLOG-04 | Create login page with HTMX form | 3 | P0 |
| BACKLOG-05 | Create register page with HTMX form | 3 | P0 |
| BACKLOG-06 | Add CSRF protection for forms | 2 | P0 |
| BACKLOG-07 | Handle auth errors with user feedback | 2 | P1 |
| BACKLOG-08 | Create downloads list page | 3 | P0 |
| BACKLOG-09 | Create download form | 2 | P0 |
| BACKLOG-10 | Implement job status display | 2 | P0 |
| BACKLOG-11 | Add logout functionality | 1 | P0 |
| BACKLOG-12 | Implement status polling (every 3s) | 3 | P1 |
| BACKLOG-13 | Add loading indicators | 1 | P1 |
| BACKLOG-14 | Display errors for failed jobs | 2 | P1 |
| BACKLOG-15 | Add manual refresh button | 1 | P2 |
| BACKLOG-16 | Validate YouTube URLs | 2 | P0 |
| BACKLOG-17 | Add clear error messages | 2 | P1 |
| BACKLOG-18 | Create empty states | 1 | P2 |
| BACKLOG-19 | Add form validation | 2 | P1 |
| BACKLOG-20 | Enhance Swagger documentation | 2 | P1 |
| BACKLOG-21 | Add API response examples | 1 | P2 |
| BACKLOG-22 | Document authentication flow | 1 | P2 |
| BACKLOG-23 | Manual testing all user flows | 3 | P0 |
| BACKLOG-24 | Test edge cases | 2 | P1 |
| BACKLOG-25 | Create error pages (404, 500) | 2 | P2 |
| BACKLOG-26 | Prepare demo script | 1 | P1 |
| BACKLOG-27 | Deploy to AWS EC2 (if required) | 5 | P0 |
| BACKLOG-28 | Configure AWS security (if required) | 3 | P1 |

---

## Sprint 1: Foundation

**Sprint Goal**: Set up HTMX frontend infrastructure with basic templates  
**Duration**: April 1-7, 2026 (5 working days)  
**Capacity**: 18 points  
**Committed**: 16 points

### Sprint Backlog

| Story | Points | Owner | Dependencies |
|-------|--------|-------|--------------|
| BACKLOG-01 - Set up Jinja2 templates in FastAPI | 2 | TBD | None |
| BACKLOG-02 - Create base HTML layout with HTMX | 3 | TBD | BACKLOG-01 |
| BACKLOG-03 - Add basic CSS styling | 1 | TBD | BACKLOG-02 |

### Tasks (Unestimated)

- [ ] Configure Jinja2Templates in main.py
- [ ] Create app/templates directory structure
- [ ] Create base.html with HTMX script include
- [ ] Add Tailwind CSS via CDN (simplest approach)
- [ ] Create navbar and footer partials
- [ ] Create static/css/styles.css with custom styles
- [ ] Mount static files in FastAPI

### Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Template paths incorrect | Medium | Test with simple "Hello" template first |
| HTMX not loading | Medium | Use CDN first, check console errors |
| CSS conflicts | Low | Use Tailwind utility classes |

### Definition of Done

- [ ] Jinja2 configured and working
- [ ] Base template renders in browser
- [ ] HTMX loads without errors
- [ ] CSS styles apply correctly
- [ ] Code reviewed by team member

---

## Sprint 2: Authentication UI

**Sprint Goal**: Users can register and login via web interface  
**Duration**: April 8-14, 2026 (5 working days)  
**Capacity**: 18 points  
**Committed**: 18 points

### Sprint Backlog

| Story | Points | Owner | Dependencies |
|-------|--------|-------|--------------|
| BACKLOG-04 - Create login page with HTMX form | 3 | TBD | Sprint 1 |
| BACKLOG-05 - Create register page with HTMX form | 3 | TBD | Sprint 1 |
| BACKLOG-06 - Add CSRF protection for forms | 2 | TBD | BACKLOG-04, BACKLOG-05 |
| BACKLOG-07 - Handle auth errors with user feedback | 2 | TBD | BACKLOG-04, BACKLOG-05 |

### Tasks (Unestimated)

- [ ] Create app/api/routes/pages.py for page routes
- [ ] Create GET /login page route
- [ ] Create GET /register page route
- [ ] Create pages/login.html template
- [ ] Create pages/register.html template
- [ ] Add HTMX form handling to login route
- [ ] Add HTMX form handling to register route
- [ ] Implement CSRF token generation
- [ ] Add CSRF middleware
- [ ] Display error messages for invalid credentials
- [ ] Display success message for registration

### Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| CSRF tokens not working | High | Use Flask-HTMLSanitizer or implement simple token |
| Form submission loops | Medium | Add hx-on::after-request to reset form |
| Session management | High | Use existing JWT, store in localStorage |

### Definition of Done

- [ ] Login page renders correctly
- [ ] Register page renders correctly
- [ ] Invalid credentials show error
- [ ] Successful login redirects to dashboard
- [ ] Successful registration shows confirmation
- [ ] CSRF protection working
- [ ] Code reviewed by team member

---

## Sprint 3: Downloads Dashboard

**Sprint Goal**: Users can view and create download jobs via web UI  
**Duration**: April 15-21, 2026 (5 working days)  
**Capacity**: 18 points  
**Committed**: 17 points

### Sprint Backlog

| Story | Points | Owner | Dependencies |
|-------|--------|-------|--------------|
| BACKLOG-08 - Create downloads list page | 3 | TBD | Sprint 2 |
| BACKLOG-09 - Create download form | 2 | TBD | BACKLOG-08 |
| BACKLOG-10 - Implement job status display | 2 | TBD | BACKLOG-08 |
| BACKLOG-11 - Add logout functionality | 1 | TBD | Sprint 2 |

### Tasks (Unestimated)

- [ ] Create GET /downloads page route
- [ ] Create pages/downloads.html template
- [ ] Query user's downloads from database
- [ ] Render download list with Jinja2 loop
- [ ] Create partials/download_card.html
- [ ] Create partials/download_form.html
- [ ] Add HTMX form to create new download
- [ ] Handle POST /downloads for HTMX
- [ ] Add new download to list via hx-swap
- [ ] Create logout route
- [ ] Clear tokens on logout

### Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Downloads not showing | Medium | Check database query, add debug logging |
| Form not submitting | High | Check HTMX attributes, network tab |
| Too many downloads | Low | Add pagination later (Sprint 5) |

### Definition of Done

- [ ] Downloads list shows user's jobs
- [ ] Can create new download via form
- [ ] New downloads appear in list immediately
- [ ] Logout clears session
- [ ] Works without page refresh
- [ ] Code reviewed by team member

---

## Sprint 4: Real-time Status Updates

**Sprint Goal**: Job status updates automatically without page refresh  
**Duration**: April 22-28, 2026 (5 working days)  
**Capacity**: 18 points  
**Committed**: 14 points

### Sprint Backlog

| Story | Points | Owner | Dependencies |
|-------|--------|-------|--------------|
| BACKLOG-12 - Implement status polling (every 3s) | 3 | TBD | Sprint 3 |
| BACKLOG-13 - Add loading indicators | 1 | TBD | BACKLOG-12 |
| BACKLOG-14 - Display errors for failed jobs | 2 | TBD | BACKLOG-12 |
| BACKLOG-15 - Add manual refresh button | 1 | TBD | Sprint 3 |

### Tasks (Unestimated)

- [ ] Create GET /downloads/{id}/status route
- [ ] Add hx-trigger="every 3s" to status element
- [ ] Create partials/status_badge.html
- [ ] Add htmx-indicator class for loading
- [ ] Style spinner/loader CSS
- [ ] Show error message when status = failed
- [ ] Add refresh button with hx-get
- [ ] Test polling doesn't cause performance issues

### Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Polling too frequent | Medium | Use 3-5 second interval |
| Status not updating | Medium | Check worker is processing jobs |
| Memory leaks | Low | Stop polling when job completes |

### Definition of Done

- [ ] Status updates every 3 seconds
- [ ] Loading spinner shows during processing
- [ ] Failed jobs show error message
- [ ] Manual refresh works
- [ ] Polling stops when job completes
- [ ] Code reviewed by team member

---

## Sprint 5: Validation & Error Handling

**Sprint Goal**: Robust user experience with clear feedback  
**Duration**: April 29 - May 5, 2026 (5 working days)  
**Capacity**: 18 points  
**Committed**: 17 points

### Sprint Backlog

| Story | Points | Owner | Dependencies |
|-------|--------|-------|--------------|
| BACKLOG-16 - Validate YouTube URLs | 2 | TBD | Sprint 4 |
| BACKLOG-17 - Add clear error messages | 2 | TBD | Sprint 4 |
| BACKLOG-18 - Create empty states | 1 | TBD | Sprint 3 |
| BACKLOG-19 - Add form validation | 2 | TBD | BACKLOG-16 |

### Tasks (Unestimated)

- [ ] Add URL regex validation for YouTube
- [ ] Return 400 with message for invalid URLs
- [ ] Display validation errors in form
- [ ] Add HTML5 pattern validation
- [ ] Create empty state for no downloads
- [ ] Add "No results" message for search
- [ ] Handle network errors gracefully
- [ ] Add toast notification system

### Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Validation too strict | Medium | Allow variations of YouTube URLs |
| Error messages unclear | Medium | Write user-friendly messages |

### Definition of Done

- [ ] Invalid URLs rejected with message
- [ ] Error messages are clear and helpful
- [ ] Empty states display correctly
- [ ] Form validation prevents bad input
- [ ] Network errors handled gracefully
- [ ] Code reviewed by team member

---

## Sprint 6: API Documentation

**Sprint Goal**: Professional Swagger documentation  
**Duration**: May 6-12, 2026 (5 working days)  
**Capacity**: 18 points  
**Committed**: 6 points

### Sprint Backlog

| Story | Points | Owner | Dependencies |
|-------|--------|-------|--------------|
| BACKLOG-20 - Enhance Swagger documentation | 2 | TBD | None |
| BACKLOG-21 - Add API response examples | 1 | TBD | BACKLOG-20 |
| BACKLOG-22 - Document authentication flow | 1 | TBD | BACKLOG-20 |

### Tasks (Unestimated)

- [ ] Update FastAPI title and description
- [ ] Add tags for API groups
- [ ] Add response examples to schemas
- [ ] Document auth flow with curl examples
- [ ] Document rate limits
- [ ] Test /docs endpoint

### Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Examples outdated | Low | Update when API changes |

### Definition of Done

- [ ] Swagger UI looks professional
- [ ] Examples are accurate
- [ ] Auth flow documented
- [ ] Rate limits documented
- [ ] Code reviewed by team member

---

## Sprint 7: Testing & Polish

**Sprint Goal**: Working demo with all features tested  
**Duration**: May 13-19, 2026 (5 working days)  
**Capacity**: 18 points  
**Committed**: 11 points

### Sprint Backlog

| Story | Points | Owner | Dependencies |
|-------|--------|-------|--------------|
| BACKLOG-23 - Manual testing all user flows | 3 | TBD | Sprint 5 |
| BACKLOG-24 - Test edge cases | 2 | TBD | BACKLOG-23 |
| BACKLOG-25 - Create error pages (404, 500) | 2 | TBD | Sprint 5 |
| BACKLOG-26 - Prepare demo script | 1 | TBD | BACKLOG-23 |

### Tasks (Unestimated)

- [ ] Test register → login → logout flow
- [ ] Test create download flow
- [ ] Test status polling
- [ ] Test download file
- [ ] Test invalid URL rejection
- [ ] Test session expiry
- [ ] Create 404 page
- [ ] Create 500 page
- [ ] Write demo walkthrough script
- [ ] Practice demo presentation

### Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Edge cases found late | Medium | Leave buffer time |
| Demo fails | High | Practice multiple times |

### Definition of Done

- [ ] All user flows tested
- [ ] Edge cases handled
- [ ] Error pages work
- [ ] Demo script ready
- [ ] Team has practiced demo
- [ ] Code reviewed by team member

---

## Sprint 8: AWS Deployment (Optional)

**Sprint Goal**: Deploy to cloud if required by assignment  
**Duration**: May 20-21, 2026 (2 working days - abbreviated due to deadline)  
**Capacity**: ~7 points (2 days × 4 people × 6 hours × 0.6 / 4 = ~7 points)  
**Committed**: 8 points (if needed) - may need to reduce scope

### Sprint Backlog

| Story | Points | Owner | Dependencies |
|-------|--------|-------|--------------|
| BACKLOG-27 - Deploy to AWS EC2 (if required) | 5 | TBD | Sprint 7 |
| BACKLOG-28 - Configure AWS security (if required) | 3 | TBD | BACKLOG-27 |

### Tasks (Unestimated)

- [ ] Set up AWS account (if not done)
- [ ] Launch EC2 instance (t3.micro)
- [ ] Install Docker on EC2
- [ ] Clone repository
- [ ] Configure environment variables
- [ ] Run docker-compose up
- [ ] Configure security group (ports 80, 443)
- [ ] Set up domain (optional)
- [ ] Configure HTTPS (optional)
- [ ] Test production deployment

### Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| AWS costs | High | Use free tier, set budget alert |
| Deployment fails | High | Test locally first |
| Security issues | Medium | Follow AWS best practices |

### Definition of Done

- [ ] Application running on EC2
- [ ] Accessible via public IP
- [ ] All features work in production
- [ ] Security configured
- [ ] Costs within budget

---

## Velocity Tracking

| Sprint | Dates | Committed | Completed | Velocity |
|--------|-------|-----------|-----------|----------|
| Sprint 1 | Apr 1-7 | 16 | TBD | TBD |
| Sprint 2 | Apr 8-14 | 18 | TBD | TBD |
| Sprint 3 | Apr 15-21 | 17 | TBD | TBD |
| Sprint 4 | Apr 22-28 | 14 | TBD | TBD |
| Sprint 5 | Apr 29 - May 5 | 17 | TBD | TBD |
| Sprint 6 | May 6-12 | 6 | TBD | TBD |
| Sprint 7 | May 13-19 | 11 | TBD | TBD |
| Sprint 8 | May 20-21 | 8 | TBD | TBD |

**Average Velocity**: To be calculated after Sprint 1

---

## Definition of Done (Global)

For all sprints, a story is complete when:

- [ ] Code written and functional
- [ ] Tests passing (if applicable)
- [ ] Code reviewed by another team member
- [ ] Merged to main branch
- [ ] Deployed to staging (if applicable)
- [ ] Product Owner acceptance

---

## Meeting Schedule

| Meeting | Frequency | Duration | Day |
|---------|-----------|----------|-----|
| Daily Standup | Daily | 15 min | Mon-Fri |
| Sprint Planning | Weekly | 60 min | Monday |
| Sprint Review | Weekly | 30 min | Friday |
| Retrospective | Weekly | 30 min | Friday |

---

## Notes

- **Sprints 1-5 are mandatory** - Core functionality
- **Sprint 6 is quick win** - Documentation
- **Sprint 7 ensures success** - Testing
- **Sprint 8 only if required** - AWS deployment

This plan assumes:
- Team has basic FastAPI knowledge
- Team has basic HTML/CSS knowledge
- No prior HTMX experience (learning curve included)
- AWS deployment only if assignment requires it

---

*Generated based on PROJECT_ROADMAP.md and sprint-planner skill framework*