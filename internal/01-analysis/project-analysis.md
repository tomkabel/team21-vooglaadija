---
Project: Vooglaadija
Date: March 17, 2026
Status: Final
---

## Cobalt Project - Complete Analysis

### Project Overview
Cobalt is a media downloader service operating as a monorepo with three main components built using modern web technologies and deployed via Docker containers.

---

## 1. Repository Structure

```
cobalt/
├── .github/              # GitHub Actions CI/CD workflows
│   ├── workflows/       # 7 workflow files
│   └── ISSUE_TEMPLATE/  # Issue templates
├── .dockerignore
├── .deepsource.toml     # DeepSource code analysis
├── .gitignore
├── Dockerfile           # Multi-stage production build
├── LICENSE (AGPL-3.0)
├── README.md
├── CONTRIBUTING.md
├── package.json         # Root (pnpm workspace manager)
├── pnpm-lock.yaml
├── pnpm-workspace.yaml  # Workspace config: api, web, packages/*
├── api/                 # @imput/cobalt-api (Node.js backend)
├── web/                 # @imput/cobalt-web (SvelteKit frontend)
├── packages/
│   ├── api-client/     # @imput/cobalt-client (placeholder SDK)
│   └── version-info/   # @imput/version-info (git metadata)
└── docs/                # Documentation & examples
```

---

## 2. Technology Stack

### Package Management
- **pnpm** v9.6.0 (workspace monorepo)
- **Node.js** >=18 (API), >=20 (Web)
- **ES modules** (type: module)

### API (`@imput/cobalt-api`)
| Category | Technology | Version |
|----------|------------|---------|
| **Framework** | Express.js | ^4.21.2 |
| **HTTP Client** | undici | ^6.21.3 |
| **Video Processing** | ffmpeg-static | ^5.1.0 |
| **HLS Parsing** | hls-parser | ^0.10.7 |
| **YouTube Client** | youtubei.js | 15.1.1 |
| **Rate Limiting** | express-rate-limit | ^7.4.1 |
| **Redis (optional)** | rate-limit-redis, redis | ^4.7.0 |
| **Security** | cors, content-disposition-header, set-cookie-parser, ipaddr.js, url-pattern, zod | various |
| **Utilities** | mime, nanoid, @imput/psl, @datastructures-js/priority-queue | various |
| **Optional Dependencies** | freebind (IP rotation), rate-limit-redis | various |

### Web (`@imput/cobalt-web`)
| Category | Technology | Version |
|----------|------------|---------|
| **Framework** | SvelteKit | ^2.20.7 |
| **UI** | Svelte | ^5.0.0 |
| **Build Tool** | Vite | ^5.4.4 |
| **Adapter** | @sveltejs/adapter-static | ^3.0.6 |
| **Language** | TypeScript | ^5.5.0 |
| **Linting** | ESLint + typescript-eslint | ^9.16.0, ^8.18.0 |
| **Preprocessing** | svelte-preprocess, mdsvex | ^6.0.2, ^0.11.2 |
| **Client-side Processing** | @imput/libav.js-remux-cli, @imput/libav.js-encode-cli | ^6.8.7 |
| **Icons** | @tabler/icons-svelte | 3.6.0 |
| **Fonts** | @fontsource/ibm-plex-mono, @fontsource/redaction-10 | ^5.x |
| **I18n** | sveltekit-i18n | ^2.4.2 |
| **Sitemap** | svelte-sitemap | 2.6.0 |
| **Types** | turnstile-types | ^1.2.2 |

### Shared Packages
- **@imput/version-info**: Git metadata reader (no dependencies)
- **@imput/cobalt-client**: Empty placeholder (dev: tsup, typescript, prettier)

---

## 3. CI/CD Pipelines & Automation

### GitHub Actions Workflows

**Docker Build & Publish** (3 workflows, all `workflow_dispatch`):
1. **docker.yml** - Release images
   - Tags: `latest`, `{version}`, `{major}`, `{version}-{commit}`
   - Platforms: `linux/amd64,linux/arm64`
   - Pushes to: `ghcr.io/imputnet/cobalt`
2. **docker-staging.yml** - Staging images
   - Tag: `staging`
   - Platform: `linux/amd64`
3. **docker-develop.yml** - Development images
   - Tag: `develop`
   - Platform: `linux/amd64`

All use:
- docker/setup-qemu-action@v3 (multi-arch)
- docker/setup-buildx-action@v3
- docker/login-action@v3
- docker/metadata-action@v5
- docker/build-push-action@v6 (with GHA cache)

**Testing** (2 workflows, run on PR/push):

4. **test.yml** - Sanity checks
   - Check lockfile: `pnpm install --frozen-lockfile`
   - Web: `.github/test.sh web` → runs `check` + `build`
   - API: `.github/test.sh api` → starts server, POST test to Tumblr, verifies tunnel & content-length

5. **test-services.yml** - Integration tests for all services
   - Discovers enabled services via `node api/src/util/test get-services`
   - Matrix job: `run-tests-for <service>` for each of 21 services
   - Uses secrets: `API_EXTERNAL_PROXY` (HTTP_PROXY)
   - Uses vars: `TEST_IGNORE_SERVICES` (bilibili, instagram, facebook, youtube, vk, twitter, reddit by default)
   - Finnicky services can fail without failing the entire job

**Security**:

6. **codeql.yml** - CodeQL analysis
   - Triggers: push to any branch, PRs to main/7, weekly Friday 07:33
   - Language: javascript-typescript (build-mode: none)
   - Uploads to GitHub Security tab

**Automation**:

7. **fast-forward.yml** - PR automation
   - Listens for `/fast-forward` comment on PRs
   - Uses sequoia-pgp/fast-forward@v1 to rebase & merge

---

## 4. Build & Deployment

### Docker Multi-stage Build

**Stage 1: base** (`node:24-alpine`)
- Sets PNPM_HOME in PATH

**Stage 2: build**
- Copy entire repo
- Enable Corepack, install `python3` + `alpine-sdk` (for native builds)
- `pnpm install --prod --frozen-lockfile` with PNPM cache mount
- `pnpm deploy --filter=@imput/cobalt-api --prod /prod/api`

**Stage 3: api** (runtime)
- Copy `/prod/api` + `.git` from build stage
- Switch to non-root `node` user
- Expose 9000, CMD `node src/cobalt`

### Web Build Process

**Development**:
```
pnpm --prefix web dev
```
- Vite dev server with self-signed SSL (`@vitejs/plugin-basic-ssl`)
- COOP/COEP headers for SharedArrayBuffer

**Production Build**:
```
pnpm --prefix web build
```
- SvelteKit static adapter → `build/` directory
- Preprocesses: TypeScript, Svelte, mdsvex (markdown)
- Custom Vite plugins:
  - `checkDefaultApiEnv`: Requires `WEB_DEFAULT_API`
  - `enableCOEP`: Sets COOP/COEP headers
  - `exposeLibAV`: Serves @imput/libav.js WASM from node_modules
  - `generateSitemap`: Creates sitemap if `WEB_HOST` set
- Manual chunking for i18n JSON files per language
- OptimizeDeps excludes `@imput/libav.js-remux-cli`

**Deployment Options**:
- **Cloudflare Workers**: `wrangler.jsonc` with assets from `./build`
- **Static Hosting**: Any web server (nginx, Caddy, GitHub Pages, etc.)

### Docker Compose (Production)
Example provided in `docs/examples/docker-compose.example.yml`:
- Image: `ghcr.io/imputnet/cobalt:11` (version-tagged)
- Ports: 9000:9000
- Read-only root filesystem
- Watchtower for auto-updates (900s interval)
- Optional yt-session-generator sidecar for YouTube sessions
- Optional cookies volume mount

---

## 5. Testing Strategy

### Test Files Location
- `api/src/util/tests/*.json` - 21 service test suites (Bilibili through YouTube)

### Test Runner
- `api/src/util/test.js` - Custom CLI
- Commands:
  - `get-services`: List all services from `service-config.js`
  - `run-tests-for <service>`: Run tests for specific service
  - No args: Run all services sequentially

### Test Format (JSON)
```json
[
  {
    "name": "basic video",
    "url": "https://example.com/video",
    "params": { "downloadMode": "auto" },
    "expected": { "status": "stream", "code": 200 }
  }
]
```

### Test Execution
- Services marked as "finnicky" (IG, FB, YT, Twitter, Reddit, VK, Bilibili) can fail without failing CI
- Uses `HTTP_PROXY` secret to avoid rate limits
- Runs in GitHub Actions matrix for parallelization
- `.github/test.sh` script:
  - Web: `pnpm check` → `pnpm build`
  - API: Starts server, waits for port 3000, POSTs to test endpoint, validates response & content-length

---

## 6. Configuration & Environment

### API Environment Variables (30+)

**General** (`api/src/core/env.js`):
| Variable | Default | Purpose |
|----------|---------|---------|
| `API_URL` | (required) | Public-facing URL of this instance |
| `API_PORT` | 9000 | Listening port |
| `API_LISTEN_ADDRESS` | 0.0.0.0 | Bind address |
| `API_INSTANCE_COUNT` | (unset) | Enable clustering if >1 |
| `API_REDIS_URL` | (unset) | Redis for cluster state |
| `DISABLED_SERVICES` | (unset) | Comma-separated list |
| `COOKIE_PATH` | (unset) | Path to cookies.json |
| `PROCESSING_PRIORITY` | (unset) | Nice value for ffmpeg |
| `FORCE_LOCAL_PROCESSING` | never | never/session/always |
| `API_ENV_FILE` | (unset) | Hot-reload config from file/URL |

**Networking**:
| Variable | Purpose |
|----------|---------|
| `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY` | Undici proxy support |
| `FREEBIND_CIDR` | IPv6 CIDR for IP randomization (Linux) |
| `API_EXTERNAL_PROXY` | Deprecated, use HTTP_PROXY |

**Limits**:
| Variable | Default | Purpose |
|----------|---------|---------|
| `DURATION_LIMIT` | 10800 | Max processing time (seconds) |
| `TUNNEL_LIFESPAN` | 90 | Stream URL expiry (seconds) |
| `RATELIMIT_WINDOW` | 60 | Rate limit window (seconds) |
| `RATELIMIT_MAX` | 20 | Requests per window |
| `SESSION_RATELIMIT_MAX` | 10 | Session tokens per window |
| `TUNNEL_RATELIMIT_WINDOW` | 60 | Tunnel creation window |
| `TUNEL_RATELIMIT_MAX` | 40 | Tunnels per window |

**Security**:
| Variable | Purpose |
|----------|---------|
| `CORS_WILDCARD` | 1 to allow all origins, 0 to use CORS_URL |
| `CORS_URL` | Specific CORS origin |
| `TURNSTILE_SITEKEY` | Cloudflare Turnstile site key |
| `TURNSTILE_SECRET` | Cloudflare Turnstile secret |
| `JWT_SECRET` | HMAC secret for session tokens (required if sessions used) |
| `JWT_EXPIRY` | Session expiry (minutes, default 120) |
| `API_KEY_URL` | file:// or URL to JSON API keys |
| `API_AUTH_REQUIRED` | 1 to require API keys |

**Service-Specific** (YouTube):
| Variable | Purpose |
|----------|---------|
| `CUSTOM_INNERTUBE_CLIENT` | Android, iOS, TV, etc. |
| `YOUTUBE_SESSION_SERVER` | External session token service |
| `YOUTUBE_SESSION_INNERTUBE_CLIENT` | Client config for session server |
| `YOUTUBE_ALLOW_BETTER_AUDIO` | 1 to try high-quality audio |
| `ENABLE_DEPRECATED_YOUTUBE_HLS` | never/key/always |

### Web Environment Variables

**Public** (exposed to browser):
- `WEB_DEFAULT_API` (required) - API endpoint URL
- `WEB_HOST` - Site hostname (for sitemap, OG tags)
- `WEB_PLAUSIBLE_HOST` - Optional analytics endpoint
- `WEB_ENABLE_WEBCODECS` - Feature flag
- `WEB_ENABLE_DEPRECATED_YOUTUBE_HLS` - Feature flag

**Private**:
- Built-time only via SvelteKit `$env/static/private`

### Hot Reload Support
- API watches `API_ENV_FILE` (local file via inotify, remote URL via polling)
- Changes trigger `updateEnv()` and callbacks for dynamic limits/secrets
- Cluster-aware: primary broadcasts to workers via IPC

---

## 7. Security Features

### API
- **Authentication**: JWT (HS256) for session tokens, API keys from JSON file
- **Bot Protection**: Cloudflare Turnstile integration
- **Rate Limiting**: Three-tier (API requests, session tokens, tunnels) with Redis backend for scaling
- **CORS**: Wildcard or specific origin
- **Secrets Management**: Rate salts & stream salts generated once, synced to workers
- **IP Rotation**: Optional `freebind` for per-download IPv6 address randomization (Linux)
- **Proxy Support**: Per-request proxy via undici's EnvHttpProxyAgent

### Web
- **CSP**: Hash-based nonces with strict directives (`default-src: none`, `script-src` limited)
- **COOP/COEP**: Required for SharedArrayBuffer (libav.js WebAssembly)
- **Static Assets**: Subresource integrity via hashes
- **Turnstile**: Can be configured for challenge-solving

---

## 8. Supported Services

API supports 21 media services via dedicated handlers:
`bilibili, bluesky, dailymotion, facebook, instagram, loom, newgrounds, ok, pinterest, reddit, rutube, snapchat, soundcloud, streamable, tiktok, tumblr, twitch, twitter, vimeo, vk, xiaohongshu, youtube`

Each service has:
- Pattern matching (URLs, short links, alternate domains)
- Quality selection logic
- Download modes (video, audio-only, mute)
- Test suite in `api/src/util/tests/<service>.json`

---

## 9. Development Workflow

### Setup
```bash
git clone https://github.com/imputnet/cobalt
cd cobalt
pnpm install --frozen-lockfile
```

### Run API Locally
```bash
cd api
echo "API_URL=http://localhost:9000/" > .env
pnpm start
# Access at http://localhost:9000/
```

### Run Web Locally
```bash
cd web
pnpm dev
# Access at https://localhost:5173/ (with self-signed SSL)
```

### Run Tests
```bash
# Web sanity (build)
.github/test.sh web

# API sanity (starts server, runs POST test)
.github/test.sh api

# All service tests (takes hours)
node api/src/util/test
# or specific service
node api/src/util/test run-tests-for youtube
```

### Build for Production
```bash
# API (Docker)
docker build -t cobalt-api .

# Web (static)
cd web && pnpm build
# Output in web/build/
```

---

## 10. Key Architecture Patterns

### API
- **Modular Service Pattern**: Each service in `processing/services/` implements `{ extract, handle }`
- **Match Dispatcher**: `processing/match.js` routes URLs to services via pattern matching
- **Stream Tunneling**: Encrypted proxy system (`/tunnel`, `/itunnel`) for secure delivery
- **Clustering**: Node.js cluster with `reusePort` for horizontal scaling (requires Redis)
- **Hot Reload**: Environment file watcher supports live updates without restart

### Web
- **Static Generation**: SvelteKit adapter-static for optimal CDN performance
- **Client-side Processing**: Web Workers + libav.js WASM for in-browser transcoding
- **State Management**: Svelte stores for settings, theme, queue, turnstile, server-info
- **I18n**: sveltekit-i18n with JSON translation files
- **Storage**: IndexedDB/OPFS abstraction for persistent local data

---

## 11. Observability & Debugging

- **API Health**: `GET /` returns JSON with `{ version, commit, branch, remote }`
- **Rate Limit Headers**: `Ratelimit-Limit`, `Ratelimit-Remaining`, `Ratelimit-Reset`, `Ratelimit-Policy`
- **Logging**: Colored console output (Green/Yellow/Bright/Cyan for different message types)
- **Metrics**: Turnstile callbacks tracked, server info polling for uptime

---

## 12. Notable Implementation Details

- **ffmpeg-static**: Precompiled FFmpeg binary, requires `nscd` on Ubuntu 22.04 for DNS resolution
- **youtubei.js**: Full YouTube innertube implementation with poToken/visitor_data support
- **Freebind**: Linux-only feature (`/proc/sys/net/ipv6/conf/all/use_oif_addrs`) for IP rotation
- **Libav.js**: Custom `@imput/libav.js-*` packages provide WebAssembly transcoding in browser
- **Docker Read-only**: Container runs with `--read-only` flag, only writable tmpfs
- **Watchtower**: Included in example compose for automatic image updates

---

## 13. Deployment Topology

Typical production setup:
```
Internet → Reverse Proxy (nginx/Caddy) → Docker Container (cobalt:latest)
                                    ↓
                               Optional Redis
                                    ↓
                          Optional yt-session-generator
```

Web can be deployed separately to Cloudflare Workers or any CDN.

---

## 14. License
- API: AGPL-3.0
- Web: CC-BY-NC-SA-4.0
- Overall: AGPL-3.0 (unless specified otherwise)

This is a production-grade, well-architected system with comprehensive CI/CD, security hardening, and support for 21+ services. The codebase demonstrates modern Node.js and Svelte best practices with strong separation of concerns.
