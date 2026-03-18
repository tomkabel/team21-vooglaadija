---
Project: Vooglaadija
Date: March 17, 2026
Status: Final
---

# Course Project Enhancement Plan: Cobalt Media Downloader

## Executive Summary

This document provides comprehensive recommendations for enhancing the Cobalt media downloader application to align with course requirements covering 19 distinct topics. The analysis maps each course topic to current project capabilities, identified gaps, and specific enhancements required to demonstrate proficiency in all required areas.

---

## 1. Project Overview

### Current Architecture

Cobalt is a production-ready media downloader with the following components:

- **Backend**: Node.js/Express API (port 9000)
- **Frontend**: Svelte-based web interface
- **Database**: Redis (optional) for caching and rate limiting; in-memory storage as fallback
- **Containerization**: Docker with multi-stage builds
- **CI/CD**: GitHub Actions workflows for testing and Docker image publishing
- **Security**: JWT authentication, Turnstile (Cloudflare) bot protection, API keys, CORS configuration, HMAC-based secrets

### Current Feature Set

The application currently supports downloading media from 20+ platforms including YouTube, Twitter, TikTok, Instagram, Facebook, and various other services. It includes features such as format selection, quality preferences, tunnel/proxy streaming, and session-based rate limiting.

---

## 2. Course Topics Gap Analysis

| Topic | Current Status | Gap | Enhancement Required |
|-------|---------------|-----|---------------------|
| Development Process | Partial | No formal process documentation | Add ADRs, development guidelines |
| Git | Basic usage | No branch strategy, commit conventions | Add Conventional Commits, branch policy |
| Testing | Basic sanity tests | Limited coverage, no unit tests | Add Jest unit tests, integration tests |
| Code Quality | Partial | No linting enforcement, limited docs | Add ESLint, JSDoc, comprehensive README |
| AWS Cloud | Not deployed | No AWS infrastructure | Deploy to ECS Fargate with proper networking |
| CI/CD | GitHub Actions | Basic pipeline | Add complete pipeline with testing, security scanning |
| Performance | No profiling | No performance metrics | Add 0x, clinic.js for profiling |
| Profiling | None | Not implemented | Integrate Node.js profiling tools |
| Database Optimization | Redis used | No query optimization | Add connection pooling, caching strategies |
| Cost Analysis | Not done | No analysis | Create AWS cost estimation |
| Architecture Patterns | Modular | No formal patterns | Document architecture, add design patterns |
| OWASP | Partial | Missing some controls | Add comprehensive security headers |
| Auth vs Authorization | JWT implemented | No clear separation | Add RBAC, permission system |
| JWT | Implemented custom | Not standard library | Add proper JWT library with claims |
| CORS | Basic | Limited configuration | Add fine-grained CORS |
| Secret Management | Custom | Not production-ready | Integrate Vault or AWS Secrets Manager |
| Teamwork | N/A | No collaboration features | Add multi-user features |
| Prometheus/Grafana | None | Not implemented | Add Micrometer, Prometheus, Grafana |
| AI Integration | None | Not integrated | Add AI features for recommendations |

---

## 3. Detailed Enhancements by Topic

### 3.1 Development Process

**Current State**: The project uses standard GitHub flow but lacks formal development process documentation.

**Recommendations**:

1. Create an Architecture Decision Records (ADR) directory at `docs/adr/` with records for major decisions such as using Express.js, implementing JWT authentication, and choosing Redis for caching
2. Add a `DEVELOPMENT.md` file detailing:
   - Setup instructions for local development
   - Code style guidelines
   - Commit message format
   - Pull request process

**Example ADR Structure** (`docs/adr/001-choose-express-framework.md`):

```markdown
# ADR 001: Use Express.js as the API Framework

## Status
Accepted

## Context
We need a web framework for the cobalt API that handles HTTP requests efficiently.

## Decision
We will use Express.js 4.x as our API framework.

## Consequences
- Fast request handling
- Large ecosystem of middleware
- Familiar to most Node.js developers
```

---

### 3.2 Git and Commit Conventions

**Current State**: Basic Git usage with no enforced conventions.

**Recommendations**:

1. Add a `.commitlintrc.json` file to enforce Conventional Commits:

```json
{
  "extends": ["@commitlint/config-conventional"],
  "rules": {
    "type-enum": [
      2,
      "always",
      ["feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert"]
    ]
  }
}
```

2. Create a branch protection policy document:

```markdown
## Branch Strategy

- `main`: Production-ready code, protected
- `develop`: Integration branch for next release
- `feature/*`: Feature development branches
- `bugfix/*`: Bug fix branches
- `hotfix/*`: Emergency production fixes

All PRs require:
- At least 1 approval
- Passing CI/CD checks
- No merge conflicts
```

3. Add Git hooks with Husky:

```json
{
  "hooks": {
    "commit-msg": "commitlint -E HUSKY_GIT_PARAMS",
    "pre-commit": "npm test && npm run lint"
  }
}
```

---

### 3.3 Testing

**Current State**: Basic sanity checks in `.github/test.sh` but no comprehensive test suite.

**Recommendations**:

1. Install testing dependencies:

```bash
npm install --save-dev jest @types/jest supertest @types/supertest
```

2. Create a comprehensive test structure:

```
api/tests/
├── unit/
│   ├── jwt.test.js
│   ├── rate-limiter.test.js
│   ├── services/youtube.test.js
│   └── processing/url.test.js
├── integration/
│   ├── api.test.js
│   └── streaming.test.js
└── fixtures/
    ├── sample-urls.json
    └── mock-responses.json
```

3. Add unit tests for core functionality:

```javascript
// api/tests/unit/jwt.test.js
import jwt from '../../src/security/jwt.js';

describe('JWT Authentication', () => {
    const testIP = '192.168.1.1';

    describe('generate', () => {
        it('should generate a valid JWT token', () => {
            const { token, exp } = jwt.generate(testIP);
            expect(token).toMatch(/^[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+$/);
            expect(exp).toBeGreaterThan(0);
        });

        it('should include IP hash in token', () => {
            const { token } = jwt.generate(testIP);
            const [, payload] = token.split('.');
            const decoded = JSON.parse(Buffer.from(payload, 'base64url').toString());
            expect(decoded.sub).toBeDefined();
        });
    });

    describe('verify', () => {
        it('should verify valid tokens', () => {
            const { token } = jwt.generate(testIP);
            expect(jwt.verify(token, testIP)).toBe(true);
        });

        it('should reject tokens from different IPs', () => {
            const { token } = jwt.generate(testIP);
            expect(jwt.verify(token, '10.0.0.1')).toBe(false);
        });
    });
});
```

4. Add integration tests for API endpoints:

```javascript
// api/tests/integration/api.test.js
import request from 'supertest';
import app from '../../src/cobalt.js';

describe('API Endpoints', () => {
    describe('POST /api/json', () => {
        it('should return 400 for invalid URL', async () => {
            const response = await request(app)
                .post('/api/json')
                .send({ url: 'invalid-url' });
            expect(response.status).toBe(400);
        });

        it('should process valid YouTube URL', async () => {
            const response = await request(app)
                .post('/api/json')
                .send({ url: 'https://youtube.com/watch?v=test123' });
            expect(response.status).toBe(200);
            expect(response.body).toHaveProperty('url');
        });
    });
});
```

5. Add test coverage script to `package.json`:

```json
{
  "scripts": {
    "test": "node --experimental-vm-modules node_modules/jest/bin/jest.js",
    "test:coverage": "node --experimental-vm-modules node_modules/jest/bin/jest.js --coverage",
    "test:watch": "node --experimental-vm-modules node_modules/jest/bin/jest.js --watch"
  }
}
```

---

### 3.4 Code Quality and Documentation

**Current State**: Partial documentation exists in `docs/` but no linting enforcement.

**Recommendations**:

1. Add ESLint configuration (`api/.eslintrc.json`):

```json
{
  "env": {
    "node": true,
    "es2022": true
  },
  "extends": ["eslint:recommended"],
  "parserOptions": {
    "ecmaVersion": "latest",
    "sourceType": "module"
  },
  "rules": {
    "no-unused-vars": "error",
    "no-console": "warn",
    "prefer-const": "error",
    "eqeqeq": ["error", "always"]
  }
}
```

2. Add comprehensive JSDoc comments to core functions:

```javascript
/**
 * Processes a media URL and returns downloadable content information.
 *
 * @param {string} url - The URL of the media to process
 * @param {Object} options - Processing options
 * @param {string} [options.vCodec] - Video codec (h264, h265, av1)
 * @param {string} [options.aCodec] - Audio codec (aac, mp3, opus)
 * @param {boolean} [options.isAudioOnly] - Extract audio only
 * @param {Object} cookies - Authentication cookies for protected content
 * @returns {Promise<ProcessingResult>} Result containing download URLs and metadata
 * @throws {ValidationError} When URL is invalid or unsupported
 * @throws {ServiceError} When the media service returns an error
 *
 * @example
 * const result = await processUrl('https://youtube.com/watch?v=abc123', {
 *   vCodec: 'h264',
 *   isAudioOnly: false
 * }, {});
 * console.log(result.url); // Download URL
 */
export async function processUrl(url, options, cookies) {
    // Implementation
}
```

3. Create a comprehensive README.md:

```markdown
# Cobalt API

Best-in-class media downloading API with support for 20+ platforms.

## Features

- Multi-platform media downloading
- High-quality format extraction
- Rate limiting and quota management
- JWT-based session authentication
- Turnstile bot protection
- Redis caching support
- Docker containerization

## Quick Start

### Prerequisites

- Node.js 18+
- Redis (optional, for caching)

### Installation

```bash
npm install
```

### Configuration

Create a `.env` file:

```env
API_URL=https://api.example.com
API_PORT=9000
JWT_SECRET=your-secret-key
# Optional: Redis for caching
API_REDIS_URL=redis://localhost:6379
```

### Running

```bash
npm start
```

## API Endpoints

### POST /api/json

Process a media URL and get download information.

**Request:**

```json
{
  "url": "https://youtube.com/watch?v=xxxxx",
  "vCodec": "h264",
  "aCodec": "mp3"
}
```

**Response:**

```json
{
  "url": "https://...",
  "filename": "video.mp4",
  "ext": "mp4"
}
```

## Testing

```bash
npm test           # Run tests
npm run test:coverage  # Run with coverage
```

## Docker

```bash
docker build -t cobalt-api .
docker run -p 9000:9000 cobalt-api
```
```

---

### 3.5 AWS Cloud Management

**Current State**: Not deployed to AWS.

**Recommendations**:

1. Create AWS infrastructure using Terraform or AWS CDK:

```typescript
// infrastructure/cdk-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as secrets from 'aws-cdk-lib/aws-secretsmanager';
import * as alb from 'aws-cdk-lib/aws-elasticloadbalancingv2';

export class CobaltStack extends cdk.Stack {
  constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create ECR repository
    const ecrRepo = new ecr.Repository(this, 'CobaltApiRepo', {
      repositoryName: 'cobalt-api',
      lifecycleRules: [
        { maxImageCount: 10 }
      ]
    });

    // Create ECS Cluster
    const cluster = new ecs.Cluster(this, 'CobaltCluster', {
      clusterName: 'cobalt-cluster',
      enableFargateCapacityProviders: true
    });

    // Create Secrets
    const jwtSecret = new secrets.Secret(this, 'JwtSecret', {
      secretName: 'cobalt/jwt-secret',
      generateSecretString: {
        passwordLength: 32,
        excludePunctuation: true
      }
    });

    const redisSecret = new secrets.Secret(this, 'RedisSecret', {
      secretName: 'cobalt/redis-config'
    });

    // Create ALB
    const vpc = new ec2.Vpc(this, 'CobaltVPC', {
      maxAzs: 2
    });

    const lb = new alb.ApplicationLoadBalancer(this, 'CobaltALB', {
      vpc,
      internetFacing: true
    });

    // ECS Task Definition
    const taskDefinition = new ecs.FargateTaskDefinition(this, 'CobaltTask', {
      memoryLimitMiB: 1024,
      cpu: 512
    });

    taskDefinition.addContainer('cobalt-api', {
      image: ecs.ContainerImage.fromEcrRepository(ecrRepo),
      portMappings: [{ containerPort: 9000 }],
      environment: {
        API_URL: `https://${lb.loadBalancerDnsName}`,
        API_PORT: '9000'
      },
      secrets: {
        JWT_SECRET: ecs.Secret.fromSecretsManager(jwtSecret),
        API_REDIS_URL: ecs.Secret.fromSecretsManager(redisSecret, 'redis-url')
      },
      logging: ecs.LogDrivers.awsLogs({
        streamPrefix: 'cobalt-api',
        logGroup: new logs.LogGroup(this, 'CobaltLogGroup', {
          logGroupName: '/ecs/cobalt-api',
          retentionDays: 7
        })
      })
    });
  }
}
```

2. Create ECS service configuration:

```yaml
# infrastructure/ecs-service.yaml
version: 1
task_definition:
  ecs_family: cobalt-api
  ecs_task_role_arn: arn:aws:iam::123456789:role/CobaltTaskRole
  ecs_execution_role_arn: arn:aws:iam::123456789:role/CobaltExecutionRole
  network_mode: awsvpc
  ecs_container_name: cobalt-api
  containerDefinitions:
    - name: cobalt-api
      image: 123456789.dkr.ecr.us-east-1.amazonaws.com/cobalt-api:latest
      essential: true
      portMappings:
        - containerPort: 9000
          protocol: tcp
      environment:
        - name: API_PORT
          value: "9000"
      logConfiguration:
        logDriver: awslogs
        options:
          awslogs-group: /ecs/cobalt-api
          awslogs-region: us-east-1
          awslogs-stream-prefix: ecs
services:
  - name: cobalt-api
    ecs_cluster_name: cobalt-cluster
    desired_count: 2
    deployment_configuration:
      minimum_healthy_percent: 50
      maximum_percent: 200
    launch_type: FARGATE
    network_configuration:
      awsvpc_configuration:
        subnets:
          - subnet-xxxxx1
          - subnet-xxxxx2
        security_groups:
          - sg-xxxxx
        assign_public_ip: true
    load_balancer_configuration:
      container_name: cobalt-api
      container_port: 9000
      target_group_arn: arn:aws:elasticloadbalancing:us-east-1:123456789:targetgroup/cobalt-api/xxxxx
```

3. Create AWS cost estimation document:

```markdown
# AWS Cost Analysis

## Monthly Cost Estimate (Development/Testing)

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| ECS Fargate | 2 tasks, 0.5 vCPU, 1GB RAM, ~40h/month | ~$8.50 |
| Application Load BalB | 1 LB, ~50GB processed | ~$16.00 |
| ECR Storage | 1GB images | ~$0.09 |
| CloudWatch Logs | 1GB logs | ~$0.50 |
| Data Transfer | ~100GB/month | ~$4.50 |
| **Total** | | **~$29.59/month** |

## Production Cost Estimate

| Service | Configuration | Monthly Cost |
|---------|--------------|--------------|
| ECS Fargate | 4 tasks, 0.5 vCPU, 1GB RAM, 730h | ~$31.00 |
| Application Load BalB | 1 LB, ~500GB processed | ~$22.00 |
| ECR Storage | 5GB images | ~$0.45 |
| CloudWatch Logs | 10GB logs | ~$0.75 |
| Data Transfer | ~1TB/month | ~$9.00 |
| Secrets Manager | 5 secrets | ~$1.50 |
| **Total** | | **~$64.70/month** |
```

---

### 3.6 CI/CD, Docker, Pipeline

**Current State**: Basic GitHub Actions workflows for testing and Docker builds.

**Recommendations**:

1. Enhance the CI/CD pipeline with multiple stages:

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  lint:
    name: Code Quality
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm run lint
      - run: pnpm run typecheck

  test:
    name: Unit Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
      - run: pnpm install --frozen-lockfile
      - run: pnpm run test:coverage
      - uses: codecov/codecov-action@v4
        with:
          files: ./coverage/coverage-final.json

  security:
    name: Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run Snyk
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      - name: Run CodeQL
        uses: github/codeql-action/analyze@v3

  build:
    name: Docker Build
    runs-on: ubuntu-latest
    needs: [lint, test, security]
    if: github.event_name != 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      - name: Login to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=sha,prefix=
            type=raw,value=latest,enable={{is_default_branch}}
      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    name: Deploy to ECS
    runs-on: ubuntu-latest
    needs: build
    if: github.ref == 'refs/heads/main'
    steps:
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      - name: Deploy to ECS
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: ${{ steps.meta.outputs.tags }}
          cluster: cobalt-cluster
          service: cobalt-api
```

2. Create a production-ready Dockerfile:

```dockerfile
# Dockerfile
FROM node:20-alpine AS base
ENV PNPM_HOME="/pnpm"
ENV PATH="$PNPM_HOME:$PATH"

FROM base AS deps
WORKDIR /app
COPY api/package.json api/pnpm-lock.yaml ./
RUN corepack enable && pnpm install --frozen-lockfile --prod

FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules /app/node_modules
COPY api/ ./
RUN pnpm deploy --filter=@imput/cobalt-api --prod /dist

FROM base AS runner
WORKDIR /app

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 cobalt

COPY --from=builder --chown=cobalt:nodejs /dist /app
COPY --from=builder --chown=cobalt:nodejs /app/package.json /app/.git /app/

USER cobalt

EXPOSE 9000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD node -e "require('http').get('http://localhost:9000/api/health', (r) => process.exit(r.statusCode === 200 ? 0 : 1))"

CMD ["node", "src/cobalt"]
```

3. Add docker-compose for local development:

```yaml
# docker-compose.yml
version: '3.8'

services:
  api:
    build:
      context: .
      target: runner
    ports:
      - "9000:9000"
    environment:
      - API_URL=http://localhost:9000
      - API_PORT=9000
      - JWT_SECRET=dev-secret-key-min-16-chars
      - API_REDIS_URL=redis://redis:6379
      - CORS_WILDCARD=1
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-data:/var/lib/grafana

volumes:
  redis-data:
  prometheus-data:
  grafana-data:
```

---

### 3.7 Performance Optimization

**Current State**: No explicit performance optimization implementation.

**Recommendations**:

1. Add response compression:

```javascript
// api/src/middleware/compression.js
import express from 'express';
import compression from 'express-compression';

export function setupCompression(app) {
    app.use(compression({
        brotli: {
            enabled: true,
            quality: 6
        },
        gzip: {
            level: 6
        },
        threshold: 1024
    }));
}
```

2. Implement caching strategies:

```javascript
// api/src/middleware/cache.js
import crypto from 'crypto';

const memoryCache = new Map();

export function createCacheMiddleware(defaultTTL = 300) {
    return (req, res, next) => {
        if (req.method !== 'GET') {
            return next();
        }

        const cacheKey = crypto
            .createHash('md5')
            .update(req.originalUrl)
            .digest('hex');

        const cached = memoryCache.get(cacheKey);

        if (cached && cached.expiry > Date.now()) {
            return res
                .set('X-Cache', 'HIT')
                .json(cached.data);
        }

        const originalJson = res.json.bind(res);
        res.json = (data) => {
            memoryCache.set(cacheKey, {
                data,
                expiry: Date.now() + (defaultTTL * 1000)
            });
            return originalJson(data);
        };

        next();
    };
}

export function clearCache(pattern = '*') {
    if (pattern === '*') {
        memoryCache.clear();
    } else {
        for (const key of memoryCache.keys()) {
            if (key.includes(pattern)) {
                memoryCache.delete(key);
            }
        }
    }
}
```

3. Add connection pooling for Redis:

```javascript
// api/src/store/redis-pool.js
import { createPool } from 'redis';

const pool = createPool({
    url: process.env.API_REDIS_URL,
    maxClients: 50,
    enableOfflineQueue: true,
    connectTimeout: 10000,
    commandQueueScaleFactor: 0.1
});

export default pool;
```

---

### 3.8 Profiling

**Current State**: No profiling tools integrated.

**Recommendations**:

1. Add profiling scripts to package.json:

```json
{
  "scripts": {
    "profile": "0x --node-args='--max-old-space-size=4096' src/cobalt",
    "profile:clinic": "clinic doctor -- node src/cobalt",
    "profile:flame": "clinic flame -- node src/cobalt",
    "profile:heap": "clinic heapprofiler -- node src/cobalt"
  }
}
```

2. Create a profiling endpoint for production:

```javascript
// api/src/middleware/profiler.js
import { performance } from 'perf_hooks';
import v8 from 'v8';

export function createProfilerMiddleware() {
    return (req, res, next) => {
        if (req.query._profile !== 'true') {
            return next();
        }

        const start = process.hrtime.bigint();

        res.on('finish', () => {
            const end = process.hrtime.bigint();
            const duration = Number(end - start) / 1e6;

            console.log({
                type: 'request_profile',
                method: req.method,
                path: req.path,
                statusCode: res.statusCode,
                duration_ms: duration,
                heap_used: process.memoryUsage().heapUsed,
                external: process.memoryUsage().external
            });
        });

        next();
    };
}

export function getHeapSnapshot() {
    return v8.writeHeapSnapshot();
}

export function getMemoryUsage() {
    const usage = process.memoryUsage();
    return {
        rss: `${Math.round(usage.rss / 1024 / 1024)}MB`,
        heapTotal: `${Math.round(usage.heapTotal / 1024 / 1024)}MB`,
        heapUsed: `${Math.round(usage.heapUsed / 1024 / 1024)}MB`,
        external: `${Math.round(usage.external / 1024 / 1024)}MB`
    };
}

export function getCPUUsage() {
    const start = process.cpuUsage();
    return new Promise((resolve) => {
        setTimeout(() => {
            const end = process.cpuUsage(start);
            resolve({
                user: end.user / 1000000,
                system: end.system / 1000000
            });
        }, 100);
    });
}
```

3. Add profile endpoint to API:

```javascript
// Add to api/src/core/api.js
app.get('/api/debug/profile', async (req, res) => {
    res.json({
        memory: getMemoryUsage(),
        cpu: await getCPUUsage(),
        uptime: process.uptime(),
        pid: process.pid
    });
});
```

---

### 3.9 Database Optimization

**Current State**: Redis is used but not fully optimized.

**Recommendations**:

1. Implement Redis optimization strategies:

```javascript
// api/src/store/redis-optimized.js
import Redis from 'redis';

class OptimizedRedis {
    constructor(url, options = {}) {
        this.client = Redis.createClient({
            url,
            socket: {
                reconnectStrategy: (retries) => {
                    if (retries > 10) {
                        return new Error('Too many retries');
                    }
                    return Math.min(retries * 100, 3000);
                },
                keepAlive: 30000
            },
            legacyMode: false,
            ...options
        });
    }

    async connect() {
        await this.client.connect();
        await this.client.configSet('notify-keyspace-events', 'Ex');
    }

    async getWithFallback(key, fallback, ttl = 300) {
        const cached = await this.client.get(key);
        if (cached) {
            return JSON.parse(cached);
        }

        const value = await fallback();
        if (value) {
            await this.client.setEx(key, ttl, JSON.stringify(value));
        }
        return value;
    }

    async cacheWithInvalidation(key, data, ttl, pattern) {
        const pipeline = this.client.multi();

        // Set new value
        pipeline.setEx(key, ttl, JSON.stringify(data));

        // Invalidate related keys
        if (pattern) {
            const keys = await this.client.keys(pattern);
            if (keys.length > 0) {
                pipeline.del(keys);
            }
        }

        await pipeline.exec();
    }
}

export default OptimizedRedis;
```

2. Add database connection monitoring:

```javascript
// api/src/middleware/db-metrics.js
import { redis } from '../store/redis-store.js';

export async function getRedisMetrics() {
    const info = await redis.info('stats');
    const memory = await redis.info('memory');

    const stats = {};
    info.split('\r\n').forEach(line => {
        const [key, value] = line.split(':');
        if (key && value) {
            stats[key] = parseInt(value, 10);
        }
    });

    const memStats = {};
    memory.split('\r\n').forEach(line => {
        const [key, value] = line.split(':');
        if (key && value) {
            memStats[key] = parseInt(value, 10);
        }
    });

    return {
        totalConnections: stats.total_connections_received || 0,
        keyspaceHits: stats.keyspace_hits || 0,
        keyspaceMisses: stats.keyspace_misses || 0,
        hitRate: stats.keyspace_hits / (stats.keyspace_hits + stats.keyspace_misses) || 0,
        usedMemory: memStats.used_memory || 0,
        usedMemoryHuman: memStats.used_memory_human || '0'
    };
}
```

---

### 3.10 Cost Analysis

**Current State**: No cost analysis performed.

**Recommendations**:

Create a comprehensive cost analysis document:

```markdown
# Cobalt API Cost Analysis

## Architecture Overview

The application will be deployed on AWS using:
- ECS Fargate for container orchestration
- Application Load Balancer for traffic distribution
- ElastiCache Redis for caching
- ECR for container image storage
- CloudWatch for logging and monitoring

## Cost Breakdown by Environment

### Development Environment (Always On)

| Service | Configuration | Unit Price | Hours/Month | Cost |
|---------|--------------|------------|-------------|------|
| ECS Fargate | 0.25 vCPU, 0.5GB | $0.04048/vCPU-h | 730 | $7.39 |
| ECS Fargate | 0.5 GB | $0.004445/GB-h | 730 | $1.62 |
| ALB | Base | $16.20/mo | 730 | $16.20 |
| ALB | LCU | $0.008/LCU-h | 730 | $0.10 |
| ECR | Storage | $0.10/GB | 1 | $0.10 |
| CloudWatch | Logs | $0.50/GB | 0.5 | $0.25 |
| Data Transfer | Inter-region | $0.09/GB | 10 | $0.90 |
| **Total** | | | | **$26.56/mo** |

### Production Environment

| Service | Configuration | Unit Price | Usage | Cost |
|---------|--------------|------------|-------|------|
| ECS Fargate | 1 vCPU, 2GB | 4 tasks | 730h | $117.24 |
| ALB | Base | $16.20/mo | 730 | $16.20 |
| ALB | LCU | $0.008/LCU-h | 2000 | $0.60 |
| ElastiCache | cache.t3.medium | $0.152/hr | 730 | $110.96 |
| ECR | Storage | $0.10/GB | 5 | $0.50 |
| CloudWatch | Logs | $0.50/GB | 10 | $5.00 |
| Data Transfer | Out to Internet | $0.09/GB | 500 | $45.00 |
| Secrets Manager | 5 secrets | $0.40/secret | 1 | $2.00 |
| **Total** | | | | **$297.50/mo** |

## Cost Optimization Strategies

1. **Reserved Capacity**: Save 40% with 1-year reserved
2. **Spot Instances**: For non-critical batch processing
3. **S3 Lifecycle Policies**: Archive old logs to Glacier
4. **CloudWatch Logs Retention**: Reduce to 3 days for debug logs
5. **ALB Idle Timeout**: Set to 60 seconds to reduce idle costs
6. **Auto-scaling**: Scale to 1 instance during off-peak
```

---

### 3.11 Software Architecture Patterns

**Current State**: Modular architecture but no formal patterns documented.

**Recommendations**:

1. Document the current architecture:

```markdown
# Architecture Documentation

## Overview

Cobalt follows a modular monolith architecture with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│              Frontend (Svelte)          │
└─────────────────┬───────────────────────┘
                  │ HTTP/WebSocket
┌─────────────────┴───────────────────────┐
│         API Gateway (Express)           │
│  - Rate Limiting                        │
│  - Authentication                       │
│  - Request Validation                   │
│  - CORS                                 │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│           Processing Layer               │
│  - URL Parser                           │
│  - Service Matcher                      │
│  - Cookie Manager                       │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│          Service Adapters                │
│  - YouTube, TikTok, Instagram, etc.     │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│           Stream Handler                 │
│  - Proxy Streaming                      │
│  - FFmpeg Processing                    │
│  - HLS Handling                         │
└─────────────────────────────────────────┘
                  │
┌─────────────────┴───────────────────────┐
│           Storage Layer                  │
│  - Redis (Production)                   │
│  - In-Memory (Development)              │
└─────────────────────────────────────────┘
```

2. Implement the Repository Pattern:

```javascript
// api/src/store/repository.js
export class RateLimitRepository {
    constructor(store) {
        this.store = store;
    }

    async getRemaining(identifier) {
        const key = `ratelimit:${identifier}`;
        const data = await this.store.get(key);
        return data ? data.remaining : null;
    }

    async decrement(identifier) {
        const key = `ratelimit:${identifier}`;
        return this.store.decrement(key);
    }

    async setLimit(identifier, limit, window) {
        const key = `ratelimit:${identifier}`;
        return this.store.set(key, { limit, window, remaining: limit });
    }
}

export class TunnelRepository {
    constructor(store) {
        this.store = store;
    }

    async create(tunnelId, data, ttl = 3600) {
        const key = `tunnel:${tunnelId}`;
        return this.store.setEx(key, ttl, data);
    }

    async get(tunnelId) {
        const key = `tunnel:${tunnelId}`;
        return this.store.get(key);
    }

    async delete(tunnelId) {
        const key = `tunnel:${tunnelId}`;
        return this.store.delete(key);
    }
}
```

3. Implement the Factory Pattern for services:

```javascript
// api/src/processing/service-factory.js
import { readdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

class ServiceFactory {
    constructor() {
        this.services = new Map();
        this.loadServices();
    }

    loadServices() {
        const servicesPath = join(__dirname, 'services');
        const files = readdirSync(servicesPath).filter(f => f.endsWith('.js'));

        for (const file of files) {
            const servicePath = join(servicesPath, file);
            import(servicePath).then(module => {
                const serviceName = file.replace('.js', '');
                this.services.set(serviceName, module.default);
            });
        }
    }

    getService(name) {
        const ServiceClass = this.services.get(name);
        if (!ServiceClass) {
            throw new Error(`Service ${name} not found`);
        }
        return new ServiceClass();
    }

    getAllServices() {
        return Array.from(this.services.keys());
    }

    matchService(url) {
        for (const [name, ServiceClass] of this.services) {
            if (ServiceClass.matches(url)) {
                return this.getService(name);
            }
        }
        return null;
    }
}

export default new ServiceFactory();
```

---

### 3.12 OWASP Security

**Current State**: Partial security implementation (JWT, rate limiting).

**Recommendations**:

1. Add comprehensive security headers:

```javascript
// api/src/security/headers.js
import helmet from 'helmet';

export function setupSecurityHeaders(app) {
    app.use(helmet({
        contentSecurityPolicy: {
            directives: {
                defaultSrc: ["'self'"],
                scriptSrc: ["'self'", "'unsafe-inline'"],
                styleSrc: ["'self'", "'unsafe-inline'"],
                imgSrc: ["'self'", 'data:', 'https:'],
                connectSrc: ["'self'"],
                fontSrc: ["'self'"],
                objectSrc: ["'none'"],
                mediaSrc: ["'self'", 'https:'],
                frameSrc: ["'none'"]
            }
        },
        hsts: {
            maxAge: 31536000,
            includeSubDomains: true,
            preload: true
        },
        referrerPolicy: { policy: 'strict-origin-when-cross-origin' },
        noSniff: true,
        xssFilter: true,
        hidePoweredBy: true
    }));
}
```

2. Add input validation with Zod (already in dependencies):

```javascript
// api/src/validators/api.js
import { z } from 'zod';

export const processUrlSchema = z.object({
    url: z.string().url().min(1).max(2048),
    vCodec: z.enum(['h264', 'h265', 'av1', '']).optional(),
    aCodec: z.enum(['aac', 'mp3', 'opus', 'vorbis', '']).optional(),
    vQuality: z.number().min(0).max(1080).optional(),
    isAudioOnly: z.boolean().optional(),
    isAudioMuted: z.boolean().optional(),
    downloadFilename: z.string().max(256).optional(),
    tiktokAudioMuted: z.boolean().optional(),
    twitterGif: z.boolean().optional(),
    instagramReel: z.boolean().optional(),
    youtubeHLS: z.boolean().optional(),
    youtubeDubbed: z.boolean().optional(),
    youtubeBetterAudio: z.boolean().optional(),
    localProcessing: z.boolean().optional()
});

export const tunnelSchema = z.object({
    id: z.string().min(1).max(128),
    action: z.enum(['start', 'stop'])
});

export function validateRequest(schema) {
    return (req, res, next) => {
        try {
            schema.parse(req.body);
            next();
        } catch (error) {
            return res.status(400).json({
                error: 'Validation failed',
                details: error.errors
            });
        }
    };
}
```

3. Add SQL/Injection prevention for any database queries:

```javascript
// api/src/security/sanitization.js
import { z } from 'zod';

export function sanitizeString(input) {
    if (typeof input !== 'string') return '';

    return input
        .replace(/[<>'";&]/g, '')
        .substring(0, 10000);
}

export function sanitizeUrl(url) {
    try {
        const parsed = new URL(url);
        const allowedProtocols = ['http:', 'https:'];
        if (!allowedProtocols.includes(parsed.protocol)) {
            throw new Error('Invalid protocol');
        }
        return parsed.toString();
    } catch {
        throw new Error('Invalid URL');
    }
}
```

---

### 3.13 Authentication vs Authorization

**Current State**: JWT implemented but not clearly separated.

**Recommendations**:

1. Implement proper RBAC:

```javascript
// api/src/security/rbac.js
import { createError } from './errors.js';

export const Roles = {
    ANONYMOUS: 'anonymous',
    USER: 'user',
    PREMIUM: 'premium',
    ADMIN: 'admin'
};

export const Permissions = {
    DOWNLOAD: 'download',
    STREAM: 'stream',
    BULK_DOWNLOAD: 'bulk_download',
    CUSTOM_FORMATS: 'custom_formats',
    HIGH_QUALITY: 'high_quality',
    MANAGE_USERS: 'manage_users',
    VIEW_ANALYTICS: 'view_analytics',
    CONFIGURE_INSTANCE: 'configure_instance'
};

const rolePermissions = {
    [Roles.ANONYMOUS]: [Permissions.DOWNLOAD, Permissions.STREAM],
    [Roles.USER]: [
        Permissions.DOWNLOAD,
        Permissions.STREAM,
        Permissions.CUSTOM_FORMATS
    ],
    [Roles.PREMIUM]: [
        Permissions.DOWNLOAD,
        Permissions.STREAM,
        Permissions.CUSTOM_FORMATS,
        Permissions.BULK_DOWNLOAD,
        Permissions.HIGH_QUALITY
    ],
    [Roles.ADMIN]: Object.values(Permissions)
};

export function checkPermission(role, permission) {
    const permissions = rolePermissions[role] || [];
    return permissions.includes(permission);
}

export function requirePermission(permission) {
    return (req, res, next) => {
        const role = req.user?.role || Roles.ANONYMOUS;

        if (!checkPermission(role, permission)) {
            throw createError('Forbidden', 403);
        }

        next();
    };
}
```

2. Add role to JWT claims:

```javascript
// api/src/security/jwt.js
const generate = (ip, options = {}) => {
    const exp = Math.floor(new Date().getTime() / 1000) + env.jwtLifetime;

    const header = toBase64URL(JSON.stringify({
        alg: 'HS256',
        typ: 'JWT'
    }));

    const payload = toBase64URL(JSON.stringify({
        jti: nanoid(8),
        sub: getIPHash(ip),
        exp,
        role: options.role || 'anonymous',  // Add role to JWT
        permissions: options.permissions || []  // Add permissions
    }));

    const signature = sign(header, payload);

    return {
        token: `${header}.${payload}.${signature}`,
        exp: env.jwtLifetime - 2,
    };
}
```

---

### 3.14 JWT Implementation

**Current State**: Custom JWT implementation using Node.js crypto.

**Recommendations**:

1. Migrate to standard JWT library:

```javascript
// api/src/security/jwt-v2.js
import jwt from 'jsonwebtoken';

const options = {
    issuer: 'cobalt-api',
    audience: 'cobalt-clients',
    algorithm: 'HS256',
    expiresIn: '2m'
};

export function generateToken(payload, secret, customOptions = {}) {
    return jwt.sign(payload, secret, {
        ...options,
        ...customOptions
    });
}

export function verifyToken(token, secret) {
    try {
        return jwt.verify(token, secret, {
            ...options,
            algorithms: ['HS256']
        });
    } catch (error) {
        if (error.name === 'TokenExpiredError') {
            throw new Error('Token expired');
        }
        if (error.name === 'JsonWebTokenError') {
            throw new Error('Invalid token');
        }
        throw error;
    }
}

export function refreshToken(token, secret, newExpiry = '1h') {
    const decoded = jwt.verify(token, secret, {
        algorithms: ['HS256'],
        ignoreExpiration: true
    });

    delete decoded.iat;
    delete decoded.exp;

    return jwt.sign(decoded, secret, {
        ...options,
        expiresIn: newExpiry
    });
}
```

2. Add JWT rotation and refresh:

```javascript
// api/src/middleware/auth.js
import { generateToken, verifyToken, refreshToken } from '../security/jwt-v2.js';

app.post('/api/auth/refresh', async (req, res) => {
    const { refreshToken: token } = req.body;

    try {
        const decoded = verifyToken(token, process.env.JWT_REFRESH_SECRET);
        const newAccessToken = generateToken(
            { userId: decoded.userId },
            process.env.JWT_SECRET,
            { expiresIn: '2m' }
        );

        res.json({ accessToken: newAccessToken });
    } catch (error) {
        res.status(401).json({ error: 'Invalid refresh token' });
    }
});
```

---

### 3.15 CORS Configuration

**Current State**: Basic CORS with wildcard support.

**Recommendations**:

1. Add fine-grained CORS:

```javascript
// api/src/security/cors.js
import cors from 'cors';

const corsOptions = {
    origin: (origin, callback) => {
        const allowedOrigins = process.env.CORS_ALLOWED_ORIGINS
            ? process.env.CORS_ALLOWED_ORIGINS.split(',')
            : ['http://localhost:3000'];

        // Allow requests with no origin (mobile apps, curl)
        if (!origin) {
            return callback(null, true);
        }

        if (allowedOrigins.includes(origin)) {
            callback(null, true);
        } else {
            callback(new Error('Not allowed by CORS'));
        }
    },
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: [
        'Content-Type',
        'Authorization',
        'X-Requested-With',
        'Accept',
        'Origin'
    ],
    exposedHeaders: ['X-RateLimit-Remaining', 'X-RateLimit-Reset'],
    credentials: true,
    maxAge: 86400, // 24 hours
    preflightContinue: false,
    optionsSuccessStatus: 204
};

export function setupCors(app) {
    app.use(cors(corsOptions));

    // Handle preflight
    app.options('*', cors(corsOptions));
}
```

---

### 3.16 Secret Management

**Current State**: Custom secret management with environment variables.

**Recommendations**:

1. Integrate AWS Secrets Manager:

```typescript
// infrastructure/secrets.ts
import * as secretsManager from 'aws-cdk-lib/aws-secretsmanager';
import * as ecs from 'aws-cdk-lib/aws-ecs';

export function createSecrets(stack, clusterName) {
    // JWT Secret
    const jwtSecret = new secretsManager.Secret(stack, 'JwtSecret', {
        secretName: `cobalt/${clusterName}/jwt-secret`,
        generateSecretString: {
            excludeCharacters: '/@" ',
            passwordLength: 32,
            includeSpace: false
        }
    });

    // API Keys
    const apiKeysSecret = new secretsManager.Secret(stack, 'ApiKeys', {
        secretName: `cobalt/${clusterName}/api-keys`,
        generateSecretString: {
            secretStringTemplate: JSON.stringify({ keys: '[]' }),
            generateSecretString: () => ({})
        }
    });

    // Redis Credentials (if using auth)
    const redisSecret = new secretsManager.Secret(stack, 'RedisSecret', {
        secretName: `cobalt/${clusterName}/redis`,
        generateSecretString: {
            excludeCharacters: '/@" ',
            passwordLength: 24,
            includeSpace: false
        }
    });

    return { jwtSecret, apiKeysSecret, redisSecret };
}

export function addSecretToTaskDefinition(taskDef, secret, envVarName) {
    taskDef.addContainer('cobalt-api', {
        // ... other config
        secrets: {
            [envVarName]: ecs.Secret.fromSecretsManager(secret)
        }
    });
}
```

2. Add local secret management for development:

```javascript
// api/src/security/local-vault.js
import { readFileSync, existsSync } from 'fs';
import { join } from 'path';

class LocalVault {
    constructor() {
        this.secrets = {};
        this.loadVault();
    }

    loadVault() {
        const vaultPath = join(process.cwd(), '.vault');

        if (existsSync(vaultPath)) {
            const content = readFileSync(vaultPath, 'utf-8');
            const lines = content.split('\n');

            for (const line of lines) {
                const [key, ...valueParts] = line.split('=');
                if (key && valueParts.length > 0) {
                    this.secrets[key.trim()] = valueParts.join('=').trim();
                }
            }
        }
    }

    get(key) {
        return this.secrets[key] || process.env[key];
    }
}

export default new LocalVault();
```

---

### 3.17 Teamwork Features

**Current State**: Single-user application.

**Recommendations**:

1. Add user management:

```javascript
// api/src/models/user.js
import { z } from 'zod';

export const UserSchema = z.object({
    id: z.string().uuid(),
    email: z.string().email(),
    passwordHash: z.string(),
    role: z.enum(['anonymous', 'user', 'premium', 'admin']),
    createdAt: z.date(),
    updatedAt: z.date(),
    lastLoginAt: z.date().optional(),
    downloadCount: z.number().default(0),
    quotaUsed: z.number().default(0),
    quotaLimit: z.number().default(100),
    settings: z.object({
        defaultFormat: z.string().optional(),
        notifications: z.boolean().default(true)
    }).optional()
});

export class UserRepository {
    constructor(store) {
        this.store = store;
    }

    async create(userData) {
        const user = {
            id: crypto.randomUUID(),
            ...userData,
            createdAt: new Date(),
            updatedAt: new Date()
        };
        await this.store.set(`user:${user.id}`, user);
        return user;
    }

    async findById(id) {
        return this.store.get(`user:${id}`);
    }

    async findByEmail(email) {
        const key = `user:email:${email}`;
        const userId = await this.store.get(key);
        if (userId) {
            return this.store.get(`user:${userId}`);
        }
        return null;
    }

    async updateQuota(userId, downloadSize) {
        const user = await this.findById(userId);
        if (!user) return false;

        user.quotaUsed += downloadSize;
        user.downloadCount += 1;
        await this.store.set(`user:${userId}`, user);

        return user.quotaUsed <= user.quotaLimit;
    }
}
```

2. Add API key management for teams:

```javascript
// api/src/security/api-keys.js
import crypto from 'crypto';

export class ApiKeyService {
    constructor(store) {
        this.store = store;
    }

    async createKey(userId, name, permissions = []) {
        const keyId = `key_${crypto.randomBytes(16).toString('hex')}`;
        const secret = crypto.randomBytes(32).toString('hex');

        const keyData = {
            keyId,
            userId,
            name,
            permissions,
            createdAt: Date.now(),
            lastUsed: null,
            rateLimit: {
                window: 60,
                max: 100
            }
        };

        // Hash the secret before storing
        const secretHash = crypto
            .createHash('sha256')
            .update(secret)
            .digest('hex');

        await this.store.set(`apikey:${keyId}`, {
            ...keyData,
            secretHash
        });

        return {
            ...keyData,
            secret  // Only returned once
        };
    }

    async verifyKey(keyId, secret) {
        const keyData = await this.store.get(`apikey:${keyId}`);
        if (!keyData) return null;

        const secretHash = crypto
            .createHash('sha256')
            .update(secret)
            .digest('hex');

        if (secretHash !== keyData.secretHash) return null;

        // Update last used
        keyData.lastUsed = Date.now();
        await this.store.set(`apikey:${keyId}`, keyData);

        return keyData;
    }

    async revokeKey(keyId) {
        await this.store.delete(`apikey:${keyId}`);
    }
}
```

---

### 3.18 Micrometer, Prometheus, Grafana

**Current State**: Not implemented.

**Recommendations**:

1. Add Micrometer metrics:

```javascript
// api/src/monitoring/metrics.js
import { Registry, Counter, Gauge, Histogram, Summary } from 'prom-client';

const register = new Registry();

// Add default metrics
register.setDefaultLabels({ app: 'cobalt-api' });

// HTTP request metrics
export const httpRequestsTotal = new Counter({
    name: 'http_requests_total',
    help: 'Total number of HTTP requests',
    labelNames: ['method', 'route', 'status'],
    registers: [register]
});

export const httpRequestDuration = new Histogram({
    name: 'http_request_duration_ms',
    help: 'Duration of HTTP requests in milliseconds',
    labelNames: ['method', 'route', 'status'],
    buckets: [0.1, 0.5, 1, 3, 5, 10, 25, 50, 100, 250, 500, 1000],
    registers: [register]
});

// Business metrics
export const downloadsTotal = new Counter({
    name: 'cobalt_downloads_total',
    help: 'Total number of downloads',
    labelNames: ['service', 'format', 'quality'],
    registers: [register]
});

export const activeSessions = new Gauge({
    name: 'cobalt_active_sessions',
    help: 'Number of active download sessions',
    registers: [register]
});

export const tunnelQueueSize = new Gauge({
    name: 'cobalt_tunnel_queue_size',
    help: 'Number of tunnels in queue',
    registers: [register]
});

// Processing metrics
export const processingDuration = new Histogram({
    name: 'cobalt_processing_duration_ms',
    help: 'Duration of media processing in milliseconds',
    labelNames: ['service', 'success'],
    buckets: [100, 500, 1000, 3000, 5000, 10000, 30000, 60000],
    registers: [register]
});

// Rate limit metrics
export const rateLimitHits = new Counter({
    name: 'cobalt_rate_limit_hits_total',
    help: 'Total number of rate limit hits',
    labelNames: ['identifier', 'limit_type'],
    registers: [register]
});

export const currentRateLimit = new Gauge({
    name: 'cobalt_current_rate_limit',
    help: 'Current rate limit for identifier',
    labelNames: ['identifier'],
    registers: [register]
});

// Redis metrics
export const redisOperationDuration = new Histogram({
    name: 'cobalt_redis_operation_duration_ms',
    help: 'Duration of Redis operations in milliseconds',
    labelNames: ['operation', 'success'],
    buckets: [0.1, 0.5, 1, 5, 10, 50, 100],
    registers: [register]
});

// System metrics
export const activeConnections = new Gauge({
    name: 'cobalt_active_connections',
    help: 'Number of active connections',
    registers: [register]
});

export default register;
```

2. Add metrics middleware:

```javascript
// api/src/middleware/metrics.js
import register, {
    httpRequestsTotal,
    httpRequestDuration,
    activeConnections
} from '../monitoring/metrics.js';

export function metricsMiddleware(req, res, next) {
    const start = Date.now();

    res.on('finish', () => {
        const duration = Date.now() - start;
        const route = req.route?.path || req.path;

        httpRequestsTotal.inc({
            method: req.method,
            route,
            status: res.statusCode
        });

        httpRequestDuration.observe({
            method: req.method,
            route,
            status: res.statusCode
        }, duration);

        activeConnections.dec();
    });

    activeConnections.inc();
    next();
}

export function metricsEndpoint(app) {
    app.get('/metrics', async (req, res) => {
        try {
            res.set('Content-Type', register.contentType);
            res.end(await register.metrics());
        } catch (ex) {
            res.status(500).end(ex);
        }
    });

    app.get('/metrics/json', async (req, res) => {
        res.set('Content-Type', register.contentType);
        res.end(await register.getSingleMetricAsJSON('http_requests_total'));
    });
}
```

3. Create Grafana dashboard configuration:

```json
// grafana/dashboards/cobalt-api.json
{
  "dashboard": {
    "title": "Cobalt API Metrics",
    "uid": "cobalt-api",
    "timezone": "browser",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (method)",
            "legendFormat": "{{method}}"
          }
        ]
      },
      {
        "title": "Request Duration (p95)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_ms_bucket[5m])) by (le))",
            "legendFormat": "p95"
          }
        ]
      },
      {
        "title": "Downloads by Service",
        "type": "piechart",
        "targets": [
          {
            "expr": "sum(increase(cobalt_downloads_total[24h])) by (service)"
          }
        ]
      },
      {
        "title": "Active Sessions",
        "type": "stat",
        "targets": [
          {
            "expr": "cobalt_active_sessions"
          }
        ]
      },
      {
        "title": "Rate Limit Hits",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(increase(cobalt_rate_limit_hits_total[5m])) by (limit_type)",
            "legendFormat": "{{limit_type}}"
          }
        ]
      },
      {
        "title": "Processing Duration",
        "type": "heatmap",
        "targets": [
          {
            "expr": "sum(rate(cobalt_processing_duration_ms_bucket[5m])) by (le, service)"
          }
        ]
      }
    ]
  }
}
```

4. Add Prometheus configuration:

```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'cobalt-api'
    static_configs:
      - targets: ['api:9000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

rule_files:
  - 'alerts.yml'
```

---

### 3.19 AI Integration

**Current State**: Not implemented.

**Recommendations**:

1. Add AI-powered features:

```javascript
// api/src/ai/recommendations.js
import { z } from 'zod';

const recommendationSchema = z.object({
    userId: z.string().optional(),
    url: z.string().url(),
    preferences: z.object({
        quality: z.enum(['low', 'medium', 'high', 'ultra']).optional(),
        format: z.enum(['mp4', 'mp3', 'webm']).optional()
    }).optional()
});

export async function getDownloadRecommendation(url, userHistory = []) {
    // Analyze URL patterns from user history
    const patterns = analyzeHistoryPatterns(userHistory);

    // Get service-specific recommendations
    const serviceRecommendations = getServiceDefaults(url);

    // Combine with user preferences
    return {
        recommended: {
            format: patterns.preferredFormat || serviceRecommendations.defaultFormat,
            quality: patterns.preferredQuality || serviceRecommendations.defaultQuality,
            codec: patterns.preferredCodec || serviceRecommendations.defaultCodec
        },
        confidence: patterns.confidence || 0.7,
        reasoning: patterns.reasoning || 'Based on service defaults'
    };
}

function analyzeHistoryPatterns(history) {
    if (history.length === 0) return { confidence: 0 };

    const formats = history.map(h => h.format);
    const qualities = history.map(h => h.quality);

    const formatCounts = formats.reduce((acc, f) => {
        acc[f] = (acc[f] || 0) + 1;
        return acc;
    }, {});

    const qualityCounts = qualities.reduce((acc, q) => {
        acc[q] = (acc[q] || 0) + 1;
        return acc;
    }, {});

    const mostCommon = (counts) =>
        Object.entries(counts).sort((a, b) => b[1] - a[1])[0];

    return {
        preferredFormat: mostCommon(formatCounts)?.[0],
        preferredQuality: mostCommon(qualityCounts)?.[0],
        confidence: Math.min(history.length / 10, 0.9),
        reasoning: `Based on ${history.length} previous downloads`
    };
}
```

2. Add content moderation:

```javascript
// api/src/ai/moderation.js
export async function moderateContent(url, metadata) {
    // Simple keyword-based moderation (replace with actual AI service)
    const blockedPatterns = [
        /explicit/i,
        /nsfw/i,
        /illegal/i
    ];

    const title = metadata?.title || '';

    for (const pattern of blockedPatterns) {
        if (pattern.test(title)) {
            return {
                allowed: false,
                reason: 'Content violates terms of service',
                confidence: 0.95
            };
        }
    }

    return { allowed: true };
}
```

3. Add usage analytics with AI insights:

```javascript
// api/src/ai/analytics.js
export class UsageAnalytics {
    constructor(store) {
        this.store = store;
    }

    async trackDownload(userId, service, format, quality, duration) {
        const key = `analytics:${userId}:${Date.now()}`;
        await this.store.set(key, {
            service,
            format,
            quality,
            duration,
            timestamp: Date.now()
        });
    }

    async getInsights(userId, days = 30) {
        const now = Date.now();
        const windowMs = days * 24 * 60 * 60 * 1000;

        // This would typically use Redis aggregation
        // For now, return mock insights
        return {
            totalDownloads: Math.floor(Math.random() * 100),
            favoriteService: 'youtube',
            preferredFormat: 'mp4',
            averageQuality: '1080p',
            peakHours: ['18:00-20:00'],
            trend: 'increasing'
        };
    }
}
```

---

## 4. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

| Task | Topic Covered |
|------|---------------|
| Set up Jest testing framework | Testing |
| Add ESLint and Prettier | Code Quality |
| Create comprehensive documentation | Documentation |
| Add security headers | OWASP |

### Phase 2: Infrastructure (Week 3-4)

| Task | Topic Covered |
|------|---------------|
| Create Terraform/AWS CDK stack | AWS Cloud |
| Set up ECS Fargate deployment | AWS Cloud |
| Configure CI/CD pipeline | CI/CD, Docker |
| Add security scanning | OWASP |

### Phase 3: Advanced Features (Week 5-6)

| Task | Topic Covered |
|------|---------------|
| Implement Prometheus metrics | Prometheus, Grafana |
| Create Grafana dashboards | Prometheus, Grafana |
| Add RBAC system | Auth vs Authorization |
| Implement JWT refresh tokens | JWT |

### Phase 4: Optimization (Week 7-8)

| Task | Topic Covered |
|------|---------------|
| Add profiling tools | Profiling |
| Implement caching strategies | Performance, Database |
| Create cost analysis | Cost Analysis |
| Document architecture | Architecture Patterns |

### Phase 5: AI & Polish (Week 9-10)

| Task | Topic Covered |
|------|---------------|
| Add AI recommendations | AI |
| Implement usage analytics | AI |
| Add API key management | Teamwork |
| Final testing and documentation | All |

---

## 5. Summary of Deliverables

After implementing all recommendations, your project will demonstrate proficiency in all 19 course topics:

1. **Development Process**: ADRs, CONTRIBUTING.md, development workflow
2. **Git**: Conventional commits, branch strategy, Git hooks
3. **Testing**: Unit tests, integration tests, test coverage
4. **Code Quality**: ESLint, JSDoc, comprehensive README
5. **AWS Cloud**: ECS Fargate deployment, Terraform/CDK
6. **CI/CD**: Multi-stage pipeline with security scanning
7. **Performance**: Compression, caching, connection pooling
8. **Profiling**: 0x, clinic.js, custom profiling endpoints
9. **Database**: Redis optimization, connection pooling
10. **Cost Analysis**: Detailed AWS cost estimation
11. **Architecture**: Documented patterns, diagrams
12. **OWASP**: Security headers, input validation, sanitization
13. **Auth vs Authorization**: RBAC, permission system
14. **JWT**: Standard library, refresh tokens
15. **CORS**: Fine-grained configuration
16. **Secret Management**: AWS Secrets Manager integration
17. **Teamwork**: User management, API keys
18. **Prometheus/Grafana**: Metrics, dashboards, alerting
19. **AI**: Recommendations, analytics

This enhancement will transform Cobalt from a functional media downloader into a production-ready, enterprise-grade application that thoroughly demonstrates all required course competencies.
