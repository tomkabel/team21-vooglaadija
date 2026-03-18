---
name: new-service-workflow
description: Step-by-step workflow for adding a new service to Cobalt
version: 1.0.0
---

# Workflow: Adding a New Service to Cobalt

This document describes the complete process for adding a new media platform service to the Cobalt API.

## Prerequisites

- Understanding of the target platform's URL structure
- Knowledge of the platform's API or embedding mechanism
- Test URLs for validation
- Cobalt development environment set up

## Phase 1: Discovery & Planning

### Step 1: Research the Platform

1. **Identify URL patterns**
   - Desktop URLs
   - Mobile URLs
   - Short URL formats
   - International domain variants

2. **Understand content types**
   - Video
   - Audio
   - Images/galleries
   - Mixed content

3. **Check for existing issues**
   - Search GitHub issues for platform requests
   - Check if service is in feature backlog

### Step 2: Define Scope

Document the following:
- Supported URL patterns (regex)
- Content types to support
- Authentication requirements (cookies/tokens)
- Rate limiting behavior
- Geographic restrictions

## Phase 2: Implementation

### Step 3: Add URL Patterns

Edit `api/src/processing/service-patterns.js`:

```javascript
const patterns = {
    // Add your service patterns
    newservice: [
        /(?:https?:\/\/)?(?:www\.)?newservice\.com\/video\/(\w+)/,
        /(?:https?:\/\/)?m\.newservice\.com\/v\/(\w+)/,
    ],
};

const testers = {
    // Add tester functions
    newservice: (url, pattern) => {
        const match = pattern.match(url);
        if (!match) return false;
        return { id: match[1] };
    },
};
```

### Step 4: Create Service File

Create `api/src/processing/services/newservice.js`:

```javascript
import { env } from "../../config.js";
import { genericError } from '../match-action.js';

export default async function(obj) {
    const { id } = obj.matches;
    
    try {
        // Implementation here
        const apiUrl = `https://api.newservice.com/video/${id}`;
        const res = await fetch(apiUrl, {
            headers: {
                // Required headers
            }
        });
        
        if (!res.ok) {
            return { error: "fetch.fail" };
        }
        
        const data = await res.json();
        
        if (!data.videoUrl) {
            return { error: "fetch.empty" };
        }
        
        return {
            urls: data.videoUrl,
            filename: `newservice_${id}.mp4`,
        };
    } catch (e) {
        return genericError(e);
    }
}
```

### Step 5: Register Service

Edit `api/src/processing/match.js`:

```javascript
import newservice from "./services/newservice.js";

// In the switch statement:
case "newservice":
    return await newservice(obj);
```

### Step 6: Add Service Alias (Optional)

Edit `api/src/processing/service-alias.js`:

```javascript
const aliases = {
    // Add aliases
    "ns": "newservice",
    "newsvc": "newservice",
};
```

## Phase 3: Testing

### Step 7: Write Tests

Add to `api/src/util/test.json`:

```json
{
    "newservice": {
        "tests": {
            "basic": [
                {
                    "name": "standard video",
                    "url": "https://newservice.com/video/abc123",
                    "expected": { "status": "success" }
                }
            ],
            "errors": [
                {
                    "name": "private video",
                    "url": "https://newservice.com/video/private",
                    "expected": { 
                        "status": "error", 
                        "error": "content.post.unavailable" 
                    }
                }
            ]
        }
    }
}
```

### Step 8: Run Tests

```bash
cd api
npm test -- --service newservice
```

### Step 9: Manual Testing

1. Start the API server: `npm start`
2. Test with curl or the web UI
3. Verify different URL formats work
4. Check error handling

## Phase 4: Documentation

### Step 10: Update Documentation

1. Update `api/README.md` with new service
2. Add to supported services list
3. Document any special requirements

### Step 11: Code Review Checklist

Before submitting PR:

- [ ] URL patterns cover all common formats
- [ ] Error codes follow Cobalt conventions
- [ ] No hardcoded secrets or API keys
- [ ] Uses undici for HTTP requests
- [ ] Handles rate limiting gracefully
- [ ] Returns correct filename format
- [ ] Tests pass
- [ ] Documentation updated

## Common Issues & Solutions

### URL Pattern Not Matching

Debug with:
```javascript
const pattern = /your-pattern/;
const url = "https://example.com/test";
console.log(pattern.test(url), pattern.exec(url));
```

### Authentication Required

Use Cookie class:
```javascript
import Cookie from "../cookie/cookie.js";
const cookie = new Cookie({});
// ... use in fetch headers
```

### Rate Limiting

Check response status and return appropriate error:
```javascript
if (res.status === 429) {
    return { error: "fetch.fail" };
}
```

## Submission

Create a PR with:
1. Service implementation
2. URL patterns
3. Tests
4. Documentation updates
5. Example URLs for reviewers to test

Use the commit message format: `api/service: add [platform name] support`
