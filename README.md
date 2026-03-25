<div align="center">

# YouTube Link Processor

High-performance YouTube media extraction API with async processing

[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-GPLv3-A41E35?style=for-the-badge&logo=gnu&logoColor=white)](https://www.gnu.org/licenses/gpl-3.0.html)
[![Version](https://img.shields.io/badge/Version-0.0.1-22D3EE?style=for-the-badge)](https://github.com/yourusername/vooglaadija)
[![FastAPI](https://img.shields.io/badge/FastAPI-26A69A?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F1B?style=for-the-badge&logo=sqlalchemy)](https://www.sqlalchemy.org/)
[![uvicorn](https://img.shields.io/badge/uvicorn-2D3748?style=for-the-badge&logo=uvicorn)](https://www.uvicorn.org/)
[![JWT](https://img.shields.io/badge/JWT-000000?style=for-the-badge&logo=json-web-tokens)](https://jwt.io/)
[![Code%20Style-black](https://img.shields.io/badge/Code%20Style-black-000000?style=for-the-badge&logo=black)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/badge/Ruff-041635?style=for-the-badge&logo=ruff)](https://docs.astral.sh/ruff/)

</div>

<div align="center">
  <img src="docs/images/vooglaadija_fin.png" alt="YouTube Link Processor" width="600" />
</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Quick Start](#-quick-start)
- [Usage](#-usage)
- [API Reference](#-api-reference)
- [Environment Variables](#-environment-variables)
- [Tech Stack](#-tech-stack)
- [Architecture](#-architecture)
- [Contributing](#-contributing)
- [License](#-license)
- [Contact](#-contact)

---

## 📖 Overview

**YouTube Link Processor** is a production-grade REST API service for extracting and downloading media from YouTube URLs. Built with FastAPI, it leverages async/await patterns for high-throughput request handling, with background job processing via Redis queues for resource-intensive media extraction operations.

The system employs a decoupled architecture: the FastAPI application handles authentication, job management, and file delivery, while a dedicated worker process consumes jobs from Redis and performs media extraction using yt-dlp.

---

## ✨ Features

- **🔐 Secure Authentication** — JWT-based auth with access/refresh token rotation
- **⚡ Async Processing** — Non-blocking job queue with Redis-backed worker
- **📊 Job Lifecycle Management** — Complete job states: pending → processing → completed/failed
- **🔗 Flexible Media Extraction** — yt-dlp powered extraction for various formats
- **⏰ Expiring Downloads** — Time-limited download links (configurable, default 24h)
- **🐳 Container-Ready** — Multi-stage Docker builds with multi-arch support
- **🧪 Test Suite** — Comprehensive pytest coverage with async test support

---

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- PostgreSQL 14+
- Redis 7+

### Option 1: Docker Compose (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/vooglaadija.git
cd vooglaadija

# Start all services
docker-compose up -d
```

### Option 2: Local Development

```bash
# Clone and setup
git clone https://github.com/yourusername/vooglaadija.git
cd vooglaadija

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run the worker (separate terminal)
python -m worker.main
```

---

## 💻 Usage

### Register a new user

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword123"}'
```

### Login and obtain tokens

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "securepassword123"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Create a download job

```bash
curl -X POST http://localhost:8000/api/v1/downloads \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Check job status

```bash
curl -X GET http://localhost:8000/api/v1/downloads/550e8400-e29b-41d4-a716-446655440000 \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Download the file

```bash
curl -X GET "http://localhost:8000/api/v1/downloads/550e8400-e29b-41d4-a716-446655440000/file" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -o downloaded_file.mp4
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register new user account |
| `POST` | `/api/v1/auth/login` | Authenticate and get JWT tokens |
| `POST` | `/api/v1/auth/refresh` | Refresh access token |
| `GET` | `/api/v1/me` | Get current user profile |
| `POST` | `/api/v1/downloads` | Create new download job |
| `GET` | `/api/v1/downloads` | List user's download jobs |
| `GET` | `/api/v1/downloads/{id}` | Get job status and details |
| `GET` | `/api/v1/downloads/{id}/file` | Download the processed file |
| `DELETE` | `/api/v1/downloads/{id}` | Delete a download job |
| `GET` | `/api/v1/health` | Service health check |

---

## ⚙️ Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@localhost:5432/ytprocessor` |
| `SECRET_KEY` | JWT signing key | `change-me` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379` |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token expiry (minutes) | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token expiry (days) | `7` |
| `FILE_EXPIRE_HOURS` | Download link expiry (hours) | `24` |
| `STORAGE_PATH` | Local storage directory | `./storage` |

---

## 🛠 Tech Stack

| Technology | Purpose |
|------------|---------|
| ![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white) | Runtime |
| ![FastAPI](https://img.shields.io/badge/FastAPI-26A69A?style=for-the-badge&logo=fastapi&logoColor=white) | API Framework |
| ![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-D71F1B?style=for-the-badge&logo=sqlalchemy) | ORM |
| ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?style=for-the-badge&logo=postgresql&logoColor=white) | Database |
| ![Redis](https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white) | Queue & Cache |
| ![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white) | Containerization |
| ![GitHub%20Actions](https://img.shields.io/badge/GitHub_Actions-2088FF?style=for-the-badge&logo=github&logoColor=white) | CI/CD |

### Key Libraries

- `python-jose[cryptography]` — JWT token handling
- `passlib[bcrypt]` — Password hashing
- `yt-dlp` — Media extraction engine
- `pytest` — Testing framework

---

## 🏗 Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  FastAPI    │────▶│ PostgreSQL  │
│ Application │     │     API     │     │  Database   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │    Redis    │
                    │    Queue    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   Worker    │────▶│   Storage   │
                    │  (yt-dlp)   │     │  (downloads)│
                    └─────────────┘     └─────────────┘
```

### Component Responsibilities

**API Server**
- User authentication (register, login, token refresh)
- Download job CRUD operations
- File streaming and expiration logic
- Health check endpoints

**Worker Process**
- Consumes jobs from Redis queue
- Extracts media using yt-dlp
- Updates job status in PostgreSQL
- Manages file lifecycle

---

## 🤝 Contributing

We welcome contributions! Please follow these guidelines:

### Development Workflow

1. **Fork** the repository
2. **Create** a feature branch: `feat/your-feature` or `fix/your-bug`
3. **Commit** your changes following conventional commits
4. **Push** to your fork and **create** a Pull Request
5. **Ensure** all tests pass before merging

### Branch Strategy

- `main` — Production-ready code only
- Feature branches — Short-lived, deleted after merge
- Direct commits to `main` are prohibited

### Code Standards

- Type hints required for all new code
- 100% test coverage for new features
- Follow PEP 8 with 100 character line limit
- Use `async`/`await` for I/O-bound operations

### Running Tests

```bash
# Run all tests with coverage
pytest tests/ --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_api/test_auth.py -v
```

---

## 📜 License

This project is licensed under the **GNU General Public License v3.0**.

```
YouTube Link Processor - REST API for YouTube media extraction
Copyright (C) 2024

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
```

---

## 📞 Contact

<div align="center">

[![GitHub](https://img.shields.io/badge/View_on-GitHub-181717?style=for-the-badge&logo=github)](https://github.com/yourusername/vooglaadija)
[![Issues](https://img.shields.io/badge/Report_Issue-EE3B3B?style=for-the-badge&logo=github)](https://github.com/yourusername/vooglaadija/issues)

*Built with FastAPI • Powered by yt-dlp*

</div>
