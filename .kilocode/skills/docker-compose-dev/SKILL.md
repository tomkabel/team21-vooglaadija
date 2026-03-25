---
name: docker-compose-dev
description: Set up and manage local development environment with Docker Compose. Use when starting services locally, debugging containers, or managing the development stack.
version: 1.0.0
---

# Docker Compose Development Skill

This skill provides guidance for local development with Docker Compose.

## Project Services

The docker-compose.yml defines:
- **api**: FastAPI application (port 8000)
- **worker**: Background job processor
- **db**: PostgreSQL database (port 5432)
- **redis**: Redis queue (port 6379)
- **nginx**: Reverse proxy (optional)

## Common Commands

### Start Services
```bash
docker-compose up -d
docker-compose up -d db redis  # Start specific services
```

### View Logs
```bash
docker-compose logs -f api
docker-compose logs -f worker
docker-compose logs -f  # All services
```

### Stop Services
```bash
docker-compose down
docker-compose down -v  # Remove volumes
```

### Rebuild
```bash
docker-compose build --no-cache
docker-compose up -d --build
```

## Development Workflow

### Initial Setup
1. Copy `.env.example` to `.env`
2. Run `docker-compose up -d`
3. Verify services: `docker-compose ps`
4. Check API: `curl http://localhost:8000/api/v1/health`

### Hot Reload
- API: Use `--reload` flag or volume mounts
- Worker: Rebuild on code changes

### Debugging

#### Enter Container
```bash
docker-compose exec api sh
docker-compose exec db psql -U postgres
```

#### View Environment
```bash
docker-compose exec api env
```

#### Network Debugging
```bash
docker network ls
docker network inspect <network>
```

## Database Operations

### Run Migrations
```bash
docker-compose exec api alembic upgrade head
```

### Backup Database
```bash
docker-compose exec db pg_dump -U vooglaadija > backup.sql
```

### Connect to Database
```bash
# Direct
docker-compose exec db psql -U vooglaadija

# From API container
docker-compose exec api python -c "import asyncio; from app.database import get_session; ..."
```

## Troubleshooting

### Container Won't Start
```bash
docker-compose logs <service>
docker-compose config  # Validate compose file
```

### Port Conflicts
```bash
# Check port usage
lsof -i :8000
# Override port in .env or docker-compose.yml
```

### Volume Issues
```bash
docker-compose down -v  # WARNING: Deletes data
docker volume ls
docker volume rm <volume>
```

### Network Issues
```bash
# Recreate network
docker-compose down
docker network prune
docker-compose up -d
```

## Security Notes

- Never commit `.env` with real credentials
- Use secrets for production
- Rotate database passwords regularly
- Scan images for vulnerabilities
