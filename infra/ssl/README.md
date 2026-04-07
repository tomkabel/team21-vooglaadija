# SSL Certificates

This directory should contain:

- `fullchain.pem` - Full certificate chain
- `privkey.pem` - Private key

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

### Option 3: Commercial certificate
Purchase from a CA and place files here.

## Docker Production Deployment

```bash
# Copy certificates to this directory
cp /path/to/fullchain.pem .
cp /path/to/privkey.pem .

# Start with production config
docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d
```
