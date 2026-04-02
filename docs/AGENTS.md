# Project Agents Documentation

**Version:** 1.0.0 | **Last Updated:** 2026-03-24

---

## Project Overview

**Project Name:** YouTube Link Processor  
**Type:** REST API Service  
**Core Functionality:** Receive YouTube URL → Extract media URL using yt-dlp → Return result to user

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI |
| Database | PostgreSQL (async with SQLAlchemy) |
| Queue | Redis |
| Auth | JWT (python-jose, passlib/bcrypt) |
| Container | Docker + Docker Compose |
| CI/CD | GitHub Actions |

---

## Key Files

| File | Description |
|------|-------------|
| `RESEARCH.md` | Full architectural research report |
| `STRUCTURE.md` | Estonian project structure documentation |
| `DOCKER-MONITORING.md` | Docker monitoring options research |

---

## Core Flow

```
User → POST /api/v1/downloads {url}
    → Job created in DB (status: pending)
    → Worker processes with yt-dlp
    → File stored in storage/downloads/
    → User GET /api/v1/downloads/{id}/file
```

---

## API Endpoints

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Get JWT tokens |
| POST | `/api/v1/auth/refresh` | Refresh access token |
| GET | `/api/v1/me` | Get current user |

### Downloads
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/downloads` | Create download job |
| GET | `/api/v1/downloads` | List user's downloads |
| GET | `/api/v1/downloads/{id}` | Get job status |
| GET | `/api/v1/downloads/{id}/file` | Download file |
| DELETE | `/api/v1/downloads/{id}` | Delete job |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health` | Service health check |

---

## Database Schema

### User
| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| email | VARCHAR(255) | Unique email |
| password_hash | VARCHAR(255) | Bcrypt hash |
| is_active | BOOLEAN | Account status |
| created_at | TIMESTAMP | Creation time |

### DownloadJob
| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Foreign key to User |
| url | TEXT | YouTube URL |
| status | VARCHAR(20) | pending/processing/completed/failed |
| file_path | VARCHAR(500) | Path to downloaded file |
| file_name | VARCHAR(255) | File name |
| error | TEXT | Error message if failed |
| created_at | TIMESTAMP | Job creation time |
| completed_at | TIMESTAMP | Completion time |
| expires_at | TIMESTAMP | File expiration |

---

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| DATABASE_URL | PostgreSQL connection string | Yes |
| SECRET_KEY | JWT signing key | Yes |
| REDIS_URL | Redis connection string | Yes |
| CORS_ORIGINS | Allowed CORS origins | No |
| ACCESS_TOKEN_EXPIRE_MINUTES | Token expiry (default: 15) | No |
| REFRESH_TOKEN_EXPIRE_DAYS | Refresh token expiry (default: 7) | No |
| FILE_EXPIRE_HOURS | Download link expiry (default: 24) | No |

---

## Docker Services

```yaml
services:
  api:        # FastAPI application
  worker:     # Background job processor
  db:         # PostgreSQL database
  redis:      # Queue and caching
```

---

## Monitoring

See `DOCKER-MONITORING.md` for detailed options:

- **Basic:** `docker stats`
- **Recommended:** cAdvisor + Prometheus + Grafana

---

## Testing

This project uses **Hatch** as the test runner with **pytest-xdist** for parallel execution.

```bash
# Run all tests
hatch run test:all

# Run unit tests only
hatch run test:unit

# Run integration tests only
hatch run test:integration

# Run with coverage
hatch run test:cov

# Generate HTML coverage report
hatch run test:cov-html
```

### Test Markers

The project defines custom pytest markers:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.slow` - Slow tests (skip with `-m "not slow"`)

### Test Database

Tests use **SQLite with aiosqlite** for isolation:
- Per-worker database files: `test_{worker_id}.db`
- Automatically handles parallel execution via pytest-xdist
- No external database required for most tests

---

## Deployment

**Recommended:** Render or Railway (simple)  
**AWS (if required):** ECS Fargate with RDS PostgreSQL

---

## Quick Reference

- **Port:** 8000 (API)
- **Prometheus:** 9090
- **Grafana:** 3000
- **cAdvisor:** 8080
- **PostgreSQL:** 5432
- **Redis:** 6379

---

*This document provides base information for agents working on this project. See individual documentation files for detailed information.*
