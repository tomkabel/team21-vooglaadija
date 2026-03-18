#!/bin/bash

# =============================================================================
# Sprint 5 Setup Script - Advanced Features & Optimization
# Repository: https://github.com/tomkabel/team21-vooglaadija
# Sprint: April 6-12, 2026
# Focus: Batch Processing, Premium Features, Performance Optimization
# =============================================================================

set -e

REPO="tomkabel/team21-vooglaadija"
SPRINT_NAME="Sprint 5: Advanced Features & Optimization"
MILESTONE_DATE="2026-04-12T23:59:59Z"

echo "🚀 Setting up Sprint 5 for $REPO"
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

gh label create "sprint-5" --color "BFD4F2" --description "Sprint 5 work" -R "$REPO" 2>/dev/null || echo "Label sprint-5 already exists"
gh label create "epic" --color "0052CC" --description "Epic - large body of work" -R "$REPO" 2>/dev/null || echo "Label epic already exists"
gh label create "priority-critical" --color "B60205" --description "Blocks release" -R "$REPO" 2>/dev/null || echo "Label priority-critical already exists"
gh label create "priority-high" --color "D93F0B" --description "Important" -R "$REPO" 2>/dev/null || echo "Label priority-high already exists"
gh label create "priority-medium" --color "FBCA04" --description "Normal priority" -R "$REPO" 2>/dev/null || echo "Label priority-medium already exists"
gh label create "type-feature" --color "1D76DB" --description "New feature" -R "$REPO" 2>/dev/null || echo "Label type-feature already exists"
gh label create "type-optimization" --color "C2E0C6" --description "Performance" -R "$REPO" 2>/dev/null || echo "Label type-optimization already exists"
gh label create "area-premium" --color "FFD700" --description "Premium Features" -R "$REPO" 2>/dev/null || echo "Label area-premium already exists"
gh label create "area-performance" --color "5319E7" --description "Performance" -R "$REPO" 2>/dev/null || echo "Label area-performance already exists"

echo "✅ Labels created"
echo ""

# ============================================================
# STEP 2: Create Milestone
# ============================================================
echo "📅 Creating Sprint 5 milestone..."

MILESTONE_RESULT=$(gh api repos/$REPO/milestones \
  --method POST \
  --field title="$SPRINT_NAME" \
  --field state=open \
  --field description="Week of Apr 6-12: Batch processing, premium features, performance optimization. Feature-complete application." \
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
echo "📋 Creating Sprint 5 Epic..."

EPIC_BODY='## Epic Goal
Implement advanced features that differentiate the application and optimize performance for production use. This sprint makes the app feature-complete.

## Success Criteria
- [ ] Batch processing works for multiple videos
- [ ] Premium features implemented (higher limits, priority)
- [ ] Performance optimized (<2s load time)
- [ ] Caching layer implemented
- [ ] Error recovery improved

## Sprint Capacity
- **Total Available:** 60 hours (2 devs × 5 days × 6 hrs)
- **Planned:** 50 hours (83% capacity)
- **Buffer:** 10 hours

## Stories
1. Batch Processing (5 pts)
2. Premium Features (8 pts)
3. Performance Optimization (5 pts)
4. Caching Layer (5 pts)
5. Error Recovery & Resilience (3 pts)

**Total: 26 points**

## Risks
| Risk | Probability | Mitigation |
|------|-------------|------------|
| Performance gains less than expected | Medium | Set realistic targets |
| Premium feature complexity | Medium | Cut scope if needed |

## Dependencies
- Sprint 4: Infrastructure deployed
- Sprint 3: Core features working'

gh issue create \
  --title="[EPIC] Sprint 5: Advanced Features & Optimization" \
  --body "$EPIC_BODY" \
  --label="epic" \
  --label="sprint-5" \
  --label="priority-high" \
  -R "$REPO"

echo "✅ Epic created"
echo ""

# ============================================================
# STEP 4: Create Story Issues
# ============================================================

echo "📝 Creating Sprint 5 Stories..."
echo ""

# Story 1: Batch Processing
STORY1_BODY='## User Story
As a power user, I want to process multiple videos at once so I can save time.

## Acceptance Criteria

### Batch Upload
- [ ] Upload multiple files (drag folder or multi-select)
- [ ] Progress for each file individually
- [ ] Queue management (pause, resume, cancel)
- [ ] Batch summary (success/failure count)

### Batch Configuration
- [ ] Apply same settings to all videos
- [ ] Per-video override option
- [ ] Preset management (save/load configurations)

### Processing
- [ ] Parallel processing (up to 3 concurrent)
- [ ] Memory management (don'"'"'t load all)
- [ ] Background processing when tab inactive

### Results
- [ ] Batch download (ZIP of all outputs)
- [ ] Individual download links
- [ ] Processing history
- [ ] Re-process failed items

### UI
- [ ] Grid view of processing videos
- [ ] Individual progress bars
- [ ] Collapsible details per video
- [ ] Batch actions (cancel all, retry all)

## Technical Notes
- Worker pool for parallel processing
- IndexedDB for queue persistence
- Service Worker for background processing

## Estimated Effort
**5 story points** (~10 hours)

## Dependencies
- Sprint 3: Core video processing
- Sprint 4: Download service

## Definition of Done
- [ ] Multiple files upload
- [ ] Parallel processing works
- [ ] Queue persists on refresh
- [ ] Batch download works
- [ ] UI handles many items'

gh issue create \
  --title="[Sprint 5] Implement batch video processing" \
  --body "$STORY1_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-5" \
  --label="priority-high" \
  --label="type-feature" \
  --label="area-ui" \
  -R "$REPO"

echo "✅ Story 1 created"

# Story 2: Premium Features
STORY2_BODY='## User Story
As a business, I want premium features so users have incentive to upgrade.

## Acceptance Criteria

### Feature Gating
- [ ] Free tier: 5 conversions/day, max 100MB
- [ ] Premium: Unlimited, max 2GB
- [ ] Feature flags for premium
- [ ] Upgrade prompts in UI

### Stripe Integration
- [ ] Checkout session creation
- [ ] Subscription management
- [ ] Webhook handling
- [ ] Invoice/receipt emails

### Premium Features
- [ ] Priority processing queue
- [ ] 4K output support
- [ ] Batch processing (unlimited)
- [ ] No watermarks
- [ ] API access
- [ ] Custom presets

### User Dashboard
- [ ] Usage statistics
- [ ] Subscription status
- [ ] Upgrade/downgrade
- [ ] Payment history
- [ ] Cancel subscription

### Database Schema
- [ ] subscriptions table
- [ ] usage_tracking table
- [ ] payments table

## Pricing Tiers
| Tier | Price | Features |
|------|-------|----------|
| Free | $0 | 5/day, 100MB, 1080p |
| Pro | $9/mo | Unlimited, 2GB, 4K, batch |
| Team | $29/mo | Everything + API, support |

## Estimated Effort
**8 story points** (~16 hours)

## Dependencies
- Sprint 2: Auth service (user management)
- Sprint 4: Database

## Definition of Done
- [ ] Stripe integration works
- [ ] Feature gating functional
- [ ] Payment flows tested
- [ ] Webhooks handled
- [ ] Upgrade prompts visible'

gh issue create \
  --title="[Sprint 5] Implement premium subscription features with Stripe" \
  --body "$STORY2_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-5" \
  --label="priority-high" \
  --label="type-feature" \
  --label="area-premium" \
  -R "$REPO"

echo "✅ Story 2 created"

# Story 3: Performance Optimization
STORY3_BODY='## User Story
As a user, I want fast load times so I can start working immediately.

## Acceptance Criteria

### Bundle Optimization
- [ ] Code splitting by route
- [ ] Lazy load heavy components
- [ ] Tree shaking verification
- [ ] Bundle size <500KB initial

### Asset Optimization
- [ ] Images: WebP with fallbacks
- [ ] Fonts: Subset and preload
- [ ] CSS: Purge unused styles
- [ ] Icons: SVG sprites

### Caching
- [ ] Service Worker for assets
- [ ] Cache-first strategy
- [ ] Offline page support
- [ ] Cache invalidation on deploy

### Runtime Performance
- [ ] Virtual scrolling for long lists
- [ ] Debounced input handlers
- [ ] RequestAnimationFrame for animations
- [ ] Memory leak prevention

### Metrics
- [ ] Lighthouse score >90
- [ ] First Contentful Paint <1.5s
- [ ] Time to Interactive <3s
- [ ] Core Web Vitals passing

### Video Processing
- [ ] Frame skipping during seek
- [ ] Throttled encoding updates
- [ ] Web Worker optimization
- [ ] Memory pool for frames

## Performance Budget
| Metric | Budget |
|--------|--------|
| JS Bundle | 500KB |
| Images | 200KB |
| CSS | 50KB |
| Fonts | 100KB |
| Total | 850KB |

## Estimated Effort
**5 story points** (~10 hours)

## Dependencies
- Sprint 3: UI components

## Definition of Done
- [ ] Lighthouse >90
- [ ] Bundle sizes met
- [ ] Caching works
- [ ] Fast load times verified
- [ ] No memory leaks'

gh issue create \
  --title="[Sprint 5] Optimize application performance and bundle size" \
  --body "$STORY3_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-5" \
  --label="priority-high" \
  --label="type-optimization" \
  --label="area-performance" \
  -R "$REPO"

echo "✅ Story 3 created"

# Story 4: Caching Layer
STORY4_BODY='## User Story
As an operator, I want caching so the application is fast and reduces costs.

## Acceptance Criteria

### Redis Setup
- [ ] Redis cluster (ElastiCache)
- [ ] Connection pooling
- [ ] Serialization (JSON/msgpack)
- [ ] TTL management

### Application Caching
- [ ] Video metadata cache (1 hour)
- [ ] User session cache
- [ ] Rate limit counters
- [ ] Download URL cache (5 min)

### CDN Caching
- [ ] CloudFront cache rules
- [ ] Static assets (1 year)
- [ ] API responses (short TTL)
- [ ] Cache invalidation API

### Cache Strategies
- [ ] Cache-aside for reads
- [ ] Write-through for critical data
- [ ] Cache warming for hot data

### Monitoring
- [ ] Hit/miss ratio tracking
- [ ] Cache size monitoring
- [ ] Eviction tracking
- [ ] Performance impact metrics

## Cache Keys
```
video:metadata:{videoId}
user:session:{userId}
rate_limit:{ip}:{endpoint}
download:url:{videoId}
```

## Estimated Effort
**5 story points** (~10 hours)

## Dependencies
- Sprint 4: AWS infrastructure
- Story 2: Premium (rate limiting)

## Definition of Done
- [ ] Redis operational
- [ ] Cache hits improved
- [ ] Latency reduced
- [ ] Cost savings measured
- [ ] Invalidation works'

gh issue create \
  --title="[Sprint 5] Implement Redis caching layer" \
  --body "$STORY4_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-5" \
  --label="priority-medium" \
  --label="type-feature" \
  --label="area-aws" \
  -R "$REPO"

echo "✅ Story 4 created"

# Story 5: Error Recovery
STORY5_BODY='## User Story
As a user, I want the app to recover from errors so I don'"'"'t lose my work.

## Acceptance Criteria

### Error Handling
- [ ] Global error boundary
- [ ] Graceful degradation
- [ ] Retry logic with exponential backoff
- [ ] Circuit breaker pattern

### State Persistence
- [ ] Auto-save user progress
- [ ] Recover processing state
- [ ] Restore form inputs
- [ ] Queue persistence (IndexedDB)

### User Experience
- [ ] Clear error messages
- [ ] Recovery suggestions
- [ ] Manual retry options
- [ ] Contact support link

### Error Logging
- [ ] Structured error logs
- [ ] Error categorization
- [ ] User context capture
- [ ] Sentry integration

### Health Checks
- [ ] Service health endpoints
- [ ] Dependency checks (DB, Redis)
- [ ] Graceful shutdown handling
- [ ] Startup validation

## Error Categories
| Category | Action | User Message |
|----------|--------|--------------|
| Network | Retry 3x | "Connection issue. Retrying..." |
| Processing | Queue for retry | "Processing failed. Retrying..." |
| Fatal | Log & notify | "Something went wrong. Please refresh." |

## Estimated Effort
**3 story points** (~6 hours)

## Dependencies
- Sprint 3: Core features

## Definition of Done
- [ ] Errors caught gracefully
- [ ] Recovery works
- [ ] State persists
- [ ] Logging comprehensive
- [ ] User-friendly messages'

gh issue create \
  --title="[Sprint 5] Implement error recovery and resilience patterns" \
  --body "$STORY5_BODY" \
  --milestone "$SPRINT_NAME" \
  --label="sprint-5" \
  --label="priority-medium" \
  --label="type-feature" \
  -R "$REPO"

echo "✅ Story 5 created"

# ============================================================
# STEP 5: Summary
# ============================================================
echo ""
echo "================================================"
echo "🎉 Sprint 5 Setup Complete!"
echo "================================================"
echo ""
echo "Repository: https://github.com/$REPO"
echo "Milestone: $SPRINT_NAME"
echo "Due: April 12, 2026"
echo ""
echo "Created:"
echo "  • 1 Epic"
echo "  • 5 Stories (26 points)"
echo "  • 9 Labels"
echo "  • 1 Milestone"
echo ""
