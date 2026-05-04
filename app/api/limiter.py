This file handles the logic and setup.

```python
import os
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.extension import NoOpLimiter
from slowapi.storages import RedisStorage
from redis.exceptions import ConnectionError, TimeoutError

# Define the key identifier
def get_dual_identifier(request: Request) -> str:
    ip = get_remote_address(request)
    # Assumes your auth middleware puts user info here
    user_id = getattr(request.state, "user", "anonymous")
    return f"{ip}:{user_id}"

is_testing = os.getenv("APP_ENV") == "test"
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

if is_testing:
    limiter = NoOpLimiter()
else:
    # strategy="moving-window" provides atomic sliding window via Lua
    storage = RedisStorage.from_url(redis_url)
    limiter = Limiter(
        key_func=get_dual_identifier,
        storage=storage,
        strategy="moving-window", 
        headers_enabled=True,
        swallow_errors=False  # Crucial for Fail-Closed
    )
```