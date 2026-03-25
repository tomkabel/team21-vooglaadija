# Local Development Setup

You are helping set up the local development environment for this YouTube Link Processor project. Follow these steps:

## Pre-requisites
- Docker and Docker Compose installed
- Python 3.11+ (for local development without Docker)

## Steps

### 1. Environment Setup
- Check if `.env` file exists
- If not, copy from `.env.example` and fill in required values:
  - `DATABASE_URL`: PostgreSQL connection string
  - `SECRET_KEY`: JWT signing key
  - `REDIS_URL`: Redis connection string

### 2. Start Services
- Run `docker-compose up -d` to start all services
- Verify services are running: `docker-compose ps`
- Check the API health: `curl http://localhost:8000/api/v1/health`

### 3. Local Python Setup (Optional)
- Create a virtual environment: `python -m venv venv`
- Activate: `source venv/bin/activate` (Linux) or `venv\Scripts\activate` (Windows)
- Install dependencies: `pip install -r requirements.txt`

### 4. Verify Services
- Database: Check PostgreSQL is accepting connections
- Redis: Verify Redis is responding: `redis-cli ping`
- API: Health endpoint returns 200

### 5. Start Development Servers
- API: `uvicorn app.main:app --reload --port 8000`
- Worker: `python worker/main.py`

## Usage
- API docs available at `http://localhost:8000/docs`
- API base URL: `http://localhost:8000/api/v1`

## Troubleshooting
- Use `docker-compose logs -f <service>` to check logs
- Use `docker-compose down -v` to reset everything
