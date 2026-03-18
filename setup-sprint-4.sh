#!/bin/bash

# =============================================================================
# Sprint 4 Setup Script - AWS Infrastructure & Deployment
# Repository: https://github.com/tomkabel/team21-vooglaadija
# Sprint: March 30 - April 5, 2026
# Focus: Infrastructure as Code, Deployment, Production Readiness
# =============================================================================

set -e

REPO="tomkabel/team21-vooglaadija"
SPRINT_NAME="Sprint 4: AWS Infrastructure & Deployment"
MILESTONE_DATE="2026-04-05T23:59:59Z"

echo "🚀 Setting up Sprint 4 for $REPO"
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

gh label create "sprint-4" --color "C5DEF5" --description "Sprint 4 work" -R "$REPO" 2>/dev/null || echo "Label sprint-4 already exists"
gh label create "epic" --color "0052CC" --description "Epic - large body of work" -R "$REPO" 2>/dev/null || echo "Label epic already exists"
gh label create "priority-critical" --color "B60205" --description "Blocks release" -R "$REPO" 2>/dev/null || echo "Label priority-critical already exists"
gh label create "priority-high" --color "D93F0B" --description "Important" -R "$REPO" 2>/dev/null || echo "Label priority-high already exists"
gh label create "type-infra" --color "0052CC" --description "Infrastructure/DevOps" -R "$REPO" 2>/dev/null || echo "Label type-infra already exists"
gh label create "type-feature" --color "1D76DB" --description "New feature" -R "$REPO" 2>/dev/null || echo "Label type-feature already exists"
gh label create "area-aws" --color "FF9900" --description "AWS/Infrastructure" -R "$REPO" 2>/dev/null || echo "Label area-aws already exists"
gh label create "area-monitoring" --color "84B6EB" --description "Monitoring" -R "$REPO" 2>/dev/null || echo "Label area-monitoring already exists"
gh label create "area-download" --color "006B75" --description "Download Service" -R "$REPO" 2>/dev/null || echo "Label area-download already exists"

echo "✅ Labels created"
echo ""

# ============================================================
# STEP 2: Create Milestone
# ============================================================
echo "📅 Creating Sprint 4 milestone..."

MILESTONE_RESULT=$(gh api repos/$REPO/milestones \
  --method POST \
  --field title="$SPRINT_NAME" \
  --field state=open \
  --field description="Week of Mar 30-Apr 5: AWS infrastructure, deployment pipeline, monitoring. Production-ready setup." \
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
echo "📋 Creating Sprint 4 Epic..."

EPIC_BODY='## Epic Goal
Deploy the application to AWS with automated CI/CD, monitoring, and infrastructure as code. Make the application production-ready.

## Success Criteria
- [ ] Application deployed to AWS ECS
- [ ] Database running on RDS
- [ ] CI/CD pipeline deploys on merge
- [ ] Monitoring and alerting active
- [ ] Download service handles video fetching
- [ ] Infrastructure defined as code

## Sprint Capacity
- **Total Available:** 60 hours (2 devs × 5 days × 6 hrs)
- **Planned:** 50 hours (83% capacity)
- **Buffer:** 10 hours

## Stories
1. Terraform Infrastructure (8 pts)
2. Download Service API (5 pts)
3. CI/CD Deployment Pipeline (5 pts)
4. Monitoring & Alerting (5 pts)
5. Production Hardening (3 pts)

**Total: 26 points**

## Risks
| Risk | Probability | Mitigation |
|------|-------------|------------|
| AWS costs exceeding budget | Medium | Cost alerts, limits |
| Deployment failures | Medium | Staging environment |
| Security vulnerabilities | Medium | Security review |

## Dependencies
- Sprint 1: AWS planning
- Sprint 2: Auth service
- Sprint 3: Core features'

gh issue create \
  --title="[EPIC] Sprint 4: AWS Infrastructure & Deployment" \
  --body "$EPIC_BODY" \
  --label="epic" \
  --label="sprint-4" \
  --label="priority-high" \
  -R "$REPO"

echo "✅ Epic created"
echo ""

# ============================================================
# STEP 4: Create Story Issues
# ============================================================

echo "📝 Creating Sprint 4 Stories..."
echo ""

# Story 1: Terraform Infrastructure
STORY1_BODY='## User Story
As a DevOps engineer, I need infrastructure as code so deployments are repeatable and versioned.

## Acceptance Criteria

### Terraform Modules
- [ ] VPC with public/private subnets (3 AZs)
- [ ] ECS Fargate cluster
- [ ] RDS PostgreSQL instance
- [ ] ALB (Application Load Balancer)
- [ ] CloudFront distribution
- [ ] S3 buckets (assets, logs)
- [ ] Security groups
- [ ] IAM roles and policies

### Environment Separation
- [ ] dev environment (smaller instances)
- [ ] staging environment (prod-like)
- [ ] production environment
- [ ] Environment-specific variables

### State Management
- [ ] S3 backend for Terraform state
- [ ] State locking with DynamoDB
- [ ] Remote state for collaboration

### Outputs
- [ ] Service endpoints
- [ ] Database connection strings
- [ ] Resource ARNs

## Terraform Structure
```
infra/
├── modules/
│   ├── vpc/
│   ├── ecs/
│   ├── rds/
│   └── cloudfront/
├── environments/
│   ├── dev/
│   ├── staging/
│   └── prod/
└── main.tf
```

## Estimated Effort
**8 story points** (~16 hours)

## Dependencies
- Sprint 1: AWS architecture planning

## Definition of Done
- [ ] terraform plan succeeds
- [ ] Infrastructure creates without errors
- [ ] Multi-environment support
- [ ] State remotely managed
- [ ] Cost estimates documented'

gh issue create \
  --title="[Sprint 4] Implement Terraform infrastructure as code" \
  --body "$STORY1_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-4" \
  --label="priority-high" \
  --label="type-infra" \
  --label="area-aws" \
  -R "$REPO"

echo "✅ Story 1 created"

# Story 2: Download Service
STORY2_BODY='## User Story
As a user, I want to paste a video URL so the application can download and process it.

## Acceptance Criteria

### API Endpoints
- [ ] POST /api/v1/download - Submit download job
- [ ] GET /api/v1/download/:id/status - Check status
- [ ] GET /api/v1/download/:id - Get result

### Download Logic
- [ ] Support YouTube URLs (yt-dlp integration)
- [ ] Support direct video URLs
- [ ] Validate URLs (security check)
- [ ] Extract metadata (title, duration, formats)

### Processing Pipeline
- [ ] Queue download jobs
- [ ] Stream to S3 bucket
- [ ] Progress tracking
- [ ] Error handling (retry logic)

### Security
- [ ] URL whitelist/blacklist
- [ ] Rate limiting (5 downloads/hour per IP)
- [ ] File size limits (2GB max)
- [ ] Virus scanning (optional)

### Response Format
```json
{
  "id": "uuid",
  "url": "original-url",
  "status": "processing|completed|failed",
  "progress": 45,
  "metadata": { "title": "...", "duration": 120 },
  "resultUrl": "s3://bucket/video.mp4"
}
```

## Architecture
- Fastify service in /services/download/
- yt-dlp for YouTube extraction
- Bull queue for job management
- S3 for temporary storage

## Estimated Effort
**5 story points** (~10 hours)

## Dependencies
- Sprint 2: Auth service (for API security)
- Story 1: AWS infrastructure (S3, ECS)

## Definition of Done
- [ ] Downloads work for YouTube
- [ ] Progress tracking functional
- [ ] Rate limiting active
- [ ] Errors handled gracefully
- [ ] API documented'

gh issue create \
  --title="[Sprint 4] Implement download service for video URLs" \
  --body "$STORY2_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-4" \
  --label="priority-high" \
  --label="type-feature" \
  --label="area-download" \
  -R "$REPO"

echo "✅ Story 2 created"

# Story 3: CI/CD Pipeline
STORY3_BODY='## User Story
As a developer, I need automated deployment so code changes reach production quickly and safely.

## Acceptance Criteria

### Build Pipeline
- [ ] Docker image builds on PR
- [ ] Multi-stage builds (dev/prod)
- [ ] Image scanning (Trivy)
- [ ] Push to ECR

### Deployment Pipeline
- [ ] Staging auto-deploy on merge to main
- [ ] Production manual approval
- [ ] Database migrations run automatically
- [ ] Rollback capability

### GitHub Actions Workflows
- [ ] build.yml - Build and test
- [ ] deploy-staging.yml - Deploy to staging
- [ ] deploy-prod.yml - Deploy to production
- [ ] terraform.yml - Infrastructure changes

### Quality Gates
- [ ] All tests must pass
- [ ] Security scan clean
- [ ] Lint checks pass
- [ ] Type check passes

### Notifications
- [ ] Slack notification on deploy
- [ ] Email on failure
- [ ] Deployment log in issue

## Workflow Diagram
```
PR opened
    │
    ├──► Build & Test ────┐
    ├──► Security Scan ───┤──► Merge ──► Deploy Staging
    └──► Type Check ──────┘                    │
                                               ▼
                                    Manual Approval
                                               │
                                               ▼
                                        Deploy Prod
```

## Estimated Effort
**5 story points** (~10 hours)

## Dependencies
- Story 1: Terraform infrastructure
- Sprint 2: CI/CD foundation

## Definition of Done
- [ ] Staging auto-deploys
- [ ] Prod requires approval
- [ ] Rollback tested
- [ ] Team notified of deploys
- [ ] Failed deploys blocked'

gh issue create \
  --title="[Sprint 4] Set up CI/CD deployment pipeline to AWS" \
  --body "$STORY3_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-4" \
  --label="priority-high" \
  --label="type-infra" \
  --label="area-aws" \
  -R "$REPO"

echo "✅ Story 3 created"

# Story 4: Monitoring & Alerting
STORY4_BODY='## User Story
As an operator, I need monitoring so I can detect and respond to issues quickly.

## Acceptance Criteria

### Metrics Collection
- [ ] Application metrics (response times, error rates)
- [ ] Infrastructure metrics (CPU, memory, disk)
- [ ] Database metrics (connections, query times)
- [ ] Business metrics (downloads, conversions)

### CloudWatch Dashboards
- [ ] Application health dashboard
- [ ] Infrastructure overview
- [ ] Database performance
- [ ] Cost monitoring

### Alerts
- [ ] High error rate (>5% 5xx)
- [ ] High latency (p95 >2s)
- [ ] Database connection issues
- [ ] Disk space >80%
- [ ] Cost anomalies

### Log Aggregation
- [ ] Centralized logging (CloudWatch Logs)
- [ ] Structured JSON logs
- [ ] Log filtering and search
- [ ] Error log alerts

### Tracing
- [ ] Request tracing (X-Ray)
- [ ] Service dependency map
- [ ] Performance bottlenecks

## Alert Channels
- P1 (Critical): Page/SMS
- P2 (High): Slack #alerts
- P3 (Medium): Email
- P4 (Low): Dashboard only

## Estimated Effort
**5 story points** (~10 hours)

## Dependencies
- Story 1: AWS infrastructure
- Story 3: Deployment pipeline

## Definition of Done
- [ ] Dashboards visible
- [ ] Alerts configured
- [ ] Runbook created
- [ ] Team trained on alerts
- [ ] On-call rotation defined'

gh issue create \
  --title="[Sprint 4] Implement monitoring and alerting with CloudWatch" \
  --body "$STORY4_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-4" \
  --label="priority-high" \
  --label="type-infra" \
  --label="area-monitoring" \
  -R "$REPO"

echo "✅ Story 4 created"

# Story 5: Production Hardening
STORY5_BODY='## User Story
As a security engineer, I need production hardening so the application is secure.

## Acceptance Criteria

### Security Headers
- [ ] HSTS enabled
- [ ] CSP (Content Security Policy)
- [ ] X-Frame-Options
- [ ] X-Content-Type-Options
- [ ] Referrer-Policy

### SSL/TLS
- [ ] HTTPS only (redirect HTTP)
- [ ] TLS 1.2+ only
- [ ] Certificate auto-renewal
- [ ] HSTS preload ready

### Secrets Management
- [ ] AWS Secrets Manager integration
- [ ] No secrets in code
- [ ] Secret rotation documented
- [ ] Local dev uses .env.example

### DDoS Protection
- [ ] CloudFront rate limiting
- [ ] WAF basic rules
- [ ] Geographic restrictions (optional)

### Backup & Recovery
- [ ] Database automated backups
- [ ] Point-in-time recovery
- [ ] Cross-region backup (optional)
- [ ] Recovery tested monthly

### Security Scanning
- [ ] Dependency vulnerability scan
- [ ] Container image scan
- [ ] SAST in CI pipeline
- [ ] Security review checklist

## Security Checklist
- [ ] OWASP Top 10 addressed
- [ ] Security headers verified
- [ ] Secrets not in logs
- [ ] Input validation in place
- [ ] SQL injection prevented
- [ ] XSS protection

## Estimated Effort
**3 story points** (~6 hours)

## Dependencies
- All previous stories

## Definition of Done
- [ ] Security scan clean
- [ ] Headers verified
- [ ] Secrets managed
- [ ] Backup tested
- [ ] Checklist complete'

gh issue create \
  --title="[Sprint 4] Production security hardening" \
  --body "$STORY5_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-4" \
  --label="priority-high" \
  --label="type-infra" \
  --label="area-aws" \
  -R "$REPO"

echo "✅ Story 5 created"

# ============================================================
# STEP 5: Summary
# ============================================================
echo ""
echo "================================================"
echo "🎉 Sprint 4 Setup Complete!"
echo "================================================"
echo ""
echo "Repository: https://github.com/$REPO"
echo "Milestone: $SPRINT_NAME"
echo "Due: April 5, 2026"
echo ""
echo "Created:"
echo "  • 1 Epic"
echo "  • 5 Stories (26 points)"
echo "  • 9 Labels"
echo "  • 1 Milestone"
echo ""
echo "Next Steps:"
echo "  1. View issues: gh issue list -R $REPO --milestone '$SPRINT_NAME'"
echo "  2. Set up GitHub Project board"
echo "  3. Begin Terraform implementation"
echo ""
