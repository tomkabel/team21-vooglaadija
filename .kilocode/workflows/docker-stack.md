# Docker Stack Management

You are helping manage the Docker stack for this project. Follow these steps:

## Services

The stack includes:
- **api**: FastAPI application
- **worker**: Background job processor
- **db**: PostgreSQL 15
- **redis**: Redis 7

## Common Operations

### Start Stack
```bash
# All services
docker-compose up -d

# Specific services
docker-compose up -d db redis api
```

### Stop Stack
```bash
# Stop and keep volumes
docker-compose down

# Stop and remove volumes (data loss!)
docker-compose down -v

# Stop and remove images
docker-compose down --rmi all
```

### Rebuild
```bash
# Rebuild without cache
docker-compose build --no-cache

# Rebuild and start
docker-compose up -d --build
```

### Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f worker

# Last N lines
docker-compose logs --tail=100 api
```

### Debugging

#### Enter Container
```bash
docker-compose exec api sh
docker-compose exec worker sh
docker-compose exec db psql -U vooglaadija
docker-compose exec redis redis-cli
```

#### Check Status
```bash
docker-compose ps
docker-compose top
```

### Database Operations

#### Run Migrations
```bash
docker-compose exec api alembic upgrade head
```

#### Reset Database
```bash
docker-compose down -v
docker-compose up -d db
# Wait for db to be ready
docker-compose exec api alembic upgrade head
```

## Troubleshooting

### Container won't start
```bash
docker-compose logs <service>
docker-compose config
```

### Port conflicts
```bash
# Check what's using the port
lsof -i :8000
# Modify ports in docker-compose.yml or .env
```

### Database connection issues
```bash
# Check db is ready
docker-compose exec db pg_isready -U vooglaadija

# Check connection from API
docker-compose exec api python -c "import asyncpg; ..."
```

### Redis connection issues
```bash
docker-compose exec redis redis-cli ping
```
