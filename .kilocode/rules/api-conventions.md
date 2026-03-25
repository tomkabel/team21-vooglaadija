# API Conventions

Follow these conventions when creating or modifying API endpoints.

## URL Structure

- Use plural nouns: `/users` not `/user`
- Use kebab-case: `/download-requests`
- Nest resources appropriately: `/users/{id}/downloads`
- Version APIs: `/api/v1/resource`

## HTTP Methods

| Method | Usage |
|--------|-------|
| GET | Retrieve resources |
| POST | Create new resources |
| PUT | Full update |
| PATCH | Partial update |
| DELETE | Remove resources |

## Response Format

```json
{
  "data": { ... },
  "message": "Optional message"
}
```

For lists:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 10,
    "total": 100
  }
}
```

## Error Responses

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  }
}
```

Use standard HTTP codes:
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 422: Validation Error
- 500: Internal Error

## Naming Conventions

- Use snake_case for JSON fields
- Use camelCase for JavaScript clients
- Prefix boolean fields with `is_`, `has_`, `can_`

## Query Parameters

- `page`: Pagination page number
- `per_page`: Items per page (default 20, max 100)
- `sort`: Sort field with `-` prefix for descending
- `filter`: Filter expression
