---
name: cobalt-dev
version: 1.0.0
description: "Development skill for the Cobalt media downloader project. Provides expertise in service implementation, testing, security auditing, and migration planning for the Cobalt monorepo."
homepage: https://github.com/imputnet/cobalt
metadata: {"kilo":{"emoji":"🎯","category":"development"}}
---

# Cobalt Development Skill 🎯

Development assistance for the Cobalt media downloader project, covering service implementation, testing, security auditing, and migration planning.

---

## Table of Contents

- [Trigger Terms](#trigger-terms)
- [Workflow](#workflow)
- [Tools](#tools)
- [Quick Start](#quick-start)
- [Examples](#examples)

---

## Trigger Terms

Use this skill when you encounter:

| Category | Terms |
|----------|-------|
| **Service Development** | add service, new platform, implement downloader, URL pattern, service file |
| **Testing** | write tests, test cases, coverage, test.json, validate service |
| **Security** | audit service, security review, SSRF, input validation, vulnerability |
| **Migration** | microservices, split monolith, bounded context, strangler fig, service extraction |
| **Code Quality** | review service, error handling, code patterns, refactor service |
| **Debugging** | fix service, debug extraction, error codes, fetch failed |

---

## Workflow

### Step 1: Understand the Request

Identify the user's goal:

| Goal | Action |
|------|--------|
| Add new service | Use `.kilocode/templates/new-service.md` |
| Write tests | Spawn `test-generator` subagent |
| Security audit | Spawn `service-auditor` subagent |
| Migration planning | Spawn `microservices-planner` subagent |
| Debug existing service | Analyze code and error patterns |

### Step 2: Gather Context

Always read relevant files:

```bash
# For service work
cat api/src/processing/services/[service].js
cat api/src/processing/service-patterns.js
cat api/src/processing/match.js

# For testing
cat api/src/util/test.json

# For project context
cat /home/notroot/Documents/cobalt/ai1/.kilocode/agents.md
```

### Step 3: Execute Task

Use appropriate subagents for complex tasks:

```
skill("cobalt-dev") spawn service-auditor:
  task: "Audit the YouTube service implementation"
  file: "api/src/processing/services/youtube.js"
```

### Step 4: Validate

Before completing:
- Run tests if available: `npm test`
- Check for TypeScript errors: `npm run check`
- Verify URL patterns work correctly
- Ensure error codes follow conventions

---

## Tools

### Subagents

| Subagent | Purpose | Trigger |
|----------|---------|---------|
| `service-auditor` | Security and quality audits | "audit this service" |
| `microservices-planner` | Migration planning | "plan microservices migration" |
| `test-generator` | Generate test suites | "write tests for [service]" |

### Templates

| Template | Use For |
|----------|---------|
| `.kilocode/templates/new-service.md` | Adding a new platform service |
| `.kilocode/workflows/new-service.md` | Step-by-step service creation |
| `.kilocode/workflows/microservices-migration.md` | Migration planning workflow |

### Reference Documents

| Document | Contents |
|----------|----------|
| `agents.md` | Project overview, architecture, code style |
| `service-patterns.js` | URL patterns and testers |
| `test.json` | Test case format and examples |

---

## Quick Start

### Adding a New Service

```
User: "Add support for the Bluesky social platform"

Actions:
1. Read agents.md for context
2. Read existing service example (e.g., twitter.js)
3. Follow new-service.md workflow
4. Create service file
5. Add URL patterns
6. Register in match.js
7. Generate tests with test-generator
8. Run npm test to validate
```

### Auditing a Service

```
User: "Audit the TikTok service for security issues"

Actions:
1. Read the service file
2. Spawn service-auditor subagent
3. Review findings
4. Address critical/high issues
5. Document medium/low issues
```

### Planning Migration

```
User: "Plan how to split Cobalt into microservices"

Actions:
1. Inventory all 21 services
2. Spawn microservices-planner
3. Review bounded contexts
4. Prioritize migration order
5. Create migration timeline
```

---

## Examples

### Service Implementation

```
"Create a service for downloading Vimeo videos"

Result:
- URL patterns for vimeo.com/*
- Service implementation using undici
- Proper error handling with standardized codes
- Cookie support if needed
- Test cases covering basic and error scenarios
```

### Security Audit

```
"Audit the Instagram service"

Result:
- SSRF prevention verification
- Input validation checks
- Error handling review
- Pattern compliance check
- Report with severity ratings and recommendations
```

### Test Generation

```
"Generate tests for the SoundCloud service"

Result:
- Basic test cases for tracks/playlists
- Audio-only extraction tests
- Error cases (private, deleted, region-blocked)
- Stable URL selection with documentation
- Complete test.json structure
```

### Migration Planning

```
"Design microservices architecture for Cobalt"

Result:
- 5-6 bounded contexts identified
- Service groupings with rationale
- Extraction sequence prioritized by risk
- Shared infrastructure recommendations
- Timeline estimates per phase
```

---

## Service Response Formats

When implementing services, return these standardized formats:

### Video
```javascript
{
    urls: "https://...",
    filename: "service_id.mp4",
    headers: { /* optional cookie */ },
    subtitles: "https://...", // optional
    fileMetadata: { /* optional */ }
}
```

### Audio
```javascript
{
    urls: "https://...",
    audioFilename: "service_id_audio",
    isAudioOnly: true,
    bestAudio: "m4a" | "mp3" | "opus",
    fileMetadata: { /* optional */ }
}
```

### Gallery/Photos
```javascript
{
    picker: [
        { type: "photo", url: "https://..." },
        // ...
    ],
    urls: "...", // optional audio
    audioFilename: "...",
    isAudioOnly: true // if audio only
}
```

### Error
```javascript
{
    error: "error.code"
}
```

Common error codes:
- `fetch.fail` - Network/request failure
- `fetch.empty` - No content found
- `content.post.unavailable` - Deleted/private content
- `content.region` - Region-blocked
- `content.post.age` - Age-restricted
- `link.unsupported` - URL not supported

---

## Best Practices

1. **Always validate URLs** against patterns before fetching
2. **Use undici** for HTTP requests, not native fetch
3. **Handle all errors** with try/catch and standardized codes
4. **Use Cookie class** for authenticated requests
5. **Stream large files** instead of buffering
6. **Return early** on error conditions
7. **Test edge cases** including private/region-blocked content
8. **Document URL patterns** with examples

---

## For Sub-Agent Usage

When spawning as a sub-agent, include full context:

```
sessions_spawn(
    task: "Implement a new service for [PLATFORM]. 
           Read /home/notroot/Documents/cobalt/ai1/.kilocode/agents.md for context.
           Follow patterns in existing services.
           Return standardized response format.
           Handle errors with appropriate codes.",
    label: "cobalt-service-[platform]",
    model: "sonnet"
)
```
