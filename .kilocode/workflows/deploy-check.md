# Deploy Readiness Check

You are helping verify the application is ready for deployment. Follow these steps:

## Pre-deployment Checklist

### 1. Environment Configuration
- [ ] `.env` is properly configured with production values
- [ ] `SECRET_KEY` is a strong, unique key
- [ ] `DATABASE_URL` points to production PostgreSQL
- [ ] `REDIS_URL` points to production Redis
- [ ] CORS origins are properly configured

### 2. Security Checklist
- [ ] No hardcoded secrets in code
- [ ] All secrets in environment variables
- [ ] HTTPS enabled/configured
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] Authentication required on protected routes

### 3. Database Checklist
- [ ] Migrations tested on staging
- [ ] Database backup strategy in place
- [ ] Connection pooling configured
- [ ] Health check endpoint returns DB status

### 4. Monitoring Checklist
- [ ] Logging configured (INFO level)
- [ ] Error tracking (Sentry, etc.)
- [ ] Metrics endpoint available
- [ ] Health endpoint accessible

### 5. Docker/Container Checklist
- [ ] `Dockerfile` optimized (multi-stage build)
- [ ] `docker-compose.yml` production-ready
- [ ] No debug ports exposed
- [ ] Resource limits set
- [ ] Health checks configured

### 6. API Checklist
- [ ] All endpoints documented (`/docs`)
- [ ] Error responses consistent
- [ ] Timeout configured appropriately
- [ ] Request size limits set

## Verification Commands

### Test Staging Environment
```bash
# Deploy to staging
docker-compose -f docker-compose.yml up -d

# Check health
curl https://staging.example.com/api/v1/health

# Check logs
docker-compose logs -f api
```

### Run Production Checks
```bash
# Security audit
bandit -r app/

# Dependency check
pip-audit

# Container scan
trivy image your-image:latest
```

## Deployment Steps

1. **Backup Database**
2. **Deploy to Staging**
3. **Run Integration Tests**
4. **Deploy to Production**
5. **Verify Health**
6. **Monitor Logs**

## Rollback Plan

If deployment fails:
1. Check logs: `docker-compose logs`
2. Rollback: `docker-compose down && docker-compose up -d <previous-tag>`
3. Restore database from backup if needed
