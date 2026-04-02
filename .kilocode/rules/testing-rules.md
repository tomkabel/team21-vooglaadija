# Testing Rules

Follow these rules when writing tests.

## Test Structure

- Test files go in `tests/`
- Mirror project structure: `tests/test_api/`, `tests/test_services/`
- Use descriptive test names: `test_register_creates_user`

## Test Types

### Unit Tests
- Test individual functions/methods
- Mock external dependencies
- Fast execution
- Use `@pytest.mark.unit` marker

### Integration Tests
- Test API endpoints
- Use TestClient
- May use test database
- Use `@pytest.mark.integration` marker

## Running Tests (Hatch)

This project uses Hatch as the test runner with pytest-xdist for parallel execution:

```bash
# Run unit tests only
hatch run test:unit

# Run integration tests only
hatch run test:integration

# Run all tests
hatch run test:all

# Run with coverage
hatch run test:cov

# Generate HTML coverage report
hatch run test:cov-html
```

### Parallel Execution

All test commands use `-n auto` for automatic parallel execution via pytest-xdist. The project automatically creates per-worker SQLite databases to avoid race conditions.

## Test Markers

Use markers to selectively run tests:

```python
import pytest

@pytest.mark.unit
def test_something():
    """Unit test - runs with hatch run test:unit"""
    pass

@pytest.mark.integration
async def test_api_endpoint():
    """Integration test - runs with hatch run test:integration"""
    pass

@pytest.mark.slow
async def test_heavy_operation():
    """Slow test - skip with -m 'not slow'"""
    pass
```

Run specific markers:
```bash
hatch run test:all -m "unit"
hatch run test:all -m "integration"
hatch run test:all -m "not slow"
```

## Fixtures

- Use `conftest.py` for shared fixtures
- Create minimal data needed for tests
- Clean up after tests

### conftest.py Patterns

The project uses sophisticated xdist worker isolation:

```python
# Per-worker database for parallel test isolation
_worker_id = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
_test_db_url = f"sqlite+aiosqlite:///test_{_worker_id}.db"
```

This creates unique databases per worker (e.g., `test_gw0.db`, `test_gw1.db`) to avoid SQLite race conditions.

### Available Fixtures

| Fixture | Description |
|---------|-------------|
| `db_session` | Async database session for tests |
| `sample_url` | Sample YouTube URL for testing |
| `client` | AsyncClient for API testing (from conftest) |

## Assertions

- Test happy path and error cases
- Test edge cases and boundaries
- Use descriptive assertion messages

## Async Tests

- Use `@pytest.mark.asyncio`
- Use `pytest-asyncio`
- Clean up async resources

## SQLite for Tests

The project uses SQLite (via aiosqlite) for test databases:

- Per-worker database files: `test_{worker_id}.db`
- Uses `NullPool` for connection management
- Tables created/dropped per test function
- Handles race conditions in parallel execution
