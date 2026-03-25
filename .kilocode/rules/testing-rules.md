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

### Integration Tests
- Test API endpoints
- Use TestClient
- May use test database

### Fixtures
- Use `conftest.py` for shared fixtures
- Create minimal data needed for tests
- Clean up after tests

## Assertions

- Test happy path and error cases
- Test edge cases and boundaries
- Use descriptive assertion messages

## Async Tests

- Use `@pytest.mark.asyncio`
- Use `pytest-asyncio`
- Clean up async resources
