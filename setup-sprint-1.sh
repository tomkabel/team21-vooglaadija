#!/bin/bash

# =============================================================================
# Sprint 1 Setup Script - Project Kickoff & Planning
# Repository: https://github.com/tomkabel/team21-vooglaadija
# Sprint: March 9-15, 2026
# Focus: Requirements, Architecture Decisions, Team Setup
# =============================================================================

set -e

REPO="tomkabel/team21-vooglaadija"
SPRINT_NAME="Sprint 1: Project Kickoff & Planning"
MILESTONE_DATE="2026-03-15T23:59:59Z"

echo "🚀 Setting up Sprint 1 for $REPO"
echo "================================================"

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed."
    exit 1
fi

# Check authentication
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

# Sprint labels
gh label create "sprint-1" --color "5319E7" --description "Sprint 1 work" -R "$REPO" 2>/dev/null || echo "Label sprint-1 already exists"
gh label create "epic" --color "0052CC" --description "Epic - large body of work" -R "$REPO" 2>/dev/null || echo "Label epic already exists"

# Priority labels
gh label create "priority-critical" --color "B60205" --description "Blocks release" -R "$REPO" 2>/dev/null || echo "Label priority-critical already exists"
gh label create "priority-high" --color "D93F0B" --description "Important" -R "$REPO" 2>/dev/null || echo "Label priority-high already exists"
gh label create "priority-medium" --color "FBCA04" --description "Normal priority" -R "$REPO" 2>/dev/null || echo "Label priority-medium already exists"
gh label create "priority-low" --color "0E8A16" --description "Nice to have" -R "$REPO" 2>/dev/null || echo "Label priority-low already exists"

# Type labels
gh label create "type-feature" --color "1D76DB" --description "New feature" -R "$REPO" 2>/dev/null || echo "Label type-feature already exists"
gh label create "type-research" --color "C2E0C6" --description "Research/Spike" -R "$REPO" 2>/dev/null || echo "Label type-research already exists"
gh label create "type-docs" --color "0075CA" --description "Documentation" -R "$REPO" 2>/dev/null || echo "Label type-docs already exists"

# Area labels
gh label create "area-architecture" --color "006B75" --description "System Architecture" -R "$REPO" 2>/dev/null || echo "Label area-architecture already exists"
gh label create "area-planning" --color "FEF2C0" --description "Project Planning" -R "$REPO" 2>/dev/null || echo "Label area-planning already exists"
gh label create "area-aws" --color "FF9900" --description "AWS/Infrastructure" -R "$REPO" 2>/dev/null || echo "Label area-aws already exists"

echo "✅ Labels created"
echo ""

# ============================================================
# STEP 2: Create Milestone
# ============================================================
echo "📅 Creating Sprint 1 milestone..."

MILESTONE_RESULT=$(gh api repos/$REPO/milestones \
  --method POST \
  --field title="$SPRINT_NAME" \
  --field state=open \
  --field description="Week of Mar 9-15: Project setup, requirements gathering, architecture decisions, team onboarding. Foundation sprint." \
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
echo "📋 Creating Sprint 1 Epic..."

EPIC_BODY='## Epic Goal
Establish project foundation through comprehensive planning, requirements definition, and architecture decisions. Set the team up for successful execution.

## Success Criteria
- [ ] All requirements documented and approved
- [ ] Architecture decisions recorded (ADRs)
- [ ] Development environment documented
- [ ] Team roles and responsibilities defined
- [ ] Project timeline with milestones established

## Sprint Capacity
- **Total Available:** 60 hours (2 devs × 5 days × 6 hrs)
- **Planned:** 50 hours (83% capacity)
- **Buffer:** 10 hours for planning discussions

## Stories
1. Requirements Gathering (5 pts)
2. Architecture Decision Records (5 pts)
3. Development Environment Setup (3 pts)
4. AWS Infrastructure Planning (5 pts)
5. Project Documentation (3 pts)

**Total: 21 points**

## Risks
| Risk | Probability | Mitigation |
|------|-------------|------------|
| Unclear requirements | Medium | Daily sync with PO |
| Scope creep | High | Strict backlog grooming |
| Technical unknowns | Medium | Schedule research spikes |

## Definition of Done (Epic)
- [ ] Architecture documented
- [ ] Team can access all tools
- [ ] Sprint 2 ready for planning
- [ ] Risk register updated'

gh issue create \
  --title="[EPIC] Sprint 1: Project Kickoff & Planning" \
  --body "$EPIC_BODY" \
  --label="epic" \
  --label="sprint-1" \
  --label="priority-high" \
  -R "$REPO"

echo "✅ Epic created"
echo ""

# ============================================================
# STEP 4: Create Story Issues
# ============================================================

echo "📝 Creating Sprint 1 Stories..."
echo ""

# Story 1: Requirements Gathering
echo "Creating Story 1: Requirements Gathering..."
STORY1_BODY='## User Story
As a product owner, I need comprehensive requirements documentation so the team understands what to build.

## Acceptance Criteria

### Functional Requirements
- [ ] User personas defined (minimum 3)
- [ ] User stories documented for MVP features
- [ ] Feature prioritization matrix (MoSCoW)
- [ ] Acceptance criteria for each story

### Non-Functional Requirements
- [ ] Performance targets (response times, throughput)
- [ ] Security requirements (authentication, data protection)
- [ ] Scalability targets (concurrent users, data volume)
- [ ] Browser support matrix

### Documentation
- [ ] Requirements stored in /docs/requirements.md
- [ ] User flows diagrammed
- [ ] Edge cases documented
- [ ] Constraints listed

## Deliverables
- requirements.md
- user-flows.mmd
- acceptance-criteria.md

## Estimated Effort
**5 story points** (~10 hours)

## Dependencies
None

## Definition of Done
- [ ] PO has approved requirements
- [ ] Team reviewed and understood
- [ ] All stories have acceptance criteria
- [ ] Documented in repository'

gh issue create \
  --title="[Sprint 1] Gather and document project requirements" \
  --body "$STORY1_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-1" \
  --label="priority-high" \
  --label="type-docs" \
  --label="area-planning" \
  -R "$REPO"

echo "✅ Story 1 created"

# Story 2: Architecture Decisions
echo "Creating Story 2: Architecture Decision Records..."
STORY2_BODY='## User Story
As a technical lead, I need documented architecture decisions so the team understands technical choices.

## Acceptance Criteria

### ADR-001: Frontend Framework
- [ ] Decision: SvelteKit 2.x with Svelte 5
- [ ] Alternatives considered: Next.js, Nuxt, Vue
- [ ] Decision rationale documented
- [ ] Trade-offs analyzed

### ADR-002: Backend Architecture
- [ ] Decision: Microservices with Fastify
- [ ] Alternatives: Express, NestJS, monolith
- [ ] Service boundaries defined
- [ ] Communication patterns documented

### ADR-003: Database
- [ ] Decision: PostgreSQL 16
- [ ] Alternatives: MySQL, MongoDB
- [ ] Schema approach documented
- [ ] Migration strategy defined

### ADR-004: Infrastructure
- [ ] Decision: AWS ECS + RDS
- [ ] Alternatives: Vercel, Railway, self-hosted
- [ ] Cost analysis included
- [ ] Scaling approach documented

### ADR-005: WebCodecs Implementation
- [ ] Decision: Client-side processing
- [ ] Alternatives: Server-side FFmpeg
- [ ] Browser compatibility analyzed
- [ ] Fallback strategy documented

## Deliverables
- /docs/adr/ directory with 5 ADRs
- Architecture diagram
- Tech stack summary

## Estimated Effort
**5 story points** (~10 hours)

## Dependencies
- Story 1: Requirements (for context)

## Definition of Done
- [ ] All ADRs in repo
- [ ] Team reviewed
- [ ] Diagrams created
- [ ] No blocking questions'

gh issue create \
  --title="[Sprint 1] Create Architecture Decision Records (ADRs)" \
  --body "$STORY2_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-1" \
  --label="priority-high" \
  --label="type-research" \
  --label="area-architecture" \
  -R "$REPO"

echo "✅ Story 2 created"

# Story 3: Dev Environment
echo "Creating Story 3: Development Environment Setup..."
STORY3_BODY='## User Story
As a developer, I need a documented development environment so I can start coding immediately.

## Acceptance Criteria

### Prerequisites
- [ ] Node.js 20+ installation guide
- [ ] pnpm installation and configuration
- [ ] Git setup with SSH keys
- [ ] GitHub CLI installation
- [ ] Docker Desktop setup

### IDE Setup
- [ ] VS Code extensions list
- [ ] Settings for consistent formatting
- [ ] Debugging configuration
- [ ] Task runners configured

### Repository Setup
- [ ] Fork/clone instructions
- [ ] Branch naming conventions
- [ ] Commit message format (conventional commits)
- [ ] Pull request template

### Verification
- [ ] Hello world test runs
- [ ] Linting works locally
- [ ] Tests run successfully
- [ ] Pre-commit hooks functional

## Deliverables
- /docs/development-setup.md
- .vscode/settings.json
- .vscode/extensions.json
- .vscode/launch.json

## Estimated Effort
**3 story points** (~6 hours)

## Dependencies
None

## Definition of Done
- [ ] New team member can setup in <30 min
- [ ] All tools documented
- [ ] Troubleshooting guide included
- [ ] Verified by team member'

gh issue create \
  --title="[Sprint 1] Document development environment setup" \
  --body "$STORY3_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-1" \
  --label="priority-high" \
  --label="type-docs" \
  --label="area-planning" \
  -R "$REPO"

echo "✅ Story 3 created"

# Story 4: AWS Infrastructure Planning
echo "Creating Story 4: AWS Infrastructure Planning..."
STORY4_BODY='## User Story
As a DevOps engineer, I need AWS infrastructure planned so we can deploy reliably.

## Acceptance Criteria

### Account Setup
- [ ] AWS account structure (dev/staging/prod)
- [ ] IAM roles and permissions
- [ ] Billing alerts configured
- [ ] Cost estimation complete

### Network Architecture
- [ ] VPC design (subnets, AZs)
- [ ] Security groups planned
- [ ] Load balancer strategy
- [ ] CDN (CloudFront) distribution

### Compute Resources
- [ ] ECS Fargate cluster design
- [ ] Service task definitions
- [ ] Auto-scaling policies
- [ ] Resource limits defined

### Data Storage
- [ ] RDS PostgreSQL configuration
- [ ] S3 buckets (media, logs)
- [ ] Backup strategy
- [ ] Encryption at rest

### Monitoring
- [ ] CloudWatch dashboards
- [ ] Alert thresholds
- [ ] Log aggregation
- [ ] Cost monitoring

## Deliverables
- /docs/infrastructure/aws-architecture.md
- Terraform/CloudFormation plan (optional)
- Cost estimate spreadsheet
- Security checklist

## Estimated Effort
**5 story points** (~10 hours)

## Dependencies
- Story 2: Architecture decisions

## Definition of Done
- [ ] Architecture diagram complete
- [ ] Cost estimate approved
- [ ] Security review passed
- [ ] Ready for Sprint 4 implementation'

gh issue create \
  --title="[Sprint 1] Plan AWS infrastructure architecture" \
  --body "$STORY4_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-1" \
  --label="priority-medium" \
  --label="type-research" \
  --label="area-aws" \
  -R "$REPO"

echo "✅ Story 4 created"

# Story 5: Project Documentation
echo "Creating Story 5: Project Documentation..."
STORY5_BODY='## User Story
As a stakeholder, I need comprehensive project documentation so I can understand the project status.

## Acceptance Criteria

### README.md
- [ ] Project overview and goals
- [ ] Tech stack summary
- [ ] Quick start guide
- [ ] Architecture overview
- [ ] Contributing guidelines

### Documentation Structure
- [ ] /docs/ directory organized
- [ ] API documentation placeholder
- [ ] Deployment guide placeholder
- [ ] Troubleshooting guide

### Project Management
- [ ] Sprint schedule defined
- [ ] Milestone dates set
- [ ] Team responsibilities
- [ ] Communication channels

### Risk Management
- [ ] Risk register created
- [ ] Mitigation strategies
- [ ] Escalation procedures
- [ ] Definition of Ready/Done

## Deliverables
- Comprehensive README.md
- /docs/ directory structure
- Project charter
- Risk register

## Estimated Effort
**3 story points** (~6 hours)

## Dependencies
- Story 1, 2, 3, 4 (for content)

## Definition of Done
- [ ] Documentation complete
- [ ] Links all work
- [ ] Spell-checked
- [ ] Team approved'

gh issue create \
  --title="[Sprint 1] Create comprehensive project documentation" \
  --body "$STORY5_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-1" \
  --label="priority-medium" \
  --label="type-docs" \
  --label="area-planning" \
  -R "$REPO"

echo "✅ Story 5 created"

# ============================================================
# STEP 5: Summary
# ============================================================
echo ""
echo "================================================"
echo "🎉 Sprint 1 Setup Complete!"
echo "================================================"
echo ""
echo "Repository: https://github.com/$REPO"
echo "Milestone: $SPRINT_NAME"
echo "Due: March 15, 2026"
echo ""
echo "Created:"
echo "  • 1 Epic"
echo "  • 5 Stories (21 points)"
echo "  • 12 Labels"
echo "  • 1 Milestone"
echo ""
echo "Next Steps:"
echo "  1. View issues: gh issue list -R $REPO --milestone '$SPRINT_NAME'"
echo "  2. Set up GitHub Project board with setup-sprint1-project.sh"
echo "  3. Conduct Sprint Planning meeting"
echo "  4. Begin requirements gathering"
echo ""
echo "Note: Automation workflows already in .github/workflows/"
echo ""
