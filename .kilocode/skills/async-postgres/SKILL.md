---
name: async-postgres
description: Implement async database operations with SQLAlchemy 2.0 and PostgreSQL. Use when creating models, queries, or database operations in the project.
version: 1.0.0
---

# Async PostgreSQL Skill

This skill provides guidance for async database operations using SQLAlchemy 2.0 with PostgreSQL.

## Project Context

Database is configured in `app/database.py`. Models in `app/models/`. Services in `app/services/`.

## Architecture

### Async Engine Setup
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://user:pass@host/db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)
```

### Async Model Definition
```python
from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID, primary_key=True)
    email = Column(String(255), unique=True, index=True)
    password_hash = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
```

## Query Patterns

### Basic Async Query
```python
async def get_user_by_email(email: str):
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
```

### Insert
```python
async def create_user(user: User):
    async with async_session() as session:
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
```

### Update
```python
async def update_job_status(job_id: UUID, status: str):
    async with async_session() as session:
        result = await session.execute(
            select(DownloadJob).where(DownloadJob.id == job_id)
        )
        job = result.scalar_one()
        job.status = status
        await session.commit()
```

## Best Practices

1. **Always use async/await** - Never block in async context
2. **Use dependency injection** - Inject session into routes
3. **Handle connections properly** - Use context managers
4. **Use transactions** - Ensure atomic operations
5. **Index frequently queried columns** - Optimize performance

## Migrations

Use Alembic for migrations:
```bash
alembic revision --autogenerate -m "add column"
alembic upgrade head
```
