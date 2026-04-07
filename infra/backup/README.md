# Database Backup Guide

## Quick Backup (Manual)

```bash
# Run backup using the backup script
PGPASSWORD=$DB_PASSWORD pg_dump -h localhost -U postgres -d ytprocessor -Fc -Z 6 > backup_$(date +%Y%m%d).sql.gz

# Or via docker:
docker-compose exec db pg_dump -U postgres -d ytprocessor -Fc -Z 6 > backup_$(date +%Y%m%d).sql.gz
```

## Automated Backups

### Option 1: Cron Container

Add to your production deployment:

```bash
docker-compose -f docker-compose.yml -f docker-compose.production.yml -f infra/backup/docker-compose.backup.yml up -d
```

### Option 2: External Cron Job

Set up a cron job on your host:

```bash
# Daily at 2 AM
0 2 * * * docker-compose exec -T db pg_dump -U postgres -d ytprocessor -Fc -Z 6 > /path/to/backups/ytprocessor_$(date +\%Y\%m\%d).sql.gz

# Keep last 30 days
0 3 * * * find /path/to/backups/ -name "ytprocessor_*.sql.gz" -mtime +30 -delete
```

### Option 3: Continuous Archiving with Point-in-Time Recovery

For production, enable PostgreSQL WAL archiving:

```bash
# In docker-compose.production.yml
db:
  command: >
    postgres
    -c wal_level=replica
    -c max_wal_senders=3
    -c archive_mode=on
    -c archive_command=' scp %p user@backup-server:/var/backups/wal/%f'
```

## Restore from Backup

```bash
# Restore to local database
pg_restore -h localhost -U postgres -d ytprocessor_restored backup_file.sql.gz

# Or via docker:
docker-compose exec -T db pg_restore -U postgres -d ytprocessor_restored /path/to/backup_file.sql.gz
```

## Backup Verification

Always verify your backups work:

```bash
# List backups
ls -la /path/to/backups/

# Check backup integrity
pg_restore --help > /dev/null && echo "pg_restore is working"

# Test restore to a different database
PGPASSWORD=$DB_PASSWORD pg_restore -h localhost -U postgres -d ytprocessor_test -c /path/to/backup_file.sql.gz
```
