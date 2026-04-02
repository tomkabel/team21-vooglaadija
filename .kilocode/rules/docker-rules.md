# Docker Rules

Follow these rules when working with Docker.

## Dockerfile

- Use multi-stage builds to reduce image size
- Run as non-root user
- Specify exact versions in FROM
- Use `.dockerignore` to exclude unnecessary files

## Best Practices

- Don't store secrets in images
- Use health checks for containers
- Set appropriate resource limits
- Use volumes for persistent data

## Development

- Use volume mounts for hot reload
- Don't expose debug ports in production
- Use docker-compose for local development

## Security

- Scan images for vulnerabilities regularly
- Update base images frequently
- Don't run as root
- Use read-only volumes where possible

## Test Containers

### Test Service Overrides

For integration tests requiring external services (PostgreSQL, Redis), use docker-compose overrides:

```yaml
# docker-compose.override.yml for testing
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: test_db
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_pass
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_user -d test_db"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5
```

### Test Database Patterns

- Use `postgres:16-alpine` for lightweight PostgreSQL testing
- Always create dedicated test databases (never use production DB)
- Use health checks to ensure services are ready before running tests
- Set appropriate resource limits for test containers:
  ```yaml
  resources:
    limits:
      memory: 512M
      cpus: "0.5"
  ```

### Docker Compose for Tests

```bash
# Start test services only
docker-compose -f docker-compose.yml -f docker-compose.override.yml up -d db redis

# Run tests against test services
hatch run test:integration

# Clean up test services
docker-compose -f docker-compose.yml -f docker-compose.override.yml down
```

### Test Container Cleanup

- Always clean up test containers after tests complete
- Use `docker-compose down -v` to remove volumes
- Consider using test-specific Docker networks for isolation
