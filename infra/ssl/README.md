# SSL Certificates

## Security Warning

**Never commit private keys to the repository!** The `privkey.pem` file (and all `*.pem` files) should be added to `.gitignore` and loaded from an external secrets path.

### .gitignore

Add the following to your `.gitignore` file to prevent accidental commits of private keys:

```gitignore
# SSL Certificates - Never commit private keys
*.pem
privkey.pem
```

### External Secrets (Recommended)

For production deployments, load certificates from external secrets management:

```bash
# Mount from external secrets path (Docker example)
# In docker-compose.yml:
# volumes:
#   - /path/to/external/secrets/fullchain.pem:/etc/nginx/ssl/fullchain.pem:ro
#   - /path/to/external/secrets/privkey.pem:/etc/nginx/ssl/privkey.pem:ro

# Or using environment-specific configuration
export SSL_CERT_PATH=/run/secrets/fullchain.pem
export SSL_KEY_PATH=/run/secrets/privkey.pem
```

## Directory Contents (When Deployed)

This directory should contain (when deployed, not in repo):

- `fullchain.pem` - Full certificate chain
- `privkey.pem` - Private key (loaded from external secrets, not committed)

## Getting Certificates

### Option 1: Let's Encrypt (Recommended)

```bash
certbot certonly --webroot -w /var/www/certbot -d yourdomain.com
# Certs will be in /etc/letsencrypt/live/yourdomain.com/
```

### Option 2: Self-signed (Development only)

```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout privkey.pem -out fullchain.pem \
  -subj "/CN=localhost"
```

**Note:** Even for development, do not commit the generated `.pem` files. They will be ignored by `.gitignore`.

### Option 3: Commercial certificate

Purchase from a CA and place files here (for local use only - do not commit).

## Docker Production Deployment

```bash
# Copy certificates to this directory for local testing only
# For production, mount from external secrets:
docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d
```

### Production Best Practices

1. **Use Docker Secrets or Kubernetes Secrets** for certificate storage
2. **Mount certificates as read-only volumes** (`:ro`)
3. **Set restrictive file permissions** (`chmod 600 privkey.pem`)
4. **Rotate certificates regularly** (automate with certbot or similar)
5. **Never commit certificates to version control**

### Example: Docker Compose with External Secrets

```yaml
version: '3.8'
services:
  nginx:
    image: nginx:alpine
    volumes:
      # Mount from external secrets path, read-only
      - /etc/letsencrypt/live/yourdomain.com/fullchain.pem:/etc/nginx/ssl/fullchain.pem:ro
      - /etc/letsencrypt/live/yourdomain.com/privkey.pem:/etc/nginx/ssl/privkey.pem:ro
    # Or use Docker secrets
    secrets:
      - ssl_cert
      - ssl_key

secrets:
  ssl_cert:
    external: true
  ssl_key:
    external: true
```
