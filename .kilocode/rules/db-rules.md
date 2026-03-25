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
