---
name: fastapi-auth
description: Implement JWT authentication and authorization in FastAPI. Use when creating protected routes, managing user sessions, or implementing authentication flows.
version: 1.0.0
---

# FastAPI Authentication Skill

This skill provides guidance for JWT authentication implementation in the project.

## Project Context

Authentication is implemented in `app/auth.py` with JWT tokens. User model in `app/models/user.py`.

## Architecture

### Authentication Flow
1. User registers via `/api/v1/auth/register`
2. User logs in via `/api/v1/auth/login` 
3. Server returns access + refresh tokens
4. Client uses access token for protected routes
5. Refresh token used to obtain new access token

### Token Structure
- **Access Token**: 15-minute expiry (configurable)
- **Refresh Token**: 7-day expiry (configurable)
- Token contains: user_id, email, role

## Implementation Patterns

### Protected Route
```python
from fastapi import Depends, HTTPException, status
from app.auth import get_current_user

@router.get("/protected")
def protected_route(user = Depends(get_current_user)):
    return {"user": user}
```

### Password Hashing
```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

### JWT Creation
```python
from jose import JWTError, jwt
from datetime import datetime, timedelta

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm="HS256")
```

## Security Best Practices

1. **Never store plain passwords** - Always hash with bcrypt
2. **Use HTTPS** in production - Tokens can be intercepted otherwise
3. **Implement token refresh** - Short-lived access tokens
4. **Validate input** - Sanitize all user inputs
5. **Rate limit auth endpoints** - Prevent brute force attacks
6. **Store secrets in env variables** - Never hardcode keys

## Common Issues

- **Token Expiry**: Handle 401 responses by refreshing token
- **Invalid Tokens**: Return proper error messages
- **Password Reset**: Implement secure reset flow
- **Session Management**: Consider Redis for session storage
