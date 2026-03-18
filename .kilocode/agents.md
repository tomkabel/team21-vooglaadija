---
name: cobalt-project-context
description: Context and guidelines for working with the Cobalt media downloader project
version: 1.0.0
---

# Cobalt Project Context

## Project Overview

Cobalt is a media downloader monorepo that provides a fast and user-friendly way to save content from various social media and content platforms. The project consists of:

- **API** (`api/`): Express.js backend that handles media extraction, processing, and streaming
- **Web** (`web/`): SvelteKit frontend providing the user interface
- **Packages** (`packages/`): Shared utilities (version-info, api-client)

**Repository**: https://github.com/imputnet/cobalt  
**License**: AGPL-3.0 (API), CC-BY-NC-SA-4.0 (Web)

## Tech Stack

### API (Node.js >=18)
- **Framework**: Express.js 4.x
- **Language**: ES Modules (ESM), JavaScript
- **Key Dependencies**:
  - `undici` - HTTP client for fetching content
  - `zod` - Schema validation
  - `youtubei.js` - YouTube extraction
  - `nanoid` - ID generation
  - `ffmpeg-static` - Media processing
  - `hls-parser` - HLS stream handling
  - `express-rate-limit` - Rate limiting

### Web (Node.js >=20, pnpm >=9)
- **Framework**: SvelteKit 2.x with Svelte 5
- **Language**: TypeScript, Svelte
- **Key Dependencies**:
  - Vite 5.x - Build tool
  - `sveltekit-i18n` - Internationalization
  - `mdsvex` - Markdown processing
  - `@tabler/icons-svelte` - Icons
  - `libav.js` - Client-side media processing

### Monorepo
- **Package Manager**: pnpm 9.6.0
- **Workspace**: Defined in `pnpm-workspace.yaml`

## Architecture Patterns

### Service Architecture
Each media platform is implemented as a service in `api/src/processing/services/`:

```
services/
├── tiktok.js      # TikTok extraction
├── youtube.js     # YouTube extraction
├── instagram.js   # Instagram extraction
├── soundcloud.js  # SoundCloud extraction
└── ...
```

**Service Pattern**:
- Default export async function receiving `obj` with URL pattern matches
- Returns standardized response object with `urls`, `filename`, metadata
- Uses `Cookie` class for session management
- Returns error objects with standardized error codes (`{ error: "fetch.fail" }`)

### URL Processing Flow
1. `match.js` - Routes requests to appropriate service
2. `service-patterns.js` - URL pattern testers
3. Service modules - Platform-specific extraction
4. `match-action.js` - Post-processing and response formatting

### Cookie Management
- `Cookie` class in `processing/cookie/cookie.js`
- Managed via `cookie/manager.js` with `updateCookie()`
- Passed in headers for authenticated requests

### Stream Handling
- `stream/manage.js` - Creates proxy streams for large files
- Supports HLS streams via `hls-parser`

## Code Style

### JavaScript/Node.js
- ES Modules only (`"type": "module"`)
- Use `import`/`export` syntax
- Prefer `const` and `let` over `var`
- Use optional chaining (`?.`) and nullish coalescing (`??`)
- Async/await over raw promises where readable

### Naming Conventions
- camelCase for variables and functions
- PascalCase for classes (e.g., `Cookie`)
- Descriptive names for service functions

### Error Handling
- Return standardized error objects: `{ error: "error.code" }`
- Common error codes:
  - `fetch.fail` - Network/request failure
  - `fetch.empty` - No content found
  - `fetch.short_link` - Short link resolution failed
  - `content.too_long` - Content exceeds duration limit
  - `content.region` - Region-blocked content
  - `content.post.unavailable` - Post deleted or private
  - `content.post.age` - Age-restricted content
  - `link.unsupported` - URL pattern not supported

### Service Response Format
```javascript
// Video response
{
  urls: "https://...",           // or array for multiple qualities
  filename: "service_id.mp4",
  headers: { cookie },           // Optional cookie for authenticated fetch
  subtitles: "https://...",      // Optional subtitle URL
  fileMetadata: { ... }          // Optional metadata
}

// Audio response
{
  urls: "https://...",
  audioFilename: "service_id_audio",
  isAudioOnly: true,
  bestAudio: "m4a" | "mp3" | "opus",
  fileMetadata: { ... }
}

// Photo/gallery response
{
  picker: [
    { type: "photo", url: "https://..." },
    ...
  ],
  urls: "...",                   // Optional audio for slideshows
  audioFilename: "...",
  isAudioOnly: true
}
```

## Critical Constraints

### Security
- NEVER expose API keys or secrets in code
- Use `env.js` for environment variable management
- JWT tokens managed via `security/jwt.js`
- Turnstile/CAPTCHA via `security/turnstile.js`
- Rate limiting enabled by default

### Performance
- Respect `env.durationLimit` for audio content
- Use freebind for IP rotation when configured
- Stream large files instead of buffering
- Cache client IDs/tokens where appropriate (see `soundcloud.js` pattern)

### Content Policies
- Check for region blocks (`policy === "BLOCK"`)
- Check for paid/snipped content (`policy === "SNIP"`)
- Respect age restrictions (`isContentClassified`)
- Handle deleted/unavailable content gracefully

### Testing
- API tests in `api/src/util/test.js`
- Run with `npm test` in api directory

## Common Tasks

### Adding a New Service
See `.kilocode/templates/new-service.md` for the complete template.

Key steps:
1. Add URL patterns to `service-patterns.js`
2. Add tester function to `testers` export
3. Create service file in `services/` directory
4. Import and add service to `match.js` switch statement
5. Add alias to `service-alias.js` if needed

### Modifying URL Patterns
1. Update regex in `service-patterns.js`
2. Update tester function to validate captures
3. Test edge cases (short links, mobile URLs, etc.)

### Working with Cookies
```javascript
import Cookie from "../cookie/cookie.js";
import { updateCookie } from "../cookie/manager.js";

const cookie = new Cookie({});
const res = await fetch(url, { headers: { cookie } });
updateCookie(cookie, res.headers);
```

### Adding Environment Variables
1. Add to `api/src/core/env.js` with validation
2. Document in `api/README.md`
3. Use via `import { env } from "../../config.js"`

## File Organization

```
api/src/
├── cobalt.js          # Entry point
├── config.js          # Configuration exports
├── core/
│   ├── api.js         # Express setup
│   └── env.js         # Environment management
├── processing/
│   ├── match.js       # Service router
│   ├── match-action.js # Response processing
│   ├── service-patterns.js # URL validators
│   ├── services/      # Platform implementations
│   └── cookie/        # Cookie management
├── security/          # Auth, JWT, rate limiting
├── stream/            # Stream management
└── util/              # Utilities, tests

web/src/
├── app.html           # HTML template
├── app.css            # Global styles
├── components/        # Svelte components
├── lib/               # Utilities, stores
└── routes/            # SvelteKit routes
```

## Development Commands

```bash
# Root (pnpm)
pnpm install          # Install dependencies

# API
npm start             # Start API server
npm test              # Run tests

# Web
npm run dev           # Start dev server
npm run build         # Production build
npm run check         # TypeScript check
```

## Resources

- **Issues**: https://github.com/imputnet/cobalt/issues
- **Contributing**: See `CONTRIBUTING.md`
- **API Docs**: See `api/README.md`
- **Web Docs**: See `web/README.md`
