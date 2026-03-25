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
