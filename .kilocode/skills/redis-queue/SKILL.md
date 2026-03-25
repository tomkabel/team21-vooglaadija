---
name: redis-queue
description: Implement Redis queue patterns for background job processing. Use when setting up task queues, caching, or message passing between services.
version: 1.0.0
---

# Redis Queue Skill

This skill provides guidance for Redis queue implementation in this project.

## Project Context

Redis is used for job queue in `worker/queue.py` and caching. Worker processes in `worker/processor.py`.

## Architecture

### Queue Structure
- **Main Queue**: `downloads:queue` - Pending download jobs
- **Processing**: `downloads:processing` - Currently processing
- **Failed**: `downloads:failed` - Failed jobs for retry

### Job Lifecycle
```
PENDING -> PROCESSING -> COMPLETED/FAILED
   |          |
   v          v
  Redis     Redis
  Queue     Set
```

## Implementation Patterns

### Enqueue Job
```python
import redis
import json

r = redis.from_url("redis://localhost:6379")

def enqueue_job(job_data: dict):
    job_id = str(uuid.uuid4())
    job = {
        "id": job_id,
        "url": job_data["url"],
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }
    r.lpush("downloads:queue", json.dumps(job))
    return job_id
```

### Worker Processing Loop
```python
def process_queue():
    while True:
        job_data = r.brpop("downloads:queue")
        job = json.loads(job_data[1])
        
        try:
            # Process job
            download_media(job["url"])
            r.lpush("downloads:completed", job["id"])
        except Exception as e:
            r.lpush("downloads:failed", job["id"])
        
        time.sleep(1)
```

### Job Status with Redis
```python
def set_job_status(job_id: str, status: str):
    r.hset(f"job:{job_id}", "status", status)

def get_job_status(job_id: str) -> str:
    return r.hget(f"job:{job_id}", "status")
```

## Caching Patterns

### Cache API Response
```python
def cache_response(key: str, value: str, ttl: int = 3600):
    r.setex(f"cache:{key}", ttl, value)

def get_cached(key: str) -> str:
    return r.get(f"cache:{key}")
```

## Best Practices

1. **Use Redis Streams** for modern queue implementation
2. **Implement dead letter queue** for failed jobs
3. **Add job timeouts** prevent stuck processing
4. **Use Lua scripts** for atomic operations
5. **Monitor Redis memory** for large queues
6. **Implement backoff** for failed jobs

## Configuration

Environment variables:
- `REDIS_URL`: Redis connection string
- Default: `redis://localhost:6379`
