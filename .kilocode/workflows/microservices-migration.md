---
name: microservices-migration-workflow
description: Workflow for planning and executing Cobalt's migration from monolith to microservices
version: 1.0.0
---

# Workflow: Microservices Migration for Cobalt

This document outlines the process for migrating Cobalt's monolithic API to a microservices architecture.

## Overview

Cobalt's API currently consists of 21 services in a single Express.js monolith. This workflow provides a structured approach to decomposing these into independent, deployable services.

## Migration Strategy: Strangler Fig Pattern

Instead of a big-bang rewrite, we'll gradually replace monolith functionality by:
1. Identifying bounded contexts (groups of related services)
2. Creating facade/proxy layer for routing
3. Migrating one context at a time
4. Decommissioning old code only after full migration

## Phase 1: Assessment & Planning

### Step 1: Inventory Current State

Document all existing services:

```bash
ls -la api/src/processing/services/
```

For each service, capture:
- Service name
- Lines of code
- External API dependencies
- Shared utility dependencies
- Cookie/authentication requirements
- Error code patterns used

### Step 2: Identify Bounded Contexts

Group services by domain:

```
Bounded Context Candidates:

1. Video Platforms
   - youtube.js, youtubeShorts.js, vimeo.js
   - Shared: video quality selection, subtitle handling

2. Social Short-Form
   - tiktok.js, instagram.js (reels)
   - Shared: watermark removal, mobile APIs

3. Social Media
   - twitter.js, instagram.js (posts/stories), reddit.js, pinterest.js
   - Shared: media galleries, metadata extraction

4. Audio Platforms
   - soundcloud.js, bandcamp.js, spotify.js
   - Shared: audio format selection, metadata

5. Streaming Services
   - twitch.js, streamable.js
   - Shared: HLS stream handling

6. Utility/Image
   - imgur.js, other image services
   - Shared: gallery extraction
```

### Step 3: Define Service Boundaries

For each bounded context, define:

```yaml
Context: Video Platforms
Services:
  - youtube
  - youtubeShorts
  - vimeo

API Surface:
  - POST /api/youtube
  - POST /api/youtubeShorts
  - POST /api/vimeo

Shared Components Needed:
  - CookieManager
  - StreamProxy
  - QualitySelector
  - ErrorHandler

Data Stores:
  - None (stateless)

External Dependencies:
  - YouTube API / youtubei.js
  - Vimeo API
```

### Step 4: Prioritize Migration Order

Rank contexts by:
1. **Low risk first**: Services with few dependencies
2. **High value first**: Most-used services
3. **Team expertise**: Familiar domains

Suggested order:
1. Utility/Image (simplest)
2. Audio Platforms (well-defined domain)
3. Streaming Services (distinct infrastructure)
4. Social Short-Form (high usage)
5. Social Media (complex, many services)
6. Video Platforms (most complex, highest risk)

## Phase 2: Infrastructure Preparation

### Step 5: Extract Shared Libraries

Create shared packages for:

```
packages/
├── cobalt-cookie/          # Cookie management
├── cobalt-stream/          # Stream proxy utilities
├── cobalt-errors/          # Error codes and handling
└── cobalt-testing/         # Test utilities
```

Each package:
- Independent versioning
- Clear API contract
- Comprehensive tests
- Documentation

### Step 6: Set Up API Gateway

Create routing facade:

```javascript
// api-gateway/routes.js
const routes = {
    // Migrated services
    '/api/soundcloud': { service: 'audio-platforms' },
    '/api/bandcamp': { service: 'audio-platforms' },
    
    // Monolith fallback
    '*': { service: 'monolith' }
};
```

Gateway responsibilities:
- Route to appropriate service
- Handle authentication
- Rate limiting
- Request/response logging
- Circuit breaking

### Step 7: Container Setup

Create Docker infrastructure:

```dockerfile
# Service template
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=3s \
    CMD curl -f http://localhost:3000/health || exit 1
CMD ["node", "index.js"]
```

## Phase 3: Service Extraction

### Step 8: Scaffold New Service

For each bounded context:

```bash
mkdir -p services/audio-platforms
cd services/audio-platforms
npm init -y
npm install express @cobalt/cookie @cobalt/stream
```

Create structure:
```
audio-platforms/
├── src/
│   ├── index.js          # Express app entry
│   ├── routes/
│   │   ├── soundcloud.js
│   │   └── bandcamp.js
│   └── shared/           # Context-specific shared code
├── test/
├── Dockerfile
├── package.json
└── README.md
```

### Step 9: Migrate Service Code

1. Copy service implementation from monolith
2. Update imports to use shared packages
3. Adapt to new structure
4. Add service-specific tests

Example migration:
```javascript
// Before (monolith)
import Cookie from "../cookie/cookie.js";
import { updateCookie } from "../cookie/manager.js";

// After (microservice)
import { Cookie, updateCookie } from "@cobalt/cookie";
```

### Step 10: Add Gateway Routes

Update API gateway:

```yaml
# gateway/config.yaml
routes:
  - path: /api/soundcloud/*
    target: http://audio-platforms:3000
    stripPath: false
    
  - path: /api/bandcamp/*
    target: http://audio-platforms:3000
    stripPath: false
```

### Step 11: Deploy Side-by-Side

Run both systems in parallel:

```yaml
# docker-compose.yml
services:
  monolith:
    image: cobalt-api:latest
    ports:
      - "3001:3000"
      
  audio-platforms:
    image: cobalt-audio-platforms:latest
    ports:
      - "3002:3000"
      
  gateway:
    image: cobalt-gateway:latest
    ports:
      - "3000:3000"
    environment:
      - MONOLITH_URL=http://monolith:3000
      - AUDIO_PLATFORMS_URL=http://audio-platforms:3000
```

## Phase 4: Validation & Cutover

### Step 12: Shadow Traffic

Route production traffic to both systems:

```javascript
// Gateway middleware
async function shadowRequest(req, service) {
    // Send to primary (monolith)
    const primary = await fetch(monolithUrl, req);
    
    // Async shadow to new service
    fetch(serviceUrl, req).then(res => {
        logComparison(req, primary, res);
    }).catch(err => {
        logError(req, err);
    });
    
    return primary;
}
```

### Step 13: Gradual Cutover

Use feature flags for controlled rollout:

```javascript
// Gateway routing logic
function route(req) {
    const service = getService(req.path);
    const rollout = getRolloutPercentage(service);
    
    if (Math.random() * 100 < rollout) {
        return routeToService(service, req);
    }
    return routeToMonolith(req);
}
```

Rollout stages:
1. 0% - Shadow only
2. 1% - Canary testing
3. 10% - Limited exposure
4. 50% - Half traffic
5. 100% - Full cutover

### Step 14: Monolith Cleanup

After 100% cutover:
1. Monitor for 1 week
2. Remove service code from monolith
3. Update documentation
4. Archive old tests

## Phase 5: Repeat

Return to Phase 3 for next bounded context.

## Rollback Procedures

### Immediate Rollback

```bash
# Set rollout to 0%
curl -X POST gateway/admin/rollout \
  -d '{"service": "audio-platforms", "percentage": 0}'
```

### Investigation Checklist

If issues arise:
- [ ] Check service health: `GET /health`
- [ ] Review error logs
- [ ] Compare responses: monolith vs service
- [ ] Check upstream dependencies
- [ ] Verify environment variables

## Success Metrics

Track throughout migration:

| Metric | Target | Measurement |
|--------|--------|-------------|
| Latency p99 | < 500ms | Gateway logs |
| Error rate | < 0.1% | Error tracking |
| Deploy frequency | Daily | CI/CD metrics |
| Rollback time | < 5 min | Incident response |
| Service independence | 100% | Can deploy without coordination |

## Common Challenges

### Shared State

Problem: Services share in-memory state
Solution: Extract to Redis/external cache

### Database Dependencies

Problem: Services share database
Solution: Each service owns its data; use events for sync

### Circular Dependencies

Problem: Service A depends on B, B depends on A
Solution: Merge into single service or extract shared component

### Testing Complexity

Problem: Integration testing across services
Solution: Contract testing with Pact; local Docker Compose stacks

## Timeline Estimate

| Phase | Duration | Cumulative |
|-------|----------|------------|
| 1: Assessment | 1 week | 1 week |
| 2: Infrastructure | 2 weeks | 3 weeks |
| 3-4: Per Context | 1-2 weeks | 3-15 weeks |
| 5: Documentation | 1 week | 4-16 weeks |

**Total estimated time**: 4-6 months for full migration

## References

- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [Domain-Driven Design](https://domainlanguage.com/ddd/reference/)
- [Cobalt Service Architecture](/home/notroot/Documents/cobalt/ai1/.kilocode/agents.md)
