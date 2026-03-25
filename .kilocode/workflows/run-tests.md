# Run Tests Workflow

You are helping run the test suite for this project. Follow these steps:

## Test Structure

Tests are located in `tests/`:
- `test_api/`: API endpoint tests
- `test_services/`: Service layer tests
- `conftest.py`: Shared pytest fixtures

## Steps

### 1. Setup Test Environment
- Ensure `.env` has `DATABASE_URL` pointing to test database
- Use SQLite for local testing if possible
- Environment variable: `TEST_DATABASE_URL=sqlite:///./test.db`

### 2. Install Test Dependencies
```bash
pip install pytest pytest-asyncio httpx
```

### 3. Run All Tests
```bash
pytest tests/ -v
pytest tests/ --cov=app --cov-report=html
```

### 4. Run Specific Test Suites
```bash
# API tests only
pytest tests/test_api/ -v

# Service tests only
pytest tests/test_services/ -v

# Single test file
pytest tests/test_api/test_auth.py -v
```

### 5. Run with Coverage
```bash
pytest tests/ --cov=app --cov-report=term-missing
```

### 6. Common Options
- `-v`: Verbose output
- `-s`: Show print statements
- `-x`: Stop on first failure
- `--lf`: Run only last failed tests

## Test Patterns

### API Test Example
```python
from fastapi.testclient import TestClient

def test_register():
    client = TestClient(app)
    response = client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "password123"
    })
    assert response.status_code == 201
```

### Async Test Example
```python
import pytest

@pytest.mark.asyncio
async def test_download():
    # Async test code here
    pass
```

## Troubleshooting
- Database issues: Check DATABASE_URL is set
- Import errors: Ensure PYTHONPATH includes project root
- Connection refused: Start required services first
