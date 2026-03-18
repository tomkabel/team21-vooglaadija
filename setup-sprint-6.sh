#!/bin/bash

# =============================================================================
# Sprint 6 Setup Script - Final Sprint & Project Closure
# Repository: https://github.com/tomkabel/team21-vooglaadija
# Sprint: April 13-19, 2026
# Focus: Polish, Documentation, Testing, Demo Preparation, Project Handoff
# =============================================================================

set -e

REPO="tomkabel/team21-vooglaadija"
SPRINT_NAME="Sprint 6: Final Polish & Project Closure"
MILESTONE_DATE="2026-04-19T23:59:59Z"

echo "🚀 Setting up Sprint 6 (Final) for $REPO"
echo "================================================"

if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    exit 1
fi

if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated. Run: gh auth login"
    exit 1
fi

echo "✅ Authentication verified"
echo ""

# ============================================================
# STEP 1: Create Labels
# ============================================================
echo "🏷️  Creating labels..."

gh label create "sprint-6" --color "D4C5F9" --description "Sprint 6 - Final" -R "$REPO" 2>/dev/null || echo "Label sprint-6 already exists"
gh label create "epic" --color "0052CC" --description "Epic - large body of work" -R "$REPO" 2>/dev/null || echo "Label epic already exists"
gh label create "priority-critical" --color "B60205" --description "Blocks release" -R "$REPO" 2>/dev/null || echo "Label priority-critical already exists"
gh label create "priority-high" --color "D93F0B" --description "Important" -R "$REPO" 2>/dev/null || echo "Label priority-high already exists"
gh label create "type-docs" --color "0075CA" --description "Documentation" -R "$REPO" 2>/dev/null || echo "Label type-docs already exists"
gh label create "type-testing" --color "84B6EB" --description "Testing" -R "$REPO" 2>/dev/null || echo "Label type-testing already exists"
gh label create "type-bug" --color "B60205" --description "Bug fix" -R "$REPO" 2>/dev/null || echo "Label type-bug already exists"
gh label create "area-demo" --color "F9D0C4" --description "Demo Preparation" -R "$REPO" 2>/dev/null || echo "Label area-demo already exists"
gh label create "area-docs" --color "C2E0C6" --description "Documentation" -R "$REPO" 2>/dev/null || echo "Label area-docs already exists"

echo "✅ Labels created"
echo ""

# ============================================================
# STEP 2: Create Milestone
# ============================================================
echo "📅 Creating Sprint 6 milestone..."

MILESTONE_RESULT=$(gh api repos/$REPO/milestones \
  --method POST \
  --field title="$SPRINT_NAME" \
  --field state=open \
  --field description="Week of Apr 13-19: Final polish, comprehensive testing, documentation, demo prep. Project completion and handoff." \
  --field due_on="$MILESTONE_DATE" 2>/dev/null || echo "exists")

if [ "$MILESTONE_RESULT" = "exists" ]; then
    echo "⚠️  Milestone may already exist"
else
    echo "✅ Milestone created"
fi
echo ""

# ============================================================
# STEP 3: Create Epic Issue
# ============================================================
echo "📋 Creating Sprint 6 Epic..."

EPIC_BODY='## Epic Goal
Deliver a polished, well-documented, thoroughly tested application ready for final demo and project handoff. Complete all project closure activities.

## Success Criteria
- [ ] All critical bugs resolved
- [ ] Documentation complete and reviewed
- [ ] Test coverage >80%
- [ ] Demo script prepared and rehearsed
- [ ] Project handoff documentation complete
- [ ] Repository archived/prepared for maintenance

## Sprint Capacity
- **Total Available:** 60 hours (2 devs × 5 days × 6 hrs)
- **Planned:** 50 hours (83% capacity)
- **Buffer:** 10 hours for unexpected issues

## Stories
1. Bug Fixes & Polish (8 pts)
2. Comprehensive Testing (5 pts)
3. Final Documentation (5 pts)
4. Demo Preparation (3 pts)
5. Project Handoff & Archive (5 pts)

**Total: 26 points**

## Definition of Project Complete
- [ ] All features implemented and working
- [ ] All tests passing (>80% coverage)
- [ ] Documentation complete
- [ ] Demo successful
- [ ] Handoff documentation delivered
- [ ] Repository in maintainable state
- [ ] Team retrospective completed

## Risks
| Risk | Probability | Mitigation |
|------|-------------|------------|
| Late-discovered critical bugs | Medium | Reserve buffer time |
| Documentation gaps | Low | Review checklist |
| Demo technical issues | Medium | Rehearsal, backup plans |'

gh issue create \
  --title="[EPIC] Sprint 6: Final Polish & Project Closure" \
  --body "$EPIC_BODY" \
  --label="epic" \
  --label="sprint-6" \
  --label="priority-critical" \
  -R "$REPO"

echo "✅ Epic created"
echo ""

# ============================================================
# STEP 4: Create Story Issues
# ============================================================

echo "📝 Creating Sprint 6 Stories..."
echo ""

# Story 1: Bug Fixes & Polish
STORY1_BODY='## User Story
As a user, I want a bug-free, polished application so I have a professional experience.

## Acceptance Criteria

### Bug Triage
- [ ] Review all open bugs and prioritize
- [ ] Fix all critical bugs (blocks release)
- [ ] Fix all high-priority bugs (major impact)
- [ ] Document known issues with workarounds

### UI/UX Polish
- [ ] Consistent spacing and typography
- [ ] Loading states on all async operations
- [ ] Error messages are helpful and actionable
- [ ] Empty states designed
- [ ] Mobile responsiveness verified

### Performance
- [ ] Lighthouse score >90 on all pages
- [ ] No console errors in production
- [ ] Memory leaks eliminated
- [ ] Bundle size optimized

### Accessibility
- [ ] ARIA labels on interactive elements
- [ ] Keyboard navigation works
- [ ] Color contrast WCAG AA compliant
- [ ] Screen reader tested

### Browser Compatibility
- [ ] Chrome/Edge: Full support
- [ ] Firefox: Full support
- [ ] Safari: Graceful degradation
- [ ] Mobile browsers tested

## Bug Categories
| Priority | Definition | SLA |
|----------|------------|-----|
| Critical | App crash, data loss, security | Fix immediately |
| High | Feature broken, bad UX | Fix in sprint |
| Medium | Minor issue, workaround exists | Document |
| Low | Cosmetic, nice-to-have | Backlog |

## Estimated Effort
**8 story points** (~16 hours)

## Dependencies
- All previous sprints completed

## Definition of Done
- [ ] All critical/high bugs fixed
- [ ] UI polish complete
- [ ] Performance targets met
- [ ] Accessibility verified
- [ ] No console errors'

gh issue create \
  --title="[Sprint 6] Bug fixes and UI/UX polish" \
  --body "$STORY1_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-6" \
  --label="priority-critical" \
  --label="type-bug" \
  --label="area-ui" \
  -R "$REPO"

echo "✅ Story 1 created"

# Story 2: Comprehensive Testing
STORY2_BODY='## User Story
As a stakeholder, I want comprehensive testing so I can trust the application quality.

## Acceptance Criteria

### Unit Tests (>80% coverage)
- [ ] All utility functions tested
- [ ] All API endpoints tested
- [ ] All database operations tested
- [ ] Edge cases covered
- [ ] Error paths tested

### Integration Tests
- [ ] Authentication flow
- [ ] Video processing pipeline
- [ ] Payment flow (Stripe)
- [ ] Batch processing
- [ ] Error recovery

### E2E Tests (Critical Paths)
- [ ] User registration and login
- [ ] Video upload and conversion
- [ ] Download workflow
- [ ] Premium upgrade
- [ ] Admin operations

### Performance Tests
- [ ] Load testing (100 concurrent users)
- [ ] Video processing benchmarks
- [ ] API response time tests
- [ ] Database query optimization

### Security Tests
- [ ] Authentication bypass attempts
- [ ] SQL injection tests
- [ ] XSS prevention verified
- [ ] Rate limiting tested
- [ ] Input validation tested

## Test Reports
- Coverage report (HTML)
- Performance benchmarks
- Security scan results
- Test execution summary

## Estimated Effort
**5 story points** (~10 hours)

## Dependencies
- All features implemented

## Definition of Done
- [ ] >80% code coverage
- [ ] All critical paths tested
- [ ] Performance benchmarks recorded
- [ ] Security tests pass
- [ ] CI pipeline green'

gh issue create \
  --title="[Sprint 6] Comprehensive testing and quality assurance" \
  --body "$STORY2_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-6" \
  --label="priority-high" \
  --label="type-testing" \
  --label="area-testing" \
  -R "$REPO"

echo "✅ Story 2 created"

# Story 3: Final Documentation
STORY3_BODY='## User Story
As a maintainer, I need complete documentation so I can support and extend the application.

## Acceptance Criteria

### Technical Documentation
- [ ] Architecture overview with diagrams
- [ ] API reference (auto-generated)
- [ ] Database schema documentation
- [ ] Deployment guide
- [ ] Environment setup guide
- [ ] Troubleshooting guide

### User Documentation
- [ ] User guide with screenshots
- [ ] FAQ section
- [ ] Feature overview
- [ ] Pricing and limits explained

### Developer Documentation
- [ ] Contributing guidelines
- [ ] Code style guide
- [ ] PR checklist
- [ ] Release process
- [ ] Monitoring and alerting runbook

### Project Documentation
- [ ] Project charter (updated)
- [ ] Sprint retrospectives summary
- [ ] Lessons learned document
- [ ] Risk register (final)
- [ ] Decision log (ADRs)

### README Updates
- [ ] Project description
- [ ] Feature list
- [ ] Tech stack
- [ ] Quick start
- [ ] Links to full docs

## Documentation Standards
- Clear, concise language
- Code examples where relevant
- Screenshots for UI features
- Diagrams for architecture
- Searchable structure

## Deliverables
- /docs/ directory complete
- README.md polished
- API docs generated
- Runbooks created

## Estimated Effort
**5 story points** (~10 hours)

## Dependencies
- All features stable

## Definition of Done
- [ ] All docs complete
- [ ] Docs reviewed by team
- [ ] README polished
- [ ] API docs generated
- [ ] Searchable navigation'

gh issue create \
  --title="[Sprint 6] Complete project documentation" \
  --body "$STORY3_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-6" \
  --label="priority-high" \
  --label="type-docs" \
  --label="area-docs" \
  -R "$REPO"

echo "✅ Story 3 created"

# Story 4: Demo Preparation
STORY4_BODY='## User Story
As a team, we need a polished demo to showcase our work effectively.

## Acceptance Criteria

### Demo Script
- [ ] 10-minute demo outline
- [ ] Feature narrative (story-driven)
- [ ] Key talking points
- [ ] Transition notes
- [ ] Backup plans for failures

### Demo Environment
- [ ] Dedicated demo instance
- [ ] Sample data prepared
- [ ] Test videos ready (various formats)
- [ ] Premium account for demo
- [ ] Clean state reset procedure

### Demo Recording
- [ ] Screen recording setup
- [ ] Backup recording (in case of live issues)
- [ ] Edited highlight reel (3 min)
- [ ] Voiceover/script

### Presentation Materials
- [ ] Slide deck (project overview)
- [ ] Architecture diagrams
- [ ] Metrics and achievements
- [ ] Team member contributions
- [ ] Q&A preparation

### Demo Scenarios
1. **Quick Win**: Upload → Convert → Download (2 min)
2. **Feature Deep Dive**: Batch processing + trim (3 min)
3. **Technical Highlight**: Premium features + API (3 min)
4. **Q&A Buffer**: (2 min)

## Demo Checklist
- [ ] Script rehearsed 3+ times
- [ ] Timing verified
- [ ] Demo environment tested
- [ ] Backup plans ready
- [ ] Team roles assigned

## Estimated Effort
**3 story points** (~6 hours)

## Dependencies
- All features working
- Stable environment

## Definition of Done
- [ ] Demo script complete
- [ ] Environment ready
- [ ] Recording made
- [ ] Slides prepared
- [ ] Team rehearsed'

gh issue create \
  --title="[Sprint 6] Prepare and rehearse final demo" \
  --body "$STORY4_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-6" \
  --label="priority-high" \
  --label="type-docs" \
  --label="area-demo" \
  -R "$REPO"

echo "✅ Story 4 created"

# Story 5: Project Handoff & Archive
STORY5_BODY='## User Story
As a project team, we need proper closure and handoff documentation.

## Acceptance Criteria

### Handoff Documentation
- [ ] System overview document
- [ ] Architecture diagrams (current)
- [ ] Deployment procedures
- [ ] Monitoring and alerting guide
- [ ] Troubleshooting runbook
- [ ] Contact list (team, stakeholders)

### Code Repository
- [ ] Code review completed
- [ ] No TODOs or FIXMEs in code
- [ ] Comments added where needed
- [ ] Secrets removed from history
- [ ] Repository cleaned and organized

### Knowledge Transfer
- [ ] Architecture walkthrough recorded
- [ ] Deployment demo recorded
- [ ] Key decisions documented
- [ ] Known issues documented
- [ ] Future enhancement ideas

### Project Retrospective
- [ ] Sprint retrospectives reviewed
- [ ] Overall project retrospective
- [ ] Lessons learned documented
- [ ] Success metrics compiled
- [ ] Team feedback collected

### Archive Preparation
- [ ] Final code snapshot tagged
- [ ] Documentation snapshot
- [ ] Demo recordings archived
- [ ] Project artifacts organized
- [ ] Handoff meeting scheduled

### Maintenance Plan
- [ ] Maintenance procedures
- [ ] Update/upgrade guidelines
- [ ] Monitoring schedule
- [ ] Backup procedures
- [ ] Disaster recovery plan

## Handoff Package
```
project-handoff/
├── 01-system-overview.md
├── 02-architecture-diagrams/
├── 03-deployment-guide.md
├── 04-monitoring-runbook.md
├── 05-troubleshooting.md
├── 06-api-reference/
├── 07-known-issues.md
├── 08-future-enhancements.md
└── 09-contact-information.md
```

## Estimated Effort
**5 story points** (~10 hours)

## Dependencies
- All other stories complete

## Definition of Done
- [ ] Handoff docs complete
- [ ] Repository cleaned
- [ ] Knowledge transferred
- [ ] Retrospective done
- [ ] Archive ready
- [ ] Handoff meeting completed

## Project Closure Checklist
- [ ] All sprints completed
- [ ] All epics closed
- [ ] Demo successful
- [ ] Documentation delivered
- [ ] Code archived
- [ ] Team celebration! 🎉'

gh issue create \
  --title="[Sprint 6] Project handoff and closure activities" \
  --body "$STORY5_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-6" \
  --label="priority-high" \
  --label="type-docs" \
  --label="area-docs" \
  -R "$REPO"

echo "✅ Story 5 created"

# ============================================================
# STEP 5: Summary
# ============================================================
echo ""
echo "================================================"
echo "🎉 Sprint 6 (Final) Setup Complete!"
echo "================================================"
echo ""
echo "Repository: https://github.com/$REPO"
echo "Milestone: $SPRINT_NAME"
echo "Due: April 19, 2026"
echo ""
echo "Created:"
echo "  • 1 Epic"
echo "  • 5 Stories (26 points)"
echo "  • 9 Labels"
echo "  • 1 Milestone"
echo ""
echo "This is the FINAL SPRINT! 🏁"
echo ""
echo "Next Steps:"
echo "  1. View issues: gh issue list -R $REPO --milestone '$SPRINT_NAME'"
echo "  2. Set up GitHub Project board"
echo "  3. Focus on quality and polish"
echo "  4. Prepare for demo and handoff"
echo ""
echo "Good luck with the final sprint! 💪"
echo ""
