---
Project: Vooglaadija
Date: March 17, 2026
Status: Final
---

# Cobalt Project Enhancement Proposal for Software Engineering Course

## Executive Summary

This document presents a comprehensive set of enhancements to transform the Cobalt media downloader into an ideal project for a software engineering course. The proposed modifications address all course requirements while preserving the project's innovative nature as a sophisticated media downloading service. The enhancements introduce a PostgreSQL database layer for user management and download history, implement comprehensive monitoring with Prometheus and Grafana, strengthen security through proper authentication and authorization, and extend the CI/CD pipeline with AWS deployment capabilities. These additions convert an already well-architected project into a complete full-stack application that demonstrates enterprise-level software engineering practices suitable for academic evaluation.

The Cobalt project serves as an excellent foundation for this course because it already possesses many characteristics that software engineering programs seek to teach. The existing architecture demonstrates modern web development patterns, service-oriented design, and production-ready deployment strategies. By building upon this foundation, students can focus on learning new concepts rather than recreating basic functionality, maximizing the educational value of the project.

---

## 1. Current Project Assessment

### 1.1 Existing Strengths

The Cobalt project already demonstrates numerous best practices that align remarkably well with software engineering education. The monorepo structure using pnpm workspaces properly separates concerns between the API backend, the web frontend, and shared packages. The existing GitHub Actions workflows handle Docker builds, comprehensive service testing, and CodeQL security analysis. The project includes thorough documentation covering deployment procedures, API usage guidelines, and instance protection strategies. The architecture follows contemporary patterns with Express.js for the API, SvelteKit for the frontend, and a service-oriented design supporting over twenty media platforms.

The current architecture supports clustering through Node.js cluster mode and optional Redis for distributed rate limiting. The security implementation includes JWT tokens, Cloudflare Turnstile integration, and API key management. The Docker deployment utilizes multi-stage builds with proper caching strategies. These existing features provide an excellent foundation upon which to add the additional course-required components without significant restructuring.

### 1.2 Gaps Addressing Course Requirements

While Cobalt excels in many areas, several enhancements are necessary to fully satisfy the course requirements. The most significant gap is the absence of a persistent database for user management and download tracking. Currently, the application operates without user accounts, relying solely on IP-based rate limiting. Adding PostgreSQL enables user authentication, download history persistence, API key storage with fine-grained controls, and analytics capabilities. Additionally, the monitoring infrastructure requires expansion to include Prometheus metrics and Grafana dashboards for demonstrating observability practices essential for production systems. The CI/CD pipeline can be extended to include AWS deployment configurations and more comprehensive testing strategies that cover database interactions and security scenarios.

---

## 2. Proposed Database Architecture

### 2.1 Database Selection and Rationale

PostgreSQL serves as the recommended database solution for this enhanced Cobalt project. The choice of PostgreSQL over alternatives such as MySQL or MongoDB reflects several architectural considerations that align with both current industry practices and educational objectives. PostgreSQL offers robust support for complex queries, JSON data types, and sophisticated indexing strategies that provide excellent learning opportunities for database optimization topics. The relational model suits the data structure of users, downloads, and API keys with clear foreign key relationships and referential integrity. Furthermore, PostgreSQL's widespread adoption in enterprise environments ensures relevant professional experience for students.

The database schema design encompasses four primary entities that capture the application's core functionality while enabling new features for the course project. The users table stores authentication credentials and account preferences with proper password hashing. The downloads table maintains a complete history of media downloads with comprehensive metadata for analytics. The api_keys table provides the existing API key functionality with proper persistent storage and usage tracking. The rate_limits table enables sophisticated rate limiting with per-user historical analysis. This schema provides ample opportunities for demonstrating database optimization through strategic indexing, query planning, and connection pooling.

### 2.2 Database Schema Design

The enhanced database schema introduces several tables that integrate seamlessly with the existing Cobalt architecture while providing new functionality for the course project. The following SQL definition represents the core schema that should be implemented, demonstrating proper table design with constraints, indexes, and data integrity measures:

```sql
-- Users table for authentication and account management
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true,
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Download history for analytics and user features
CREATE TABLE downloads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE SET NULL,
    service VARCHAR(50) NOT NULL,
    url TEXT NOT NULL,
    filename VARCHAR(500),
    format VARCHAR(50),
    file_size BIGINT,
    duration INTEGER,
    status VARCHAR(50) DEFAULT 'completed',
    ip_address INET,
    user_agent TEXT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- API keys for programmatic access with enhanced management
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) NOT NULL,
    name VARCHAR(100),
    rate_limit INTEGER DEFAULT 100,
    allowed_services TEXT[],
    allowed_ips INET[],
    expires_at TIMESTAMP WITH TIME ZONE,
    last_used_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

-- Session tokens for JWT refresh with secure storage
CREATE TABLE refresh_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    user_agent TEXT,
    ip_address INET
);

-- Indexes for query optimization covering common access patterns
CREATE INDEX idx_downloads_user_id ON downloads(user_id);
CREATE INDEX idx_downloads_created_at ON downloads(created_at DESC);
CREATE INDEX idx_downloads_service ON downloads(service);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires ON refresh_tokens(expires_at) WHERE expires_at > CURRENT_TIMESTAMP;
```

### 2.3 Database Connection Management

The API should implement a connection pooling strategy using the node-postgres library with the pg-pool abstraction. Connection pooling reduces database overhead by reusing connections across requests and limits the maximum number of simultaneous connections to prevent database overload. The pool configuration should include minimum and maximum connection limits, connection timeout settings, and idle timeout values. This implementation provides an excellent demonstration of database optimization concepts including connection lifecycle management, query queuing, and resource allocation that are essential for high-traffic applications.

```javascript
import pg from 'pg';
const { Pool } = pg;

const pool = new Pool({
    host: process.env.DB_HOST,
    port: parseInt(process.env.DB_PORT || '5432'),
    database: process.env.DB_NAME,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    max: 20,
    idleTimeoutMillis: 30000,
    connectionTimeoutMillis: 2000,
});

pool.on('error', (err) => {
    console.error('Unexpected database error on idle client:', err);
});

export default pool;
```

---

## 3. Authentication and Authorization Implementation

### 3.1 JWT-Based Authentication System

The enhanced Cobalt project implements a comprehensive JWT-based authentication system that demonstrates the distinction between authentication and authorization, two critical security concepts covered extensively in the course curriculum. Authentication verifies user identity through credentials, while authorization determines what actions an authenticated user can perform. The implementation uses access tokens with short expiration for API requests and refresh tokens with longer expiration for session maintenance, following industry best practices for secure session management.

The authentication flow begins with user login, where credentials are validated against the database and a pair of tokens is issued. Access tokens contain user identity and role information, serving as bearer tokens for API authorization. Refresh tokens enable obtaining new access tokens without re-authentication and are stored in the database for revocation capability. This design demonstrates proper token lifecycle management including issuance, validation, refresh, and revocation, which are essential security skills for modern web development.

```javascript
import jwt from 'jsonwebtoken';
import bcrypt from 'bcrypt';
import pool from '../db/pool.js';

const JWT_ACCESS_SECRET = process.env.JWT_ACCESS_SECRET;
const JWT_REFRESH_SECRET = process.env.JWT_REFRESH_SECRET;
const ACCESS_TOKEN_EXPIRY = '15m';
const REFRESH_TOKEN_EXPIRY = '7d';

export async function login(req, res) {
    const { email, password } = req.body;
    
    const result = await pool.query(
        'SELECT id, email, password_hash, role FROM users WHERE email = $1 AND is_active = true',
        [email]
    );
    
    if (result.rows.length === 0) {
        return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    const user = result.rows[0];
    const validPassword = await bcrypt.compare(password, user.password_hash);
    
    if (!validPassword) {
        return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    const accessToken = jwt.sign(
        { userId: user.id, email: user.email, role: user.role },
        JWT_ACCESS_SECRET,
        { expiresIn: ACCESS_TOKEN_EXPIRY }
    );
    
    const refreshToken = jwt.sign(
        { userId: user.id, type: 'refresh' },
        JWT_REFRESH_SECRET,
        { expiresIn: REFRESH_TOKEN_EXPIRY }
    );
    
    const tokenHash = await bcrypt.hash(refreshToken, 10);
    await pool.query(
        `INSERT INTO refresh_tokens (user_id, token_hash, expires_at, user_agent, ip_address)
         VALUES ($1, $2, NOW() + interval '7 days', $3, $4)`,
        [user.id, tokenHash, req.get('User-Agent'), req.ip]
    );
    
    await pool.query('UPDATE users SET last_login = NOW() WHERE id = $1', [user.id]);
    
    res.json({ 
        accessToken, 
        refreshToken, 
        user: { 
            id: user.id, 
            email: user.email, 
            role: user.role 
        } 
    });
}
```

### 3.2 Authorization Middleware and Role-Based Access Control

Authorization in the enhanced Cobalt project implements role-based access control (RBAC) with three distinct roles demonstrating the authorization concept comprehensively. The administrator role has full access to all endpoints including user management and system configuration. The user role can access personal download history, manage their own API keys, and perform downloads within rate limits. The anonymous role represents unauthenticated users who can only access public endpoints with IP-based rate limiting.

The middleware implementation demonstrates proper separation of concerns between authentication and authorization, a fundamental software architecture principle. Authentication middleware validates JWT tokens and attaches user information to the request object. Authorization middleware checks user roles and permissions before allowing access to protected resources. This pattern illustrates architectural best practices while providing granular access control suitable for various deployment scenarios.

```javascript
export function requireAuth(req, res, next) {
    const authHeader = req.headers.authorization;
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        return res.status(401).json({ error: 'Authentication required' });
    }
    
    const token = authHeader.split(' ')[1];
    
    try {
        const decoded = jwt.verify(token, JWT_ACCESS_SECRET);
        req.user = decoded;
        next();
    } catch (error) {
        return res.status(401).json({ error: 'Invalid or expired token' });
    }
}

export function requireRole(...roles) {
    return (req, res, next) => {
        if (!req.user) {
            return res.status(401).json({ error: 'Authentication required' });
        }
        
        if (!roles.includes(req.user.role)) {
            return res.status(403).json({ error: 'Insufficient permissions' });
        }
        
        next();
    };
}

router.get('/downloads', requireAuth, getUserDownloads);
router.get('/admin/users', requireAuth, requireRole('admin'), listAllUsers);
router.post('/api/keys', requireAuth, createApiKey);
```

### 3.3 Password Security and Hashing

Password security follows OWASP recommendations using bcrypt with appropriate work factors that balance security and performance. The implementation demonstrates proper salt generation, secure hashing algorithms, and timing-attack resistant comparisons through the bcrypt library. This component directly addresses OWASP topics related to password storage and credential management, providing students with practical experience in secure password handling.

---

## 4. Monitoring and Observability Infrastructure

### 4.1 Prometheus Metrics Integration

The enhanced Cobalt project implements comprehensive metrics collection using Prometheus, providing hands-on experience with the Micrometer and Prometheus technologies specified in the course curriculum. Metrics are exposed through a dedicated endpoint that Prometheus scrapes at regular intervals, following the pull model standard in the industry. The implementation covers application metrics, business metrics, and infrastructure metrics, demonstrating the breadth of observability required in production systems.

Application metrics track HTTP request handling including request counts, response times categorized by route and status code, and error rates. Business metrics capture download operations aggregated by service and status, user registrations, and API key usage patterns. Infrastructure metrics monitor database connection pool status, memory usage through Node.js process metrics, and CPU utilization. This comprehensive metrics strategy demonstrates how observability supports both operational monitoring and business analytics, essential skills for production software development.

```javascript
import client from 'prom-client';

const register = new client.Registry();
client.collectDefaultMetrics({ register });

const httpRequestDuration = new client.Histogram({
    name: 'http_request_duration_seconds',
    help: 'Duration of HTTP requests in seconds',
    labelNames: ['method', 'route', 'status_code'],
    buckets: [0.01, 0.05, 0.1, 0.5, 1, 2, 5]
});

const httpRequestTotal = new client.Counter({
    name: 'http_requests_total',
    help: 'Total number of HTTP requests',
    labelNames: ['method', 'route', 'status_code']
});

const downloadsTotal = new client.Counter({
    name: 'cobalt_downloads_total',
    help: 'Total number of downloads',
    labelNames: ['service', 'status', 'user_type']
});

const downloadsDuration = new client.Histogram({
    name: 'cobalt_download_duration_seconds',
    help: 'Duration of download processing',
    labelNames: ['service'],
    buckets: [1, 5, 10, 30, 60, 120, 300]
});

const dbQueryDuration = new client.Histogram({
    name: 'db_query_duration_seconds',
    help: 'Duration of database queries',
    labelNames: ['query_type', 'table'],
    buckets: [0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
});

register.registerMetric(httpRequestDuration);
register.registerMetric(httpRequestTotal);
register.registerMetric(downloadsTotal);
register.registerMetric(downloadsDuration);
register.registerMetric(dbQueryDuration);

app.get('/metrics', async (req, res) => {
    res.set('Content-Type', register.contentType);
    res.end(await register.metrics());
});

export function metricsMiddleware(req, res, next) {
    const start = Date.now();
    
    res.on('finish', () => {
        const duration = (Date.now() - start) / 1000;
        const route = req.route?.path || req.path;
        
        httpRequestDuration.labels(req.method, route, res.statusCode).observe(duration);
        httpRequestTotal.labels(req.method, route, res.statusCode).inc();
    });
    
    next();
}
```

### 4.2 Grafana Dashboard Configuration

Grafana provides visualization of the collected metrics, completing the observability stack as specified in the course requirements. The dashboard configuration includes pre-built panels for key performance indicators, service health status indicators, user activity trends, and system resource utilization graphs. Students gain practical experience with dashboard design, PromQL query optimization, and alerting configuration that are essential for production operations.

```yaml
apiVersion: 1

dashboards:
  - name: Cobalt Overview
    uid: cobalt-overview
    panels:
      - title: "Request Rate"
        type: graph
        targets:
          - expr: sum(rate(http_requests_total[5m])) by (method)
            legendFormat: "{{method}}"
      - title: "Response Time P95"
        type: graph
        targets:
          - expr: histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le))
            legendFormat: "P95"
      - title: "Download Success Rate"
        type: gauge
        targets:
          - expr: sum(rate(cobalt_downloads_total{status="success"}[5m])) / sum(rate(cobalt_downloads_total[5m]))
      - title: "Active Users (24h)"
        type: graph
        targets:
          - expr: count(distinct(user_id)) from downloads where created_at > now() - 24h
      - title: "Database Connection Pool"
        type: stat
        targets:
          - expr: pg_stat_activity_count / pg_settings_max_connections
      - title: "Memory Usage"
        type: graph
        targets:
          - expr: process_resident_memory_bytes{job="cobalt-api"}
            legendFormat: "RSS"
```

### 4.3 Health Check and Readiness Endpoints

Kubernetes-style health checks provide container orchestration compatibility and demonstrate modern deployment patterns for cloud-native applications. The liveness endpoint indicates whether the application is running correctly and should be restarted if failing, which Kubernetes uses to determine container health. The readiness endpoint indicates whether the application can handle requests, including database connectivity, which Kubernetes uses to route traffic to pods. This distinction is crucial for production deployments managing container lifecycle and traffic routing effectively.

```javascript
import pool from '../db/pool.js';

app.get('/health/liveness', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

app.get('/health/readiness', async (req, res) => {
    const checks = {
        database: false,
        redis: false
    };
    
    try {
        await pool.query('SELECT 1');
        checks.database = true;
    } catch (error) {
        console.error('Database health check failed:', error);
    }
    
    if (redisClient && redisClient.isOpen) {
        checks.redis = true;
    }
    
    const allHealthy = Object.values(checks).every(Boolean);
    res.status(allHealthy ? 200 : 503).json({
        status: allHealthy ? 'ok' : 'degraded',
        checks,
        timestamp: new Date().toISOString()
    });
});
```

---

## 5. Enhanced CI/CD Pipeline

### 5.1 GitHub Actions Workflow Enhancements

The enhanced CI/CD pipeline extends the existing GitHub Actions configuration with additional workflows covering comprehensive testing, security scanning, and AWS deployment capabilities. The pipeline demonstrates modern DevOps practices including infrastructure-as-code, automated testing at multiple levels, and progressive deployment strategies suitable for enterprise environments. Each workflow serves specific purposes aligned with development best practices and course requirements for demonstrating continuous integration and delivery competencies.

```yaml
name: CI Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  validate-lockfile:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - name: Verify lockfile
        run: pnpm install --frozen-lockfile

  code-quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 'lts/*'
      - uses: pnpm/action-setup@v4
      - name: Install dependencies
        run: pnpm install --frozen-lockfile
      - name: ESLint
        run: pnpm --prefix web lint
      - name: TypeScript check
        run: pnpm --prefix web check

  unit-tests:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: cobalt_test
          POSTGRES_USER: test
          POSTGRES_PASSWORD: test
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 'lts/*'
      - uses: pnpm/action-setup@v4
      - name: Setup test database
        run: |
          psql -h localhost -U test -d cobalt_test -f api/src/db/schema.sql
        env:
          PGPASSWORD: test
      - name: Run unit tests
        run: pnpm --prefix api run test:unit
        env:
          DB_HOST: localhost
          DB_PORT: 5432
          DB_NAME: cobalt_test
          DB_USER: test
          DB_PASSWORD: test
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage/lcov.info

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v4
      - name: Run service tests
        run: .github/test.sh api
        env:
          API_EXTERNAL_PROXY: ${{ secrets.API_EXTERNAL_PROXY }}

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run dependency audit
        run: pnpm audit --audit-level=high
      - name: Run Snyk
        uses: snyk/actions/node@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      - name: Run trivy
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'
```

### 5.2 AWS Deployment Configuration

The AWS deployment configuration demonstrates cloud management skills through infrastructure-as-code using AWS CDK. The deployment includes an ECS Fargate cluster for the API, S3 with CloudFront for the web application, RDS PostgreSQL for the database, ElastiCache Redis for rate limiting, and Application Load Balancer for traffic distribution. This comprehensive AWS architecture demonstrates scalability, high availability, and cost optimization principles essential for cloud-native development.

```typescript
import * as cdk from 'aws-cdk-lib';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as elasticache from 'aws-cdk-lib/aws-elasticache';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as acm from 'aws-cdk-lib/aws-certificatemanager';

export class CobaltStack extends cdk.Stack {
    constructor(scope: cdk.App, id: string, props?: cdk.StackProps) {
        super(scope, id, props);
        
        const vpc = new cdk.aws_ec2.Vpc(this, 'CobaltVPC', {
            maxAzs: 2,
            natGateways: 1,
        });
        
        const database = new rds.DatabaseInstance(this, 'CobaltDatabase', {
            engine: rds.DatabaseEngine.postgres({ 
                version: rds.PostgresEngineVersion.VER_16 
            }),
            instanceType: cdk.aws_ec2.InstanceType.of(
                cdk.aws_ec2.InstanceClass.T4G,
                cdk.aws_ec2.InstanceSize.MICRO
            ),
            vpc,
            allocatedStorage: 20,
            maxAllocatedStorage: 100,
            backupRetention: cdk.Duration.days(7),
            deletionProtection: true,
        });
        
        const redisSubnetGroup = new elasticache.CfnSubnetGroup(this, 'RedisSubnetGroup', {
            description: 'Redis subnet group',
            subnetIds: vpc.privateSubnets.map(s => s.subnetId),
        });
        
        const redis = new elasticache.CfnReplicationGroup(this, 'CobaltRedis', {
            replicationGroupDescription: 'Cobalt rate limiting cache',
            replicationGroupId: 'cobalt-redis',
            cacheNodeType: 'cache.t4g.micro',
            engine: 'redis',
            numNodeGroups: 1,
            replicasPerNodeGroup: 0,
            cacheSubnetGroupName: redisSubnetGroup.ref,
            atRestEncryptionEnabled: true,
            transitEncryptionEnabled: true,
        });
        
        const cluster = new ecs.Cluster(this, 'CobaltCluster', {
            vpc,
            capacityProviders: ['FARGATE'],
        });
        
        const taskDefinition = new ecs.FargateTaskDefinition(this, 'CobaltTask', {
            memoryLimitMiB: 1024,
            cpu: 512,
        });
        
        taskDefinition.addContainer('cobalt-api', {
            image: ecs.ContainerImage.fromRegistry('ghcr.io/imputnet/cobalt:latest'),
            environment: {
                API_URL: `https://${this.node.tryGetContext('domain')}/`,
                DB_HOST: database.dbInstanceEndpointAddress,
                DB_PORT: database.dbInstanceEndpointPort,
                DB_NAME: 'cobalt',
            },
            secrets: {
                DB_USER: ecs.Secret.fromSecretsManager(database.secret, 'username'),
                DB_PASSWORD: ecs.Secret.fromSecretsManager(database.secret, 'password'),
                JWT_SECRET: ecs.Secret.fromSecretsManager('cobalt-secrets', 'jwt-secret'),
            },
            portMappings: [{ containerPort: 9000 }],
        });
        
        const alb = new cdk.aws_elasticloadbalancingv2.ApplicationLoadBalancer(this, 'CobaltALB', {
            vpc,
            internetFacing: true,
        });
        
        const listener = alb.addListener('HTTPS', {
            port: 443,
            certificates: [acm.Certificate.fromCertificateArn(this, 'Cert', 
                this.node.tryGetContext('certificate-arn'))],
        });
        
        listener.addTargets('CobaltTargets', {
            port: 80,
            targets: [cluster.getService('cobalt-api')],
            healthCheck: {
                path: '/health/readiness',
                interval: cdk.Duration.seconds(30),
            },
        });
        
        const webBucket = new s3.Bucket(this, 'CobaltWeb', {
            encryption: s3.BucketEncryption.S3_MANAGED,
            publicAccessBlock: false,
        });
        
        new cloudfront.Distribution(this, 'CobaltCDN', {
            defaultBehavior: {
                origin: new cloudfront_origins.S3Origin(webBucket),
                viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                compress: true,
            },
            errorResponses: [
                { httpStatus: 404, responsePagePath: '/404.html', responseHttpStatus: 404 },
            ],
        });
    }
}
```

### 5.3 Deployment Pipeline

```yaml
name: Deploy to AWS

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Login to ECR
        uses: aws-actions/amazon-ecr-login@v2
      
      - name: Build and push Docker image
        run: |
          docker build -t $ECR_REGISTRY/cobalt:${{ github.sha }} .
          docker push $ECR_REGISTRY/cobalt:${{ github.sha }}
      
      - name: Deploy to ECS
        uses: aws-actions/amazon-ecs-deploy-task-definition@v1
        with:
          task-definition: task-definition.json
          cluster: cobalt-cluster
          service: cobalt-api
          force-new-deployment: true
      
      - name: Invalidate CloudFront cache
        run: |
          aws cloudfront create-invalidation --distribution-id ${{ secrets.CF_DISTRIBUTION_ID }} --paths "/*"
```

---

## 6. Performance Optimization Strategies

### 6.1 Database Query Optimization

The enhanced Cobalt project demonstrates database optimization through strategic indexing, query analysis, and connection management as required by the course. Indexes are created based on query patterns identified through application logging and performance monitoring tools. The implementation includes composite indexes for complex queries, partial indexes for filtered views, and proper index maintenance procedures. This practical experience with PostgreSQL optimization directly addresses the database optimization course topic while improving application performance.

```sql
CREATE INDEX idx_downloads_user_date 
    ON downloads(user_id, created_at DESC);

CREATE INDEX idx_refresh_tokens_active 
    ON refresh_tokens(user_id) 
    WHERE expires_at > CURRENT_TIMESTAMP;

CREATE INDEX idx_downloads_recent 
    ON downloads(created_at DESC) 
    WHERE created_at > NOW() - INTERVAL '30 days';

EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT service, COUNT(*), SUM(file_size) 
FROM downloads 
WHERE user_id = $1 
AND created_at > NOW() - INTERVAL '30 days'
GROUP BY service;
```

### 6.2 Caching Strategy Implementation

Multiple layers of caching improve application performance and reduce database load as required for demonstrating performance optimization skills. Redis serves as the primary caching layer for frequently accessed data including user sessions, rate limit counters, and service metadata. HTTP caching headers enable browser-level caching for static assets served through the web application. The caching implementation demonstrates cache invalidation strategies, TTL management, and distributed cache patterns that are essential for high-traffic applications.

```javascript
import Redis from 'ioredis';

const redis = new Redis(process.env.REDIS_URL);

async function cacheGet(key) {
    const cached = await redis.get(key);
    return cached ? JSON.parse(cached) : null;
}

async function cacheSet(key, value, ttlSeconds = 300) {
    await redis.setex(key, ttlSeconds, JSON.stringify(value));
}

export async function getServiceMetadata(service) {
    const cacheKey = `service:${service}:metadata`;
    
    let metadata = await cacheGet(cacheKey);
    if (!metadata) {
        metadata = await loadServiceMetadataFromDatabase(service);
        await cacheSet(cacheKey, metadata, 3600);
    }
    
    return metadata;
}

export async function checkRateLimit(userId, limit, window) {
    const key = `ratelimit:${userId}`;
    const current = await redis.incr(key);
    
    if (current === 1) {
        await redis.expire(key, window);
    }
    
    return {
        allowed: current <= limit,
        remaining: Math.max(0, limit - current),
        reset: await redis.ttl(key)
    };
}
```

### 6.3 API Response Optimization

The API implements several optimization strategies including response compression through the compression middleware, pagination for large datasets with configurable page sizes, and field selection for reduced payload sizes when clients only need specific data. These techniques demonstrate practical performance optimization for high-traffic APIs while maintaining functionality and user experience.

```javascript
import compression from 'compression';

app.use(compression());

export async function paginatedQuery(req, res, next) {
    const page = Math.max(1, parseInt(req.query.page) || 1);
    const limit = Math.min(100, Math.max(1, parseInt(req.query.limit) || 20));
    const offset = (page - 1) * limit;
    
    req.pagination = { page, limit, offset };
    next();
}

export function selectFields(fields) {
    return (req, res, next) => {
        const select = req.query.select?.split(',').map(f => f.trim()) || fields;
        req.selectedFields = select;
        next();
    };
}
```

---

## 7. Security Enhancements

### 7.1 OWASP Compliance Implementation

The enhanced Cobalt project addresses OWASP Top 10 vulnerabilities through comprehensive security measures that demonstrate practical security implementation. Input validation using Zod schemas prevents injection attacks by ensuring data conforms to expected types and ranges. Parameterized queries eliminate SQL injection vulnerabilities through proper query construction. Proper error handling prevents information leakage that could aid attackers. Security headers protect against common web attacks including cross-site scripting and clickjacking. The implementation demonstrates practical application of OWASP recommendations in a production-style environment.

```javascript
import { z } from 'zod';

const loginSchema = z.object({
    email: z.string().email().max(255),
    password: z.string().min(8).max(100),
});

const downloadSchema = z.object({
    url: z.string().url().max(2048),
    downloadMode: z.enum(['video', 'audio', 'mute']).default('video'),
    format: z.enum(['mp4', 'mp3', 'webm']).optional(),
    filename: z.string().max(500).optional(),
});

export function validateInput(schema) {
    return (req, res, next) => {
        try {
            req.validated = schema.parse(req.body);
            next();
        } catch (error) {
            if (error instanceof z.ZodError) {
                return res.status(400).json({
                    error: 'Validation failed',
                    details: error.errors
                });
            }
            next(error);
        }
    };
}

import helmet from 'helmet';

app.use(helmet.contentSecurityPolicy({
    directives: {
        defaultSrc: ["'self'"],
        scriptSrc: ["'self'", "'unsafe-inline'"],
        styleSrc: ["'self'", "'unsafe-inline'"],
        imgSrc: ["*", "data:"],
        connectSrc: ["*"],
    },
}));

app.use(helmet.hsts({
    maxAge: 31536000,
    includeSubDomains: true,
}));
```

### 7.2 Secret Management

Secret management demonstrates proper handling of sensitive information using environment variables, secrets managers, and the principle of least privilege as required by the course. The implementation separates configuration from code and ensures secrets are never committed to version control through proper gitignore configuration. The AWS Secrets Manager integration for production deployments provides enterprise-grade secret rotation and comprehensive audit logging capabilities.

```javascript
import 'dotenv/config';

const requiredEnvVars = [
    'API_URL',
    'JWT_ACCESS_SECRET',
    'JWT_REFRESH_SECRET',
    'DB_HOST',
    'DB_NAME',
    'DB_USER',
    'DB_PASSWORD',
];

export function validateEnvironment() {
    const missing = requiredEnvVars.filter(v => !process.env[v]);
    
    if (missing.length > 0) {
        throw new Error(`Missing required environment variables: ${missing.join(', ')}`);
    }
    
    if (process.env.JWT_ACCESS_SECRET?.length < 32) {
        throw new Error('JWT_ACCESS_SECRET must be at least 32 characters');
    }
    
    console.log('Environment validation passed');
}

import { SecretsManagerClient, GetSecretValueCommand } from '@aws-sdk/client-secrets-manager';

export async function loadSecretsFromAWS(secretName) {
    const client = new SecretsManagerClient({ region: process.env.AWS_REGION });
    
    const command = new GetSecretValueCommand({ SecretId: secretName });
    const response = await client.send(command);
    
    return JSON.parse(response.SecretString);
}
```

### 7.3 CORS Configuration

Proper CORS configuration demonstrates understanding of cross-origin request handling and security implications as specified in the course requirements. The implementation supports both wildcard and specific origin configuration while preventing common misconfiguration pitfalls that could lead to security vulnerabilities. The configuration includes proper allowed methods, headers, and credentials settings.

```javascript
import cors from 'cors';

const corsOptions = {
    origin: function (origin, callback) {
        const allowedOrigins = process.env.CORS_ORIGINS?.split(',') || [];
        
        if (!origin || allowedOrigins.includes(origin) || 
            (process.env.CORS_WILDCARD === 'true' && !origin.startsWith('file://'))) {
            callback(null, true);
        } else {
            callback(new Error('Not allowed by CORS'));
        }
    },
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
    exposedHeaders: ['X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset'],
    credentials: true,
    maxAge: 86400,
    preflightContinue: false,
    optionsSuccessStatus: 204
};

app.use(cors(corsOptions));
```

---

## 8. Documentation Enhancements

### 8.1 API Documentation with OpenAPI

The enhanced Cobalt project includes comprehensive OpenAPI (Swagger) documentation that describes all API endpoints, request/response schemas, authentication requirements, and error codes in a machine-readable format. This documentation serves both as developer reference and as a demonstration of API documentation best practices required by the course. The specification enables automatic client SDK generation and interactive API exploration through tools like Swagger UI.

```yaml
openapi: 3.0.3
info:
  title: Cobalt API
  description: Media downloader API with user authentication
  version: 11.5.0
  contact:
    name: Cobalt Support
    url: https://cobalt.tools

servers:
  - url: https://api.cobalt.tools
    description: Production server
  - url: http://localhost:9000
    description: Development server

security:
  - BearerAuth: []
  - ApiKeyAuth: []

paths:
  /auth/login:
    post:
      summary: User login
      tags: [Authentication]
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [email, password]
              properties:
                email:
                  type: string
                  format: email
                password:
                  type: string
                  format: password
      responses:
        '200':
          description: Login successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  accessToken:
                    type: string
                  refreshToken:
                    type: string
                  user:
                    $ref: '#/components/schemas/User'
        '401':
          $ref: '#/components/responses/Unauthorized'

components:
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key
  
  schemas:
    User:
      type: object
      properties:
        id:
          type: string
          format: uuid
        email:
          type: string
          format: email
        role:
          type: string
          enum: [admin, user]
        createdAt:
          type: string
          format: date-time
```

### 8.2 Architecture Documentation

Comprehensive architecture documentation includes system diagrams created with tools like Mermaid or PlantUML, component relationships, data flow descriptions, and deployment topologies. These documents demonstrate technical communication skills essential for professional software development and are particularly important for onboarding new team members and communicating with stakeholders.

```markdown
# Cobalt System Architecture

## Overview

Cobalt is a distributed media downloading service with the following components:

- **Web Application**: Static SvelteKit application deployed to CloudFront/S3
- **API Cluster**: Express.js application running on ECS Fargate
- **Database Layer**: PostgreSQL for persistent storage (users, downloads, keys)
- **Cache Layer**: Redis for caching and rate limiting
- **Blob Storage**: S3 for temporary file storage during processing

## Authentication Flow

1. User submits credentials to `/auth/login`
2. Server validates and returns JWT access + refresh tokens
3. Access token used for subsequent API requests
4. Refresh token enables session extension without re-authentication
5. Tokens validated on each request through middleware
```

---

## 9. Cost Analysis and Optimization

### 9.1 AWS Cost Breakdown

The deployment architecture includes detailed cost analysis demonstrating cloud resource management skills essential for professional software development. Understanding cloud costs is critical for making architecture decisions, and this section provides practical experience with cloud economics and budget management that companies value highly.

```markdown
# Monthly Cost Estimate (US East Region)

## Compute
| Resource | Quantity | Unit Cost | Monthly Cost |
|----------|----------|-----------|--------------|
| ECS Fargate (API) | 2 vCPU, 2GB | $0.04048/vCPU/hr | ~$58 |
| ALB | 1 | $0.0225/LCU/hr | ~$16 |
| CloudFront | 100GB transfer | $0.085/GB | ~$9 |

## Data Storage
| Resource | Quantity | Unit Cost | Monthly Cost |
|----------|----------|-----------|--------------|
| RDS PostgreSQL (t4g.micro) | 20GB | $0.017/GB/hr | ~$12 |
| S3 (web assets) | 1GB | $0.023/GB | ~$1 |
| ElastiCache (t4g.micro) | 1GB | $0.018/GB/hr | ~$13 |

## Additional Services
| Resource | Quantity | Unit Cost | Monthly Cost |
|----------|----------|-----------|--------------|
| Route 53 | 1 hosted zone | $0.50/mo | ~$0.50 |
| ACM Certificate | 1 | Free | $0 |
| Data Transfer | 50GB | ~$0.09/GB | ~$5 |

Total Estimated Monthly Cost: $115-150
```

### 9.2 Cost Optimization Strategies

The implementation includes cost optimization measures that demonstrate efficient resource utilization as required by the course. These strategies include right-sizing compute resources based on actual usage patterns, implementing caching to reduce data transfer costs, using reserved instances for predictable workloads, and implementing auto-scaling to match demand and avoid over-provisioning.

---

## 10. Team Collaboration Features

### 10.1 Git Workflow Implementation

The enhanced Cobalt project implements a structured Git workflow suitable for team development environments as required for demonstrating teamwork skills. The workflow includes feature branches for parallel development, code review requirements through pull requests, and deployment gates that mirror professional development environments. This structure prepares students for real-world development team collaboration.

```markdown
# Git Workflow

## Branch Structure
- main: Production-ready code
- develop: Integration branch for next release
- feature/*: New feature development
- bugfix/*: Bug fixes
- hotfix/*: Urgent production fixes

## Commit Message Convention
<type>(<scope>): <description>

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation
- style: Formatting
- refactor: Code restructuring
- test: Testing
- chore: Maintenance

Example: feat(auth): add password reset functionality

## Pull Request Process
1. Create feature branch from develop
2. Implement changes with passing tests
3. Update documentation if needed
4. Request code review
5. Address feedback
6. Squash and merge to develop
7. Auto-deploy to staging
8. Merge to main for production
```

---

## 11. Implementation Roadmap

### Phase 1: Foundation (Week 1-2)

The first phase establishes the database layer and basic authentication that form the foundation for all subsequent features. Students implement PostgreSQL schema with proper constraints and indexes, connection pooling for efficient resource utilization, user registration and login endpoints with secure password hashing, JWT token management with access and refresh tokens, and basic authorization middleware. This phase directly addresses database, authentication, and JWT course topics with practical implementation experience.

### Phase 2: Core Features (Week 3-4)

The second phase integrates the database with existing functionality and adds user-facing features. Students implement download history storage with comprehensive metadata, API key management with database persistence for revocation capability, enhanced rate limiting with per-user limits and historical tracking, and a user dashboard in the web interface showing download statistics. This phase connects the new data layer with existing services while demonstrating data modeling and integration patterns.

### Phase 3: Observability (Week 5-6)

The third phase implements monitoring and performance optimization as required by the course. Students add Prometheus metrics covering application and business operations, health check endpoints for container orchestration compatibility, Grafana dashboard configuration with practical visualization experience, database query optimization through indexing and query analysis, and API response caching for improved performance. This phase addresses monitoring, profiling, and optimization topics comprehensively.

### Phase 4: Production Readiness (Week 7-8)

The final phase prepares the application for production deployment as would occur in professional environments. Students configure AWS infrastructure with CDK for infrastructure-as-code, implement secret management with AWS Secrets Manager, enhance CI/CD pipelines with security scanning and deployment automation, add comprehensive security hardening measures, and create thorough documentation covering all aspects of the system. This phase addresses AWS, CI/CD, security, and documentation topics while preparing a production-ready deliverable.

---

## 12. Summary of Course Requirements Coverage

The enhanced Cobalt project comprehensively addresses all course requirements through practical implementation that prepares students for professional software development careers:

| Course Topic | Implementation |
|--------------|----------------|
| Front end and back end | SvelteKit web application + Express API backend |
| Database | PostgreSQL with connection pooling and optimization |
| Documentation | OpenAPI specification, architecture docs, deployment guides |
| Not just CRUD | Media downloading, tunnel streaming, service integration |
| Development process | Agile methodology, sprint planning, code review |
| Git | Feature branches, commit conventions, pull request workflow |
| Testing | Unit tests, integration tests, service tests, code coverage |
| Code quality | ESLint, TypeScript strict mode, code review standards |
| AWS cloud management | CDK infrastructure, RDS, ElastiCache, ECS, CloudFront |
| CI/CD, Docker | GitHub Actions, multi-stage builds, deployment pipelines |
| Performance optimization | Caching, compression, pagination, query tuning |
| Profiling | Prometheus metrics with detailed timing histograms |
| Database optimization | Strategic indexes, connection pooling, query analysis |
| Cost analysis | AWS cost breakdown, optimization strategies |
| Software architecture | Microservices patterns, separation of concerns |
| OWASP | Input validation, security headers, secret management |
| Authentication vs authorization | JWT authentication + RBAC authorization |
| JWT | Access tokens with short expiry + refresh tokens |
| CORS | Configurable origin validation with security |
| Secret management | Environment variables, AWS Secrets Manager |
| Teamwork | Git workflow, code review process, pair programming |
| Micrometer, Prometheus, Grafana | Complete observability stack implementation |

This enhanced Cobalt project provides a production-quality foundation for demonstrating comprehensive software engineering competencies while maintaining the innovative nature of the original media downloading service. Students gain practical experience with technologies and practices used in professional software development, making this an ideal course project that balances educational value with technical sophistication.
