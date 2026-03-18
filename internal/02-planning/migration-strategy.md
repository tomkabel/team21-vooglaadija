# Monorepo to Microservices Migration: Comprehensive Guide

## Executive Summary

Migrating from a monorepo to microservices requires careful planning and incremental approaches. The most successful migrations follow a **gradual strangler fig pattern** rather than big-bang rewrites, with estimated success rates of 70-80% vs <20% for big-bang approaches.

---

## 1. LEAST-EFFORT MIGRATION PATTERNS

### 1.1 Strangler Fig Pattern ⭐ **Highest Priority - Lowest Risk**

**Implementation**: Gradually replace monolith functionality by intercepting requests and routing to new microservices.

**How it works**:
1. Identify seams in monolith where services can be extracted
2. Add routing layer (API Gateway, edge service) to intercept requests
3. Build new microservices for specific functionality
4. Incrementally route traffic from monolith to new services
5. Remove legacy code when deprecated

**Node.js/TypeScript Example with pnpm workspaces**:
```
monorepo/
├── packages/
│   ├── legacy-monolith/     # Original monolith
│   ├── api-gateway/         # Strangler gateway
│   ├── user-service/        # First extracted service
│   ├── order-service/       # Second extracted service
│   └── shared/              # Shared utilities
└── pnpm-workspace.yaml
```

**Pros**:
- Zero downtime migration
- Continuous feature delivery maintained
- Early value realization
- Risk mitigation through incremental changes

**Cons**:
- Requires transitional architecture maintenance
- Dual system complexity during transition
- Higher operational overhead initially

**Implementation Effort**: Medium (4-6 weeks for first service)
**Risk Level**: Low

### 1.2 Parallel Run Pattern

**Implementation**: Run both monolith and microservices in parallel, gradually shifting traffic.

**Strategy**:
- Duplicate functionality in both systems
- Use feature flags to control routing
- Compare outputs for correctness validation
- Phase out monolith once confidence established

**Best for**: Critical systems where rollback capability is essential

**Pros**: Complete safety net during migration
**Cons**: 2x development effort initially, complexity in synchronizing state

**Implementation Effort**: High (8-12 weeks)
**Risk Level**: Very Low

### 1.3 Anticorruption Layer

**Implementation**: Create translation layer between monolith and new services to prevent legacy patterns from infecting new code.

**Components**:
- **Translator**: Converts data formats between systems
- **Facade**: Simplifies complex legacy interfaces
- **Adapter**: Bridges protocol differences

**Node.js Example**:
```typescript
// anticorruption-layer/user-adapter.ts
export class UserAdapter {
  async getUserProfile(userId: string): Promise<UserProfile> {
    // Transform legacy response to clean domain model
    const legacyData = await this.legacyClient.getUser(userId);
    return {
      id: legacyData.USER_ID,
      email: legacyData.EMAIL_ADDR,
      name: `${legacyData.FIRST_NM} ${legacyData.LAST_NM}`
    };
  }
}
```

**Pros**: Protects bounded contexts, enables gradual refactoring
**Cons**: Additional layer adds latency, maintenance overhead

**Implementation Effort**: Medium (2-4 weeks per integration point)
**Risk Level**: Low

---

## 2. INCREMENTAL DECOMPOSITION APPROACHES

### 2.1 Step-by-Step Extraction Strategy

**Phase 1 - Preparation (2-4 weeks)**:
- Identify service boundaries using DDD bounded contexts
- Set up monorepo structure with pnpm workspaces
- Create shared packages for common utilities
- Establish CI/CD baseline

**Phase 2 - First Service Extraction (4-6 weeks)**:
1. Choose low-risk, high-value service (e.g., user management, notifications)
2. Extract data models and business logic
3. Implement API contract
4. Set up database (separate from monolith)
5. Implement anticorruption layer for integration
6. Deploy alongside monolith
7. Route read traffic first, then writes

**Phase 3 - Subsequent Services (3-4 weeks each)**:
- Follow lessons learned from first extraction
- Refine patterns and tooling
- Extract services in order of business value and dependency

**Phase 4 - Monolith Decommission (2-4 weeks)**:
- Remove extracted functionality from monolith
- Monitor for remaining dependencies
- Eventually shut down monolith completely

---

## 3. MONOREPO-FIRST STRATEGIES FOR NODE.JS/PNPM

### 3.1 Benefits of Monorepo During Migration

- **Shared Code**: Common utilities, types, configurations
- **Unified Tooling**: Single CI/CD pipeline, consistent linting
- **Dependency Management**: Centralized version control
- **Atomic Changes**: Cross-service refactoring in single PR
- **Gradual Extraction**: Services evolve from monorepo packages

### 3.2 pnpm Workspace Configuration

**pnpm-workspace.yaml**:
```yaml
packages:
  - 'packages/*'
  - 'services/*'
```

**Root package.json**:
```json
{
  "name": "monorepo-root",
  "private": true,
  "scripts": {
    "build": "turbo run build",
    "test": "turbo run test",
    "lint": "turbo run lint"
  },
  "devDependencies": {
    "turbo": "^1.10.0",
    "typescript": "^5.0.0"
  }
}
```

### 3.3 Service Template Pattern

Create a service template package to ensure consistency:

```bash
# Create template
pnpm create @modern-monolith/service-template services/user-service

# Template includes:
# - Standard TypeScript config
# - Express/FastAPI setup
# - Dockerfile template
# - Test setup (Jest, Supertest)
# - CI/CD workflow template
# - Health checks
# - Logging configuration
```

**Pros**: Faster service creation, consistency, reduced boilerplate
**Cons**: Template drift over time requires maintenance

**Implementation Effort**: 1-2 weeks to establish template
**Risk Level**: Very Low

---

## 4. DECOMPOSITION CRITERIA: WHAT TO EXTRACT FIRST

### 4.1 Bounded Contexts from Domain-Driven Design

**Primary Criteria** (rank by priority):

1. **Low Coupling, High Cohesion**: Services with minimal external dependencies
2. **Business Value**: High-impact features delivering immediate ROI
3. **Independent Scaling Needs**: Services with different load patterns
4. **Team Alignment**: Services matching team boundaries (Conway's Law)
5. **Data Ownership**: Services with clear data responsibility

### 4.2 Extraction Priority Matrix

| Criteria | Weight | Score (1-5) | Weighted |
|----------|--------|-------------|----------|
| Coupling | 30% | | |
| Business Value | 25% | | |
| Team Boundaries | 20% | | |
| Data Consistency Needs | 15% | | |
| Technical Complexity | 10% | | |

**Example - E-commerce System**:
1. **User Authentication** (Score: 4.2) - High cohesion, clear boundaries
2. **Product Catalog** (Score: 4.0) - Read-heavy, independent scaling
3. **Order Management** (Score: 3.5) - Medium coupling, high business value
4. **Payment Processing** (Score: 3.2) - External dependencies, security concerns
5. **Inventory Management** (Score: 2.8) - High coupling with orders/catalog

### 4.3 Service Boundary Identification Process

**Step 1 - Dependency Graph Analysis**:
```bash
# Use madge to visualize dependencies
npx madge --image graph.svg packages/legacy-monolith/src/
```

**Step 2 - Business Capability Mapping**:
- List all business capabilities
- Group related capabilities
- Identify natural boundaries

**Step 3 - Data Flow Analysis**:
- Map data ownership
- Identify shared data patterns
- Determine if database per service is feasible

**Step 4 - Team Structure Alignment**:
- Map capabilities to team ownership
- Ensure 2-pizza team size (6-10 people per service)

---

## 5. COMMUNICATION PATTERNS

### 5.1 REST/HTTP - Default Choice ⭐

**When to use**:
- Synchronous request/response patterns
- Simple integration needs
- Browser/client API exposure
- Team familiarity with HTTP

**Node.js Implementation**:
```typescript
// services/user-service/src/controllers/user.controller.ts
import { Request, Response } from 'express';
export class UserController {
  async getUser(req: Request, res: Response) {
    const user = await this.userService.findById(req.params.id);
    res.json(user);
  }
}

// services/order-service/src/services/order.service.ts
import axios from 'axios';
export class OrderService {
  async validateUser(userId: string): Promise<boolean> {
    const response = await axios.get(
      `http://user-service:3000/users/${userId}/status`
    );
    return response.data.isActive;
  }
}
```

**Pros**:
- Ubiquitous, well-understood
- HTTP tooling mature (caching, load balancing)
- Human-readable for debugging

**Cons**:
- Text-based overhead (JSON parsing)
- Connection management overhead
- Tight coupling via synchronous calls
- Cascading failures potential

**Performance**: ~2-10ms overhead per call, 20-40% payload bloat vs binary

### 5.2 gRPC - High Performance ⭐

**When to use**:
- Service-to-service internal communication
- High-throughput, low-latency requirements
- Strongly-typed contracts needed
- Bidirectional streaming required

**Node.js Implementation**:
```protobuf
// shared/protos/user.proto
syntax = "proto3";

service UserService {
  rpc GetUser (GetUserRequest) returns (User);
  rpc ValidateUser (ValidateRequest) returns (ValidationResponse);
}

message GetUserRequest {
  string user_id = 1;
}

message User {
  string id = 1;
  string email = 2;
  string name = 3;
}
```

```typescript
// Generated client usage
const client = new UserServiceClient(
  'user-service:50051',
  grpc.credentials.createInsecure()
);
const user = await client.getUser({ userId: '123' });
```

**Pros**:
- Binary protocol: 30-50% smaller payloads
- 5-10x faster serialization vs JSON
- Code generation for type safety
- Streaming support
- HTTP/2 multiplexing

**Cons**:
- Steeper learning curve
- Limited browser support (requires gRPC-web)
- Debugging less straightforward
- Versioning more complex

**Performance**: ~1-3ms overhead per call, 50-70% payload reduction

### 5.3 Event-Driven Messaging - Decoupled ⭐⭐⭐

**When to use**:
- Asynchronous workflows
- Event sourcing/CQRS patterns
- Decoupling services in time
- Audit trails and replayability
- Fan-out patterns

**Node.js with Kafka Example**:
```typescript
// services/order-service/src/events/order-created.event.ts
export class OrderCreatedEvent {
  readonly orderId: string;
  readonly userId: string;
  readonly total: number;
  readonly occurredAt: Date;
  
  toKafkaMessage(): Record<string, any> {
    return {
      key: this.orderId,
      value: JSON.stringify(this),
      headers: {
        eventType: 'order.created',
        timestamp: this.occurredAt.toISOString()
      }
    };
  }
}

// Event producer
const producer = new KafkaProducer();
await producer.send([
  new OrderCreatedEvent(order).toKafkaMessage()
]);

// Event consumer in another service
const consumer = new KafkaConsumer();
consumer.subscribe(['orders']);
consumer.on('message', async (msg) => {
  const event = JSON.parse(msg.value.toString());
  await handleOrderCreated(event);
});
```

**Message Queue Options**:

| Tool | Best For | Throughput | Ordering Guarantees |
|------|----------|-------------|-------------------|
| RabbitMQ | Traditional queues, AMQP | 10k-50k msg/s | Per-queue ordering |
| Apache Kafka | Event streaming, high throughput | 100k-1M msg/s | Per-partition ordering |
| NATS | Low-latency, simple pub/sub | 10M+ msg/s | Per-subject ordering |
| AWS SQS | Managed, cloud-native | 2k-300k msg/s | Best-effort ordering |

**Pros**:
- Loose temporal coupling
- Improved resilience (buffering)
- Natural event sourcing support
- Better scalability

**Cons**:
- Eventual consistency complexity
- Message ordering challenges
- Debugging distributed flows difficult
- Operational overhead (message brokers)

**Recommendation for Node.js monorepos**: Start with REST, add Kafka for async workflows requiring decoupling.

---

## 6. SHARED CODE MANAGEMENT

### 6.1 The Shared Code Dilemma

**Problem**: DRY vs Service Independence tension

**Anti-pattern**: Creating shared libraries that become distributed monolith
- Services coupled through shared code
- Version conflicts across services
- Deployment coordination required
- Team boundary violations

### 6.2 Three Strategies for Shared Code

#### Strategy A: Monorepo Shared Packages (Recommended ⭐)

**Structure**:
```
packages/
├── shared/
│   ├── utils/           # Pure functions, no business logic
│   ├── types/           # TypeScript interfaces, DTOs
│   ├── logger/          # Logging configuration
│   └── config/          # Configuration schemas
├── services/
│   ├── user-service/
│   ├── order-service/
│   └── product-service/
```

**Implementation**:
```typescript
// packages/shared/types/src/user.types.ts
export interface User {
  id: string;
  email: string;
  name: string;
  createdAt: Date;
}

// packages/shared/logger/src/index.ts
export function createLogger(serviceName: string) {
  return pino({
    name: serviceName,
    level: process.env.LOG_LEVEL || 'info',
    base: { service: serviceName }
  });
}

// Usage in service
import { User, createLogger } from '@monorepo/shared';
const logger = createLogger('user-service');
```

**Pros**:
- Single source of truth
- Easy to update across all services
- Type safety with TypeScript path mapping
- Consistent implementation

**Cons**:
- Services must be in same repo or vendored
- Version coupling - all services share same version
- Risk of business logic leakage

**Rule**: Only share utilities, types, and infrastructure code. Never share business logic.

#### Strategy B: Internal Package Registry (NPM)

**When monorepo not feasible**:
- Services in different repositories
- Different team ownership
- Varying release cadences

**Implementation**:
```json
// packages/auth-utils/package.json
{
  "name": "@company/auth-utils",
  "version": "1.2.0",
  "publishConfig": {
    "registry": "https://npm.internal.company.com"
  }
}
```

**Pros**: Independent versioning, cross-repo sharing
**Cons**: Network dependency, version proliferation, coordination overhead

**Implementation Effort**: 1-2 weeks setup
**Risk Level**: Medium

#### Strategy C: Copy-and-Paste with Automated Sync

**For truly independent services**:
- Initial copy of shared code
- Periodic sync via script
- Services evolve independently

**Tool**: `copycat` or custom script

**Pros**: Complete independence
**Cons**: Code divergence, manual sync effort

**Recommendation**: Use Strategy A for monorepo, Strategy B for multi-repo setups.

---

## 7. DATABASE PATTERNS

### 7.1 Database Per Service Pattern ⭐⭐⭐ **Recommended**

**Architecture**:
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  User       │    │  Order      │    │  Product    │
│  Service    │    │  Service    │    │  Service    │
├─────────────┤    ├─────────────┤    ├─────────────┤
│  PostgreSQL │    │  MongoDB    │    │  PostgreSQL │
│  (users_db) │    │  (orders)   │    │  (products) │
└─────────────┘    └─────────────┘    └─────────────┘
```

**Implementation Steps**:

1. **Initial Setup**:
```typescript
// services/user-service/src/infrastructure/database.ts
import { Pool } from 'pg';

const pool = new Pool({
  host: process.env.DB_HOST,
  database: process.env.DB_NAME || 'users_service',
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
});

export { pool };
```

2. **Data Duplication Strategy**:
- Each service owns its data completely
- Duplicate reference data across services (read-replica pattern)
- Use events to propagate changes

```typescript
// User service publishes user updates
await kafkaProducer.send([
  {
    key: user.id,
    value: JSON.stringify({
      eventType: 'user.updated',
      userId: user.id,
      email: user.email,
      name: user.name
    })
  }
]);

// Order service subscribes and maintains local copy
consumer.on('user.updated', async (event) => {
  await orderRepository.updateUserReference(event);
});
```

**Pros**:
- Full service autonomy
- Independent scaling, technology choice
- Fault isolation
- Schema evolution without coordination

**Cons**:
- Data consistency challenges (eventual consistency)
- Duplicate data storage
- Cross-service queries require API composition or CQRS

**Implementation Effort**: 2-4 weeks per service
**Risk Level**: Medium

### 7.2 Shared Database Pattern (Anti-pattern ⚠️)

**Only consider for**:
- Legacy systems with tight coupling impossible to break
- Short-term migration bridge (<6 months)
- Very small teams (<3 developers)

**Issues**:
- Database becomes single point of failure
- Schema changes require coordination
- Breaks service autonomy
- Vendor lock-in to single database technology

**Recommendation**: Use shared database **only** as temporary bridge during migration, plan to split within 6-12 months.

---

## 8. CONFIGURATION & ENVIRONMENT MANAGEMENT

### 8.1 Configuration Hierarchy

```
Application
├── Environment (dev/staging/prod)
├── Service (user-service, order-service)
├── Instance (instance-specific overrides)
└── Secrets (database passwords, API keys)
```

### 8.2 Configuration Management Options

#### Option A: Environment Variables (Simple ⭐)

**Implementation**:
```typescript
// config/index.ts
export const config = {
  database: {
    host: process.env.DB_HOST || 'localhost',
    port: parseInt(process.env.DB_PORT || '5432'),
    name: process.env.DB_NAME || 'service_db'
  },
  kafka: {
    brokers: process.env.KAFKA_BROKERS?.split(',') || ['localhost:9092']
  },
  service: {
    port: parseInt(process.env.PORT || '3000'),
    environment: process.env.NODE_ENV || 'development'
  }
};
```

**Helmet/Docker Compose**:
```yaml
# docker-compose.yml
services:
  user-service:
    image: user-service:latest
    environment:
      - DB_HOST=postgres
      - DB_PORT=5432
      - KAFKA_BROKERS=kafka:9092
      - NODE_ENV=production
```

**Pros**: Simple, standard 12-factor app approach
**Cons**: No versioning, difficult to manage at scale, all-or-nothing

#### Option B: ConfigMaps & Secrets (Kubernetes ⭐)

```yaml
# kubernetes/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: user-service-config
data:
  NODE_ENV: "production"
  DB_HOST: "postgres.production.svc.cluster.local"
  LOG_LEVEL: "info"
---
apiVersion: v1
kind: Secret
metadata:
  name: user-service-secrets
type: Opaque
stringData:
  DB_PASSWORD: "super-secret-password"
  JWT_SECRET: "jwt-secret-key"
```

```yaml
# kubernetes/deployment.yaml
spec:
  containers:
  - name: user-service
    image: user-service:1.0.0
    envFrom:
    - configMapRef:
        name: user-service-config
    - secretRef:
        name: user-service-secrets
```

**Pros**: Kubernetes-native, versioned, secret management
**Cons**: Kubernetes lock-in, YAML overhead

#### Option C: External Configuration Store

**Tools**:
- **HashiCorp Consul**: KV store with health checking
- **etcd**: Distributed key-value store
- **AWS Parameter Store / Azure Key Vault**: Cloud-native
- **Spring Cloud Config** (Java, less relevant for Node.js)

**Implementation with Consul**:
```typescript
import { Consul } from 'consul';
const consul = new Consul({ host: 'consul-server' });

async function loadConfig() {
  const { Value } = await consul.kv.get('services/user-service/config');
  return JSON.parse(Value);
}
```

**Pros**: Centralized management, dynamic updates, audit trails
**Cons**: Network dependency, additional infrastructure

#### Option D: GitOps Configuration (Advanced ⭐⭐⭐)

**Store configs in Git repository**:
```
config/
├── services/
│   ├── user-service/
│   │   ├── config.yaml
│   │   └── secrets.enc.yaml  # Encrypted with SOPS/Mozilla
│   └── order-service/
└── environments/
    ├── dev/
    ├── staging/
    └── production/
```

**Tools**:
- **FluxCD / ArgoCD**: Automatically syncs Git to cluster
- **SOPS**: Encrypt secrets in Git
- **Helm/Kustomize**: Templating and overlays

**Implementation**:
```yaml
# Helm values/user-service/values.yaml
replicaCount: 3
image:
  repository: user-service
  tag: "1.2.0"
database:
  host: "{{ .Values.global.dbHost }}"
  name: "users_db"
```

```bash
# FluxCD syncs automatically when Git changes
flux reconcile source git flux-system
```

**Pros**: Versioned, auditable, declarative, Git workflow
**Cons**: Requires GitOps tooling, learning curve

**Recommendation for Node.js/PNPM**:
- **Local/Dev**: Environment variables with `.env.local` (git-ignored)
- **Staging/Prod**: Kubernetes ConfigMaps/Secrets + GitOps for version control
- **Multi-cluster**: Consider Consul or cloud provider config service

**Implementation Effort**:
- Env vars: 1 day
- K8s ConfigMaps: 1 week
- GitOps: 2-3 weeks

---

## 9. TESTING STRATEGIES FOR DISTRIBUTED SYSTEMS

### 9.1 Testing Pyramid for Microservices

```
           E2E Tests (5%)
          /            \
    Integration Tests (20%)
     /                 \
Unit Tests + Contract Tests (75%)
```

### 9.2 Contract Testing ⭐⭐⭐ **Critical for Microservices**

**Problem**: Traditional integration tests become brittle and slow with many services.

**Solution**: Consumer-Driven Contract Testing (CDCT)

**Tooling**:
- **Pact**: Most popular, language-agnostic
- **Spring Cloud Contract**: Java ecosystem
- **OpenAPI Validator**: REST API contract validation

#### Pact Implementation (Node.js)

**Consumer Side**:
```typescript
// services/order-service/tests/contracts/user-service.pact.ts
import { Pact } from '@pact-foundation/pact';
import path from 'path';

const provider = new Pact({
  consumer: 'OrderService',
  provider: 'UserService',
  port: 9999,
  log: path.resolve(process.cwd(), 'logs', 'pact.log'),
  dir: path.resolve(process.cwd(), 'pacts'),
});

describe('Order Service - User Service Contract', () => {
  before(() => {
    return provider.setup();
  });

  after(() => {
    return provider.finalize();
  });

  it('validates user exists', async () => {
    await provider.addInteraction({
      state: 'user 123 exists',
      uponReceiving: 'a request to validate user 123',
      withRequest: {
        method: 'GET',
        path: '/users/123/validate',
      },
      willRespondWith: {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: {
          isValid: true,
          userId: '123'
        }
      }
    });

    // Execute actual request to mock server
    const response = await axios.get(
      `http://localhost:9999/users/123/validate`
    );
    expect(response.status).toEqual(200);
  });
});
```

**Provider Side**:
```typescript
// services/user-service/tests/contract/verify-pact.ts
import { Verifier } from '@pact-foundation/pact';
import path from 'path';

const opts = {
  providerBaseUrl: 'http://localhost:3000',
  pactUrls: [path.resolve(process.cwd(), '../order-service/pacts/orderservice-userservice.json')],
  providerStatesSetupUrl: 'http://localhost:3000/_pact/provider-states',
};

new Verifier(opts)
  .verifyProvider()
  .then(() => console.log('✅ Pact verification passed'))
  .catch(() => process.exit(1));
```

**Workflow**:
1. Consumer test creates contract (Pact file) during CI
2. Pact file shared with provider (artifact repository or Git)
3. Provider verifies contract in their CI
4. Breaking changes caught before deployment

**Benefits**:
- Tests interactions, not implementation
- Enables independent deployment
- Catches breaking changes early
- Contracts serve as documentation

**Implementation Effort**: 2-3 weeks per service pair
**Risk Level**: Low

### 9.3 Integration Testing

**Service Integration with Testcontainers**:
```typescript
import { GenericContainer } from 'testcontainers';

describe('OrderService Integration', () => {
  let postgresContainer: StartedTestContainer;
  let kafkaContainer: StartedTestContainer;
  
  beforeAll(async () => {
    postgresContainer = await new GenericContainer('postgres:15')
      .withEnv('POSTGRES_PASSWORD', 'test')
      .withEnv('POSTGRES_DB', 'orders_test')
      .withExposedPorts(5432)
      .start();
    
    kafkaContainer = await new GenericContainer('confluentinc/cp-kafka:latest')
      .withExposedPorts(9092)
      .start();
  });
  
  it('should create order and publish event', async () => {
    const orderService = new OrderService({
      database: {
        host: postgresContainer.getHost(),
        port: postgresContainer.getMappedPort(5432)
      },
      kafka: {
        brokers: [`${kafkaContainer.getHost()}:${kafkaContainer.getMappedPort(9092)}`]
      }
    });
    
    const order = await orderService.createOrder({
      userId: '123',
      items: [{ productId: 'p1', quantity: 2 }]
    });
    
    expect(order.status).toBe('PENDING');
    
    // Verify event published
    const event = await kafkaConsumer.poll('orders', order.id);
    expect(event.type).toBe('order.created');
  });
});
```

**Pros**: Real dependencies, high confidence
**Cons**: Slower (30-60s per test), infrastructure required

**Strategy**: Run contract tests on every PR, integration tests on staging environment.

### 9.4 Unit Testing

**Standard Jest setup**:
```typescript
import { UserService } from './user.service';
import { UserRepository } from './user.repository';

describe('UserService', () => {
  let service: UserService;
  let mockRepo: jest.Mocked<UserRepository>;
  
  beforeEach(() => {
    mockRepo = {
      findById: jest.fn(),
      create: jest.fn()
    };
    service = new UserService(mockRepo);
  });
  
  it('should find user by id', async () => {
    mockRepo.findById.mockResolvedValue({
      id: '123',
      email: 'test@example.com'
    });
    
    const user = await service.getUser('123');
    expect(user.email).toBe('test@example.com');
    expect(mockRepo.findById).toHaveBeenCalledWith('123');
  });
});
```

**Coverage Target**: 80% unit, 60% integration, 40% contract

---

## 10. CI/CD PIPELINE CHANGES

### 10.1 Pipeline Architecture

**Multi-stage Pipeline per Service**:
```yaml
# .github/workflows/ci-cd.yml (or .gitlab-ci.yml)
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
    paths:
      - 'services/user-service/**'
      - 'packages/shared/**'
  pull_request:
    branches: [main]
    paths:
      - 'services/user-service/**'
      - 'packages/shared/**'

jobs:
  # 1. Unit Tests (on every commit)
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: pnpm/action-setup@v2
      - run: pnpm install --frozen-lockfile
      - run: pnpm --filter user-service test
      - run: pnpm --filter user-service test:cov
      - run: pnpm --filter user-service lint
      
  # 2. Build Docker image
  build:
    needs: test
    runs-on: ubuntu-latest
    outputs:
      image: ${{ steps.build.outputs.image }}
    steps:
      - uses: actions/checkout@v3
      - uses: pnpm/action-setup@v2
      - run: pnpm --filter user-service build
      - id: build
        run: |
          IMAGE="user-service:${{ github.sha }}"
          echo "image=$IMAGE" >> $GITHUB_OUTPUT
      - name: Build Docker image
        run: docker build -t ${{ steps.build.outputs.image }} -f services/user-service/Dockerfile .
      - name: Push to registry
        if: github.ref == 'refs/heads/main'
        run: |
          echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
          docker push ${{ steps.build.outputs.image }}

  # 3. Deploy to staging (on main branch)
  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Deploy to staging
        run: |
          kubectl set image deployment/user-service \
            user-service=${{ needs.build.outputs.image }} \
            -n staging
          kubectl rollout status deployment/user-service -n staging

  # 4. Integration & Contract Tests on staging
  integration-test:
    needs: deploy-staging
    runs-on: ubuntu-latest
    steps:
      - run: pnpm --filter user-service test:integration
      - run: pnpm --filter user-service test:contract:provider
      - run: pnpm --filter=order-service test:contract:consumer

  # 5. Manual approval for production
  deploy-prod:
    needs: integration-test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v3
      - name: Wait for manual approval
        uses: peter-evans/slash-command-dispatch@v2
        with:
          token: ${{ secrets.PERSONAL_TOKEN }}
          reaction: '+1'
      - name: Deploy to production
        run: |
          kubectl set image deployment/user-service \
            user-service=${{ needs.build.outputs.image }} \
            -n production
          kubectl rollout status deployment/user-service -n production
```

### 10.2 GitOps Approach (Modern ⭐⭐⭐)

**Tools**:
- **FluxCD** or **ArgoCD**: GitOps operators
- **Helm** or **Kustomize**: Templating
- **Renovate**/**Dependabot**: Automated dependency updates

**Git Repository Structure**:
```
gitops-repo/
├── clusters/
│   ├── staging/
│   │   ├── apps/
│   │   │   ├── user-service.yaml
│   │   │   └── order-service.yaml
│   │   └── namespaces/
│   └── production/
└── flux/
    └── gotk-components.yaml  # FluxCD installation
```

**Service Manifest (FluxCD)**:
```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1beta2
kind: Kustomization
metadata:
  name: user-service
  namespace: flux-system
spec:
  interval: 5m
  path: ./services/user-service/overlays/staging
  prune: true
  sourceRef:
    kind: GitRepository
    name: apps-repo
  targetNamespace: user-service
```

**Benefits**:
- Declarative infrastructure
- Git as source of truth
- Automated drift detection and reconciliation
- Audit trail via Git history

**Implementation Effort**: 2-3 weeks setup
**Risk Level**: Low

**Recommendation**: Start with CI/CD pipelines, migrate to GitOps once stable.

---

## 11. CONTAINER ORCHESTRATION

### 11.1 Docker Compose vs Kubernetes

| Aspect | Docker Compose | Kubernetes |
|--------|---------------|------------|
| **Scale** | Single host | Multi-node cluster |
| **Learning Curve** | Easy (hours) | Hard (weeks) |
| **Production Ready** | Dev/Test only | Yes |
| **Self-healing** | No | Yes |
| **Auto-scaling** | Manual only | Horizontal/Vertical |
| **Service Discovery** | DNS (basic) | DNS + K8s Service |
| **Secrets Management** | Env vars/.env | Secrets objects + Vault |
| **Rolling Updates** | Manual | Built-in |
| **Load Balancing** | Basic round-robin | L4/L7 with Ingress |
| **Monitoring** | Simple | Rich ecosystem |
| **Cost** | $0 (local) | $ (cloud/cluster) |

### 11.2 Development Workflow: Docker Compose

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: users_dev
      POSTGRES_PASSWORD: devpassword
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/data
  
  kafka:
    image: confluentinc/cp-kafka:latest
    ports:
      - "9092:9092"
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
    depends_on:
      - zookeeper
  
  user-service:
    build:
      context: ./services/user-service
      dockerfile: Dockerfile.dev
    ports:
      - "3001:3000"
    environment:
      DB_HOST: postgres
      DB_NAME: users_dev
      KAFKA_BROKERS: kafka:9092
    volumes:
      - ./services/user-service:/app
      - /app/node_modules
    depends_on:
      - postgres
      - kafka
  
  order-service:
    build: ./services/order-service
    ports:
      - "3002:3000"
    environment:
      DB_HOST: postgres
      KAFKA_BROKERS: kafka:9092
    depends_on:
      - postgres
      - kafka

volumes:
  postgres_data:
```

**Usage**:
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f user-service

# Stop services
docker-compose down
```

**Pros**: Fast setup, local development, low overhead
**Cons**: No production features, single host only

**Implementation Effort**: 1-2 days
**Risk Level**: Very Low

### 11.3 Production: Kubernetes

**Minikube/kind for Local Testing**:
```bash
# Install kind (Kubernetes in Docker)
kind create cluster --name dev

# Load Docker images into kind cluster
kind load docker-image user-service:latest --name dev

# Apply manifests
kubectl apply -f k8s/manifests/
```

**Production Kubernetes Setup**:

1. **Managed Kubernetes** (recommended):
   - AWS EKS, Azure AKS, Google GKE
   - Reduces operational overhead

2. **Self-hosted**:
   - More control, higher operational cost

**Service Deployment Manifest**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
      - name: user-service
        image: user-service:1.2.0
        ports:
        - containerPort: 3000
        envFrom:
        - configMapRef:
            name: user-service-config
        - secretRef:
            name: user-service-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 10
          periodSeconds: 5
        livenessProbe:
          httpGet:
            path: /health/live
            port: 3000
          initialDelaySeconds: 30
          periodSeconds: 10

---
apiVersion: v1
kind: Service
metadata:
  name: user-service
spec:
  selector:
    app: user-service
  ports:
  - port: 80
    targetPort: 3000
  type: ClusterIP

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: user-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: user-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Pros**: Production-grade features, scalability, ecosystem
**Cons**: Complex, operational overhead

**Recommendation**:
- **Development**: Docker Compose
- **Staging**: Minikube/kind or managed K8s
- **Production**: Managed Kubernetes (EKS/AKS/GKE)

**Implementation Effort**:
- Docker Compose: 1-2 days
- Staging K8s: 1-2 weeks
- Production K8s: 4-6 weeks (including learning)

**Risk Level**:
- Docker Compose: Very Low
- Kubernetes: Medium (due to complexity)

---

## 12. SERVICE DISCOVERY

### 12.1 Patterns

**Client-Side Discovery**:
- Services maintain registry of instances
- Client queries registry directly
- Load balancing logic in client

**Service-Side Discovery (Kubernetes Default)**:
- Client requests to DNS name
- K8s Service load balances to pods
- Simpler client implementation

### 12.2 Tool Options

| Tool | Type | Best For | Complexity |
|------|------|----------|------------|
| **Kubernetes DNS** | Built-in | Single cluster | Low |
| **Eureka** | Client-side | Spring Cloud | Medium |
| **Consul** | Hybrid | Multi-cluster, hybrid | High |
| **AWS Cloud Map** | Managed | AWS environments | Medium |

### 12.3 Kubernetes Native (Recommended for Single Cluster ⭐⭐)

**No additional setup needed**:

```typescript
// Service-to-service call using K8s DNS
const response = await axios.get(
  'http://user-service.default.svc.cluster.local:3000/users/123'
);
// Or just service name within same namespace
const response = await axios.get('http://user-service:3000/users/123');
```

**K8s Service Definition**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: user-service
  namespace: default
spec:
  selector:
    app: user-service
  ports:
  - port: 80
    targetPort: 3000
    protocol: TCP
  type: ClusterIP  # Internal-only
```

**Benefits**: Zero additional infrastructure, automatic DNS, health checking
**Limitations**: Cluster-bound only

**Implementation Effort**: 0 (built-in)
**Risk Level**: Very Low

### 12.4 Consul (Multi-Cluster/Hybrid ⭐⭐)

**Setup**:
```bash
# Install Consul on K8s
helm repo add hashicorp https://helm.releases.hashicorp.com
helm install consul hashicorp/consul \
  --namespace consul \
  --create-namespace \
  --set global.name=consul
```

**Consul Service Registration**:
```typescript
import { Consul } from 'consul';

const consul = new Consul({
  host: process.env.CONSUL_HOST,
  port: parseInt(process.env.CONSUL_PORT || '8500')
});

// Register service
await consul.agent.service.register({
  name: 'user-service',
  address: 'user-service.default.svc.cluster.local',
  port: 3000,
  check: {
    http: 'http://localhost:3000/health',
    interval: '10s'
  }
});

// Discover services
const services = await consul.catalog.service.nodes('user-service');
const instances = services.map(node => ({
  address: node.Address,
  port: node.ServicePort
}));
```

**Pros**: Multi-datacenter, health checks, KV store, service mesh
**Cons**: Additional infrastructure, complex

**Use when**: Need multi-cluster service discovery, hybrid cloud/VMs

---

## 13. MONITORING & OBSERVABILITY

### 13.1 Three Pillars of Observability

1. **Logs**: Timestamped records of events
2. **Metrics**: Numeric measurements (counters, gauges, histograms)
3. **Traces**: distributed request tracking

### 13.2 Logging Strategy

**Structured Logging with Pino (Node.js)**:
```typescript
// packages/logger/src/index.ts
import pino from 'pino';

export function createLogger(serviceName: string) {
  return pino({
    name: serviceName,
    level: process.env.LOG_LEVEL || 'info',
    base: {
      service: serviceName,
      environment: process.env.NODE_ENV || 'production',
      timestamp: pino.stdTimeFunctions.isoTime
    },
    formatters: {
      level (label, level) {
        return { level };
      }
    },
    timestamp: pino.stdTimeFunctions.isoTime,
    transport: {
      target: 'pino-pretty'
    }
  });
}

// Usage in service
const logger = createLogger('user-service');
logger.info('User created', { userId: user.id, email: user.email });
logger.error('Database connection failed', { error: err.message });
```

**JSON Logs for Production**:
```bash
# Log output
{"level":30,"time":"2024-01-15T10:30:00.123Z","service":"user-service","msg":"User created","userId":"123"}
```

**Log Aggregation**:
- **Fluentd/Fluent Bit**: Collect and forward logs
- **Loki**: Lightweight log aggregation (Grafana Labs)
- **ELK Stack**: Full-featured but heavy
- **Datadog/Splunk**: Commercial solutions

**Implementation (Loki + Promtail)**:
```yaml
# promtail-config.yaml
scrape_configs:
- job_name: user-service
  kubernetes_sd_configs:
  - role: pod
  relabel_configs:
  - source_labels: [__meta_kubernetes_pod_label_app]
    action: keep
    regex: user-service
  pipeline_stages:
  - json:
      expressions:
        message: msg
  - labels:
      service:
```

### 13.3 Metrics with Prometheus

**Prometheus Client**:
```typescript
import client from 'prom-client';

// Create custom metrics
const httpRequestDurationMicroseconds = new client.Histogram({
  name: 'http_request_duration_seconds',
  help: 'Duration of HTTP requests in seconds',
  labelNames: ['method', 'route', 'status_code'],
  buckets: [0.1, 0.5, 1, 1.5, 2, 5]
});

const requestsTotal = new client.Counter({
  name: 'http_requests_total',
  help: 'Total number of HTTP requests',
  labelNames: ['method', 'route', 'status_code']
});

// Middleware to record metrics
app.use((req, res, next) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = (Date.now() - start) / 1000;
    const route = req.route?.path || req.path;
    
    httpRequestDurationMicroseconds
      .labels(req.method, route, res.statusCode.toString())
      .observe(duration);
    
    requestsTotal
      .labels(req.method, route, res.statusCode.toString())
      .inc();
  });
  
  next();
});

// Expose metrics endpoint
app.get('/metrics', async (req, res) => {
  res.set('Content-Type', client.register.contentType);
  res.end(await client.register.metrics());
});
```

**Prometheus scrape config**:
```yaml
# prometheus-config.yaml
scrape_configs:
  - job_name: 'user-service'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: user-service
    metrics_path: /metrics
    scheme: http
```

**Grafana Dashboard**:
- Create dashboards for:
  - Request rate, error rate, duration (RED)
  - Resource utilization (CPU, memory)
  - Business metrics (orders per second, user registrations)

### 13.4 Distributed Tracing with OpenTelemetry ⭐⭐⭐

**Why critical**: Understand request flow across services, identify bottlenecks.

**OpenTelemetry Setup**:
```typescript
import { diag, DiagConsoleLogger, DiagLogLevel } from '@opentelemetry/api';
import { Resource } from '@opentelemetry/resources';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';
import { NodeSDK } from '@opentelemetry/sdk-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-otlp-grpc';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';

// Diagnostics
diag.setLogger(new DiagConsoleLogger(), DiagLogLevel.ERROR);

// Resource with service info
const resource = new Resource({
  [SemanticResourceAttributes.SERVICE_NAME]: 'user-service',
  [SemanticResourceAttributes.SERVICE_VERSION]: '1.2.0',
});

// Trace provider
const provider = new NodeTracerProvider({
  resource,
});

// OTLP exporter to collector
const exporter = new OTLPTraceExporter({
  url: 'http://otel-collector:4317',
});

provider.addSpanProcessor(new SimpleSpanProcessor(exporter));
provider.register();

// Auto-instrument HTTP requests
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
const sdk = new NodeSDK({
  resource,
  instrumentations: [getNodeAutoInstrumentations()],
});
sdk.start();
```

**Jaeger/Zipkin Visualization**:
```
# Jaeger UI
http://jaeger-ui:16686

# Search by:
# - Trace ID
# - Service name
# - Operation name
# - Time range
```

**Benefits**:
- Trace requests across service boundaries
- Identify slow services
- Debug distributed issues

**Implementation Effort**: 2-3 days per service
**Risk Level**: Low

**Recommended Stack**:
- **Collection**: OpenTelemetry Collector
- **Storage**: Jaeger (traces), Prometheus (metrics), Loki (logs)
- **Visualization**: Grafana
- **Alerting**: Prometheus Alertmanager

---

## 14. DATA CONSISTENCY PATTERNS: SAGAS & EVENTUAL CONSISTENCY

### 14.1 The Distributed Transaction Problem

In microservices with database-per-service, ACID transactions spanning services are impossible. Need alternative patterns.

### 14.2 Saga Pattern ⭐⭐⭐ **Critical Pattern**

**Definition**: Sequence of local transactions with compensating actions for rollback.

**Two Coordination Styles**:

#### Choreography-Based Saga

**Services communicate via events**:
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Order     │───>│  Customer   │───>│   Stock     │
│   Service   │<───│   Service   │<───│   Service   │
└─────────────┘    └─────────────┘    └─────────────┘
      │                    │                    │
      │ OrderCreated       │ CreditReserved     │ StockReserved
      │◄───────────────────│◄───────────────────│
```

**Node.js Implementation**:
```typescript
// services/order-service/src/sagas/create-order.saga.ts
export class CreateOrderSaga {
  async execute(orderData: CreateOrderDto): Promise<OrderResult> {
    try {
      // 1. Create order (local transaction)
      const order = await this.orderRepository.create({
        ...orderData,
        status: 'PENDING'
      });
      
      // 2. Publish event
      await this.eventPublisher.publish('order.created', {
        orderId: order.id,
        userId: order.userId,
        total: order.total
      });
      
      // 3. Listen for credit reservation result
      const creditResult = await this.waitForCreditResult(order.id);
      if (!creditResult.approved) {
        throw new Error('Credit not approved');
      }
      
      // 4. Update order status
      await this.orderRepository.update(order.id, { status: 'CONFIRMED' });
      
      return { success: true, order };
      
    } catch (error) {
      // Compensating transaction
      await this.compensate(order.id);
      throw error;
    }
  }
  
  async compensate(orderId: string): Promise<void> {
    await this.orderRepository.update(orderId, { status: 'CANCELLED' });
    await this.eventPublisher.publish('order.cancelled', { orderId });
  }
}

// Event handlers
this.eventSubscriber.subscribe('credit.reserved', async (event) => {
  const { orderId, approved } = event;
  if (approved) {
    await this.orderRepository.update(orderId, { status: 'AWAITING_STOCK' });
    await this.eventPublisher.publish('order.awaiting_stock', { orderId });
  } else {
    await this.sagaCompensation.compensate(orderId);
  }
});
```

#### Orchestration-Based Saga

**Central orchestrator manages saga**:
```typescript
// services/saga-orchestrator/src/orchestrators/create-order.orchestrator.ts
export class CreateOrderOrchestrator {
  async orchestrate(orderId: string): Promise<void> {
    try {
      // Step 1: Create order
      await this.orderService.createOrder(orderId);
      
      // Step 2: Reserve credit
      const creditResult = await this.customerService.reserveCredit(
        orderId, 
        this.getOrderTotal(orderId)
      );
      if (!creditResult.approved) {
        throw new Error('Credit not approved');
      }
      
      // Step 3: Reserve stock
      await this.inventoryService.reserveStock(orderId);
      
      // Step 4: Confirm order
      await this.orderService.confirmOrder(orderId);
      
    } catch (error) {
      // Orchestrator triggers compensation
      await this.compensate(orderId);
      throw error;
    }
  }
  
  async compensate(orderId: string): Promise<void> {
    // Execute compensating transactions in reverse order
    await this.inventoryService.releaseStock(orderId);
    await this.customerService.releaseCredit(orderId);
    await this.orderService.cancelOrder(orderId);
  }
}
```

**Comparison**:

| Aspect | Choreography | Orchestration |
|--------|-------------|---------------|
| Control Flow | Decentralized | Centralized |
| Coupling | Looser (events) | Tighter (orchestrator knows all steps) |
| Complexity | Moderate (eventual consistency) | Higher (orchestrator logic) |
| Monitoring | Difficult (distributed) | Easier (single orchestrator) |
| Error Recovery | Each service handles | Orchestrator coordinates |

**Recommendation**: Start with choreography, use orchestration for complex sagas.

### 14.3 Eventual Consistency

**Acceptance**: Data may be temporarily inconsistent, but will converge eventually.

**Countermeasures**:

1. **Idempotency**: Operations can be retried safely
```typescript
// Idempotent operation using idempotency key
const result = await this.repository.findByOperationId(operationId);
if (result) {
  return result; // Already processed
}
// Process operation
await this.repository.save({ operationId, ... });
```

2. **Read-Your-Writes**: User sees their own updates immediately
```typescript
// After write, read from write model (not eventual read model)
const user = await this.userRepository.findById(userId);
res.json(user);  // Fresh data
```

3. **Compensating Actions**: Explicit corrections for failures
```typescript
async function transferFunds(from: string, to: string, amount: number) {
  try {
    await debitAccount(from, amount);
    await creditAccount(to, amount);
  } catch (error) {
    // Compensate any partial debits
    await creditAccount(from, amount);
    throw error;
  }
}
```

4. **Version Stamps**: Detect stale updates
```typescript
interface Entity {
  id: string;
  data: any;
  version: number;  // Increment on each update
}

// Optimistic locking
async function updateEntity(id: string, update: Partial<Entity>) {
  const current = await repo.findById(id);
  if (update.version !== current.version) {
    throw new ConflictError('Stale data');
  }
  await repo.update(id, { ...update, version: current.version + 1 });
}
```

**When eventual consistency is acceptable**:
- User activity feeds (social media)
- Search indexes
- Analytics dashboards
- Non-critical aggregations

**When strong consistency needed**:
- Financial transactions
- Inventory reservations
- Seat bookings
- User account status

---

## 15. SERVICE DECOMPOSITION: DETAILED CRITERIA

### 15.1 Bounded Context Identification Process

**Step 1: Domain Exploration**
- Conduct Event Storming workshops
- Identify domain events, commands, aggregates
- Map business processes

**Event Storming Example**:
```
User Registration:
  UserRegistered[Event] ← UserRegisteredCommand
    └─ Validate Email → EmailValidationCompleted
    └─ Create Profile → ProfileCreated
    └─ Send Welcome Email → WelcomeEmailSent
```

**Step 2: Context Mapping**
```
Context Map:
┌─────────────────┐    ┌─────────────────┐
│  Identity       │    │  Order          │
│  Context        │◄──►│  Context        │
│                 │    │                 │
│ - Users         │    │ - Orders        │
│ - Auth          │    │ - Cart          │
│ - Permissions   │    │ - Checkout      │
└─────────────────┘    └─────────────────┘
         ▲                       ▲
         │                       │
┌─────────────────┐    ┌─────────────────┐
│  Shared Kernel  │    │  Customer       │
│  (User DTOs)    │    │  Context        │
└─────────────────┘    │ - Profile       │
                       │ - Preferences   │
                       └─────────────────┘
```

**Step 3: Service Extraction Decision**

**Extract as service if**:

...10388 bytes truncated...

The tool call succeeded but the output was truncated. Full output saved to: /home/notroot/.local/share/kilo/tool-output/tool_cce33fd49001uHa3Sl7awh303q
Use the Task tool to have explore agent process this file with Grep and Read (with offset/limit). DO NOT read the full file yourself - delegate to save context.

---
- Independent business capability
- Owns distinct data (no shared tables)
- Can be scaled separately
- Team of 2-10 people can own it
- Changes independently (low coupling)

**Keep in monolith if**:
- Tight coupling (same transaction)
- Shared database schema unavoidable
- Too small to warrant separate deployment
- Changes always coordinated with other parts

### 15.2 Decomposition Patterns

**1. Decompose by Business Capability**
```
E-commerce → Catalog, Cart, Order, Payment, Shipping, User
```

**2. Decompose by Subdomain (DDD)**
```
E-commerce:
├─ Core Subdomain: Order, Inventory, Pricing
├─ Supporting: User, Notification
└─ Generic: File Storage, Email Delivery
```

**3. Decompose by Verbs/Nouns**
```
Nouns (Resources): User, Product, Order
Verbs (Processes): Checkout, Payment, Shipping
```

**4. Decompose by Volatility** (Advanced)
- Services that change frequently separated from stable ones
- Higher change velocity → smaller, more agile services

### 15.3 Service Size Guidelines

**Too Large (>10k LOC)**:
- Multiple teams working on same service
- Difficult to test end-to-end
- Deployment coordination required
- **Action**: Split by business capability

**Too Small (<1k LOC)**:
- Overhead of separate deployment outweighs benefits
- Too many services to manage
- **Action**: Merge related services

**Sweet Spot**: 1,000-5,000 lines of code, 1-2 databases, 1 team

---

## 16. IMPLEMENTATION PRIORITY MATRIX

### Phase 1: Foundation (Weeks 1-4) - **Low Risk, High Impact**

| Task | Effort | Risk | Priority | Dependencies |
|------|--------|------|----------|--------------|
| Set up pnpm monorepo | 1-2 days | Very Low | **P0** | None |
| Create shared packages (types, logger, config) | 1 week | Low | **P0** | Monorepo |
| Docker Compose dev environment | 1-2 days | Very Low | **P0** | None |
| Basic CI/CD for shared packages | 1 week | Low | **P0** | Shared packages |
| Identify service boundaries (DDD) | 2 weeks | Low | **P0** | Domain knowledge |
| First service selection | 3 days | Low | **P0** | Boundary analysis |

### Phase 2: Extrace First Service (Weeks 5-10) - **Medium Risk, High Value**

| Task | Effort | Risk | Priority | Dependencies |
|------|--------|------|----------|--------------|
| Extract User Service (low risk) | 4-6 weeks | Medium | **P0** | Foundation |
| Database per service setup | 1-2 weeks | Medium | **P0** | Service design |
| API Gateway/Strangler setup | 2 weeks | Medium | **P1** | First service |
| Contract testing framework | 2-3 weeks | Low | **P0** | Shared packages |
| Basic monitoring (logs, metrics) | 1 week | Low | **P1** | K8s cluster |

### Phase 3: Scale Out (Weeks 11-20) - **Medium Risk**

| Task | Effort | Risk | Priority | Dependencies |
|------|--------|------|----------|--------------|
| Extract 2-3 more services | 3-4 weeks each | Medium | **P0** | First service done |
| Kubernetes production setup | 4-6 weeks | Medium | **P0** | Staging validated |
| OpenTelemetry tracing | 2-3 days per service | Low | **P1** | Services running |
| Advanced CI/CD (GitOps) | 2-3 weeks | Medium | **P1** | Basic CI/CD stable |
| Saga pattern for transactions | 2-4 weeks | High | **P1** | Multiple services |

### Phase 4: Optimize (Weeks 21+) - **Lower Risk**

| Task | Effort | Risk | Priority |
|------|--------|------|----------|
| Performance tuning | Ongoing | Low | P2 |
| Cost optimization | Ongoing | Low | P2 |
| Monolith decommission | 4-6 weeks | Medium | P0 |
| Advanced patterns (CQRS) | 4+ weeks | High | P2 |

---

## 17. RECOMMENDATIONS BY PRIORITY

### Critical (Do First) ⭐⭐⭐

1. **Use Strangler Fig pattern** - Never big-bang rewrite
2. **Set up monorepo with pnpm workspaces** - Shared code management foundation
3. **Database per service from start** - Avoid shared database lock-in
4. **Implement contract testing** - Enable independent deployment
5. **Start with Docker Compose for dev** - Fast feedback loop
6. **Choose REST first, add gRPC for internal high-throughput** - Progressive enhancement
7. **Structured logging from day one** - Observability foundation
8. **Extract lowest-risk service first** - Learn with minimal impact

### Important (Do Early) ⭐⭐

9. **Set up Kubernetes for staging** - Production readiness
10. **Implement basic metrics with Prometheus** - Monitoring foundation
11. **Saga pattern for cross-service transactions** - Data consistency
12. **Service discovery via K8s DNS** - Zero-cost for single cluster
13. **Configuration management with ConfigMaps** - Environment isolation
14. **API Gateway for request routing** - Strangler Fig enablement

### Advanced (Do Later) ⭐

15. **OpenTelemetry distributed tracing** - Advanced observability
16. **GitOps for deployments** - Declarative infrastructure
17. **Consul for multi-cluster** - Only if needed
18. **CQRS for read/write separation** - Only for high-scale scenarios
19. **Event sourcing** - Complex, only for audit-heavy domains
20. **Service mesh (Istio/Linkerd)** - Advanced traffic management

---

## 18. NODE.JS/PNPM SPECIFIC BEST PRACTICES

### 18.1 Monorepo Structure

```
my-monolith-migration/
├── pnpm-workspace.yaml
├── turbo.json                    # Turborepo config for parallel tasks
├── package.json                  # Root (devDependencies only)
├── .github/workflows/            # CI/CD
├── docker-compose.yml           # Dev environment
├── k8s/                         # Kubernetes manifests
├── packages/                    # Shared libraries
│   ├── shared-types/
│   ├── shared-utils/
│   ├── logger/
│   └── config/
└── services/                    # Microservices
    ├── user-service/
    │   ├── src/
    │   ├── tests/
    │   ├── Dockerfile
    │   ├── package.json
    │   └── k8s/
    ├── order-service/
    └── product-service/
```

### 18.2 Package Scripts

**Root package.json**:
```json
{
  "scripts": {
    "build": "turbo run build",
    "test": "turbo run test",
    "test:cov": "turbo run test:cov",
    "lint": "turbo run lint",
    "type-check": "turbo run type-check",
    "dev": "docker-compose up",
    "clean": "turbo run clean"
  }
}
```

**Service package.json**:
```json
{
  "name": "@myorg/user-service",
  "version": "1.0.0",
  "main": "dist/index.js",
  "scripts": {
    "build": "tsc",
    "start": "node dist/index.js",
    "dev": "nodemon --watch src --exec ts-node src/index.ts",
    "test": "jest",
    "test:cov": "jest --coverage",
    "lint": "eslint src/",
    "type-check": "tsc --noEmit"
  }
}
```

### 18.3 Turborepo Configuration

**turbo.json**:
```json
{
  "pipeline": {
    "build": {
      "dependsOn": ["^build"],
      "outputs": ["dist/**"]
    },
    "test": {
      "dependsOn": ["build"],
      "outputs": []
    },
    "test:cov": {
      "dependsOn": ["build"],
      "outputs": ["coverage/**"]
    },
    "lint": {
      "outputs": []
    },
    "type-check": {
      "dependsOn": ["build"],
      "outputs": []
    },
    "dev": {
      "cache": false,
      "persistent": true
    }
  }
}
```

**Benefits**:
- Parallel task execution
- Incremental builds (only changed packages)
- Remote caching for CI

---

## 19. COMMON PITFALLS & AVOIDANCE

| Pitfall | Symptoms | Prevention | Remediation |
|---------|----------|-------------|-------------|
| **Shared database** | Schema changes break multiple services | Enforce DB-per-service from start | Extract databases, add events |
| **Chatty services** | Cascading timeouts, high latency | Set latency SLOs, use async | Add caching, aggregate services |
| **Temporal coupling** | One slow service cascades failures | Timeout circuits, bulkheads | Use async messaging |
| **Service discovery issues** | "Connection refused" errors | Health checks, retries, circuit breakers | Implement resilience patterns |
| **Configuration sprawl** | Different envs behave differently | Config validation, version control | Centralize config, use GitOps |
| **Logging inconsistencies** | Cannot correlate logs across services | Structured logging, trace IDs | Implement OpenTelemetry from start |
| **Version hell with shared libs** | Cannot upgrade dependencies | Semantic versioning, minimal sharing | Refactor shared libs, duplicate if needed |

---

## 20. SUCCESS METRICS & KPIs

### Technical Metrics

- **Deployment frequency**: Target >1 deployment/service/day
- **Lead time for changes**: Target <1 day
- **Mean time to recovery (MTTR)**: Target <1 hour
- **Change failure rate**: Target <15%
- **Service availability**: Target 99.9% per service
- **End-to-end latency**: Track P95, P99 across service calls

### Business Metrics

- **Developer productivity**: Features per team per sprint
- **Time to market**: Feature concept → production
- **System reliability**: Uptime, error rates
- **Scalability**: Requests per second capacity

### Migration-Specific Metrics

- **Percentage of monolith functionality extracted**: Target 20% first service, then 10% per month
- **Monolith code churn**: Should trend downward
- **Incidents related to migration**: Should trend downward after initial phase
- **Team satisfaction**: Survey monthly

---

## CONCLUSION

The most successful monorepo-to-microservices migrations follow these principles:

1. **Incremental over big-bang**: Strangler Fig pattern reduces risk
2. **Database per service**: Commit to autonomy early
3. **Contract testing**: Enables independent deployment
4. **Shared code discipline**: Only utilities, never business logic
5. **Observability from day one**: You can't debug what you can't see
6. **Automated CI/CD**: GitOps for production-grade deployments
7. **Start simple, evolve**: REST + HTTP first, add gRPC/events as needed
8. **Team alignment with service boundaries**: Conway's Law in reverse

**Timeline Expectation**: 
- Minimal viable microservices architecture: 3-4 months
- Full monolith replacement: 9-18 months (depending on size)

**Team Size**: Minimum 2-3 teams of 4-6 engineers each to see microservices benefits.

**Investment Required**: Expect 20-30% increase in infrastructure complexity, 10-20% temporary productivity dip during initial extraction, payback within 12-18 months through increased velocity and scalability.

The migration is not a destination but a journey toward architectural agility.
</task_result>