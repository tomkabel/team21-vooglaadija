# Authentication Rules

Follow these rules when implementing authentication.

## Password Requirements

- Minimum 8 characters
- Store as bcrypt hash, never plain text
- Validate on backend, not just client

## JWT Tokens

- Use HS256 algorithm
- Access token: 15 minutes expiry
- Refresh token: 7 days expiry
- Include `user_id` and `email` in payload
- Never include password in token

## Protected Routes

- Always verify JWT on protected endpoints
- Return 401 for missing/invalid tokens
- Return 403 for valid token but insufficient permissions

## API Keys

- Use for service-to-service auth
- Rotate regularly
- Never commit to repository
- Store in environment variables

## Security Headers

Always include:
- `Content-Type: application/json`
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`

## Rate Limiting

- Auth endpoints: 5 requests/minute
- API endpoints: 60 requests/minute
- Return 429 when exceeded
