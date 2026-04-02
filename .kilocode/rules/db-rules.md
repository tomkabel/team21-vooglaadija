# Database Rules

Follow these rules when working with the database.

## Async Operations

- Always use async/await for database operations
- Never block the event loop
- Use `async with` for sessions

## Queries

- Use parameterized queries (prevent SQL injection)
- Index frequently queried columns
- Limit results with pagination
- Use `select()` for specific columns when possible

## Models

- Use SQLAlchemy 2.0 style
- Define relationships in models
- Use UUID for primary keys
- Add `created_at` and `updated_at` timestamps

## Migrations

- Use Alembic for migrations
- Always test on staging first
- Never modify migration files after running
- Backup database before migrating

## Transactions

- Use transactions for multi-step operations
- Rollback on error
- Don't hold transactions longer than necessary

## Test Database Patterns

For testing, use SQLite with aiosqlite for fast, isolated test execution:

```python
# Per-worker database for parallel test isolation
import os
_worker_id = os.environ.get("PYTEST_XDIST_WORKER", "gw0")
_test_db_url = f"sqlite+aiosqlite:///test_{_worker_id}.db"
```

### Test Database Benefits

- **Isolation**: Each xdist worker gets its own database file
- **Speed**: SQLite is faster than PostgreSQL for tests
- **No cleanup**: Files can be deleted after test run
- **Parallel safety**: Avoids race conditions in parallel execution

### Transaction Rollback for Performance

Use transaction rollback to speed up tests:

```python
@pytest.fixture(autouse=True)
async def setup_database():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
```

### Per-Worker Database Isolation

The project uses `PYTEST_XDIST_WORKER` environment variable to create unique databases:
- `test_gw0.db` for worker 0
- `test_gw1.db` for worker 1
- etc.

This prevents SQLite race conditions during parallel test execution.
