# Pull Request Review

You are helping review code changes for this project. Follow these steps:

## Pre-review Checklist

### 1. Check for Common Issues
- Search for `TODO` comments that shouldn't be committed
- Check for `console.log` or print statements
- Look for hardcoded credentials or API keys
- Check for commented-out code that should be removed

### 2. Run Linting
```bash
# Python linting
ruff check app/ tests/
black --check app/ tests/

# If using pre-commit
pre-commit run --all-files
```

### 3. Run Tests
```bash
pytest tests/ -v
```

### 4. Type Checking
```bash
mypy app/
```

## Code Review Focus Areas

### Security
- Authentication/authorization logic
- Input validation
- SQL injection prevention
- Secret handling
- Rate limiting

### API Design
- RESTful conventions followed
- Proper HTTP status codes
- Error response format consistency
- Request/response validation

### Database
- Proper async patterns
- Connection management
- Migration handling
- Query optimization

### Performance
- N+1 query patterns
- Caching implementation
- Background job efficiency
- Resource cleanup

### Testing
- Test coverage
- Proper fixtures
- Edge case handling
- Mock usage

## Review Process

1. **Understand the PR**: Read the description and motivation
2. **Check the diff**: Review each changed file
3. **Test locally**: Pull and test the changes
4. **Verify documentation**: Ensure docs are updated if needed
5. **Check CI status**: Verify all checks pass

## Comment Format

Use constructive feedback:
- **Suggestion**: "Consider using X because..."
- **Question**: "How does Y handle Z?"
- **Must Fix**: "This breaks because..."
- **Nitpick**: "Optional: could simplify to..."

## Common PR Issues to Flag

- Missing tests
- No documentation updates
- Breaking changes not noted
- Large files (>500 lines changed)
- Too many changes in one PR
