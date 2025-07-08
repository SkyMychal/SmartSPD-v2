# SmartSPD v2 Production Deployment Guide

## Overview

This guide covers deploying SmartSPD v2 to production using Docker and Docker Compose. The deployment includes all necessary services: PostgreSQL, Redis, Neo4j, FastAPI backend, Next.js frontend, and Nginx reverse proxy.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM
- 20GB+ available disk space
- Domain name (for SSL/HTTPS)

## Quick Start

1. **Clone and prepare environment:**
   ```bash
   git clone <repository>
   cd SmartSPD-v2
   cp .env.production .env.prod
   ```

2. **Configure environment variables in `.env.prod`:**
   ```bash
   # Required configurations
   POSTGRES_PASSWORD=your_secure_postgres_password
   NEO4J_PASSWORD=your_secure_neo4j_password
   SECRET_KEY=your_very_secure_secret_key
   OPENAI_API_KEY=your_openai_api_key
   PINECONE_API_KEY=your_pinecone_api_key
   ```

3. **Deploy the application:**
   ```bash
   ./scripts/deploy.sh
   ```

## Detailed Configuration

### Environment Variables

#### Required Settings
- `POSTGRES_PASSWORD`: Secure password for PostgreSQL
- `NEO4J_PASSWORD`: Secure password for Neo4j
- `SECRET_KEY`: JWT secret key (generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- `OPENAI_API_KEY`: OpenAI API key for AI features
- `PINECONE_API_KEY`: Pinecone API key for vector search

#### Optional Settings
- `AUTH0_*`: Auth0 configuration for authentication
- `SENTRY_DSN`: Error tracking with Sentry
- `AWS_*`: S3 configuration for backups
- `SSL_*`: SSL certificate paths

### SSL/HTTPS Configuration

1. **Obtain SSL certificates** (Let's Encrypt recommended):
   ```bash
   # Using Certbot
   sudo certbot certonly --standalone -d your-domain.com
   ```

2. **Update nginx configuration:**
   - Uncomment HTTPS server block in `docker/nginx/conf.d/default.conf`
   - Update SSL certificate paths
   - Enable HTTP to HTTPS redirect

3. **Place certificates:**
   ```bash
   mkdir -p docker/nginx/ssl
   cp /etc/letsencrypt/live/your-domain.com/fullchain.pem docker/nginx/ssl/cert.pem
   cp /etc/letsencrypt/live/your-domain.com/privkey.pem docker/nginx/ssl/key.pem
   ```

## Deployment Scripts

### Main Deployment Script

```bash
./scripts/deploy.sh [options]

Options:
  (no args)    - Full deployment with backup
  --no-backup  - Deploy without creating backup
  backup       - Create backup only
  build        - Build images only
  deploy       - Deploy services only
  health       - Run health checks only
  status       - Show deployment status
  cleanup      - Clean up old Docker images
```

### Backup Script

```bash
./scripts/backup.sh [options]

Options:
  (no args)  - Full system backup
  database   - Database backup only
  files      - Files backup only
  config     - Configuration backup only
  cleanup    - Clean up old backups
```

## Service Architecture

### Services Overview

- **nginx**: Reverse proxy and load balancer (ports 80, 443)
- **frontend**: Next.js application (internal port 3000)
- **backend**: FastAPI application (internal port 8000)
- **postgres**: PostgreSQL database (port 5432)
- **redis**: Cache and session store (port 6379)
- **neo4j**: Knowledge graph database (ports 7474, 7687)

### Service Dependencies

```
nginx → frontend → backend → postgres
                          → redis
                          → neo4j (optional)
```

### Health Checks

All services include health checks with automatic restart policies:
- **Backend**: `GET /api/v1/health`
- **Frontend**: `GET /api/health`
- **PostgreSQL**: `pg_isready`
- **Redis**: `redis-cli ping`
- **Neo4j**: HTTP endpoint check

## Monitoring and Maintenance

### Log Management

View service logs:
```bash
# All services
docker-compose -f docker-compose.prod.yml logs -f

# Specific service
docker-compose -f docker-compose.prod.yml logs -f backend
```

Log rotation is configured automatically with:
- Maximum file size: 10MB
- Maximum files: 3-5 per service

### Health Monitoring

Check service status:
```bash
docker-compose -f docker-compose.prod.yml ps
```

Health check endpoints:
- Application: `http://your-domain/health`
- Backend API: `http://your-domain/api/v1/health`
- Frontend: `http://your-domain/api/health`

### Database Maintenance

#### PostgreSQL
```bash
# Connect to database
docker-compose -f docker-compose.prod.yml exec postgres psql -U smartspd_user -d smartspd

# Run vacuum
docker-compose -f docker-compose.prod.yml exec postgres psql -U smartspd_user -d smartspd -c "VACUUM ANALYZE;"
```

#### Redis
```bash
# Connect to Redis
docker-compose -f docker-compose.prod.yml exec redis redis-cli

# Check memory usage
docker-compose -f docker-compose.prod.yml exec redis redis-cli info memory
```

#### Neo4j
```bash
# Connect to Neo4j
docker-compose -f docker-compose.prod.yml exec neo4j cypher-shell -u neo4j -p your_password
```

## Backup and Recovery

### Automated Backups

Configure automated daily backups with cron:
```bash
# Add to crontab
0 2 * * * /path/to/SmartSPD-v2/scripts/backup.sh
```

### Manual Backup

```bash
./scripts/backup.sh
```

Backups include:
- PostgreSQL database (custom format + SQL dump)
- Redis data (RDB file)
- Neo4j data (Cypher export)
- Uploaded files
- Application logs
- Configuration files

### Recovery Process

1. **Stop services:**
   ```bash
   docker-compose -f docker-compose.prod.yml down
   ```

2. **Restore database:**
   ```bash
   # Extract backup
   tar xzf backups/TIMESTAMP.tar.gz
   
   # Restore PostgreSQL
   docker-compose -f docker-compose.prod.yml up -d postgres
   docker-compose -f docker-compose.prod.yml exec postgres pg_restore -U smartspd_user -d smartspd < TIMESTAMP/database.backup
   ```

3. **Restore files:**
   ```bash
   # Restore uploads
   docker run --rm -v smartspd-v2_uploads_data:/uploads -v "$PWD/TIMESTAMP":/backup ubuntu tar xzf /backup/uploads.tar.gz -C /uploads
   ```

4. **Restart services:**
   ```bash
   ./scripts/deploy.sh --no-backup
   ```

## Security Considerations

### Network Security
- All services run in isolated Docker network
- Only nginx exposes ports to host
- Internal communication uses service names

### Data Security
- Passwords stored in environment variables
- JWT tokens for API authentication
- File upload restrictions and validation
- SQL injection protection with SQLAlchemy ORM

### SSL/TLS
- HTTPS encryption in production
- Secure headers configured in nginx
- HSTS enabled for browser security

## Performance Tuning

### PostgreSQL Optimization
- Configured for 4GB RAM (adjust in `docker/postgres/postgresql.conf`)
- Connection pooling enabled
- Query logging for slow queries (>1s)

### Redis Optimization
- Memory limit: 256MB (adjust based on usage)
- LRU eviction policy
- AOF persistence enabled

### Nginx Optimization
- Gzip compression enabled
- Rate limiting configured
- Keep-alive connections
- Static file caching

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service logs
docker-compose -f docker-compose.prod.yml logs service_name

# Check resource usage
docker stats
```

#### Database Connection Issues
```bash
# Verify database is running
docker-compose -f docker-compose.prod.yml ps postgres

# Test connection
docker-compose -f docker-compose.prod.yml exec backend python -c "from app.core.database import engine; print(engine.execute('SELECT 1').scalar())"
```

#### High Memory Usage
```bash
# Check memory usage
docker stats --no-stream

# Adjust service limits in docker-compose.prod.yml
```

### Log Locations

- Application logs: `/app/logs` (in backend container)
- Nginx logs: `docker/nginx/logs`
- PostgreSQL logs: Container logs via `docker-compose logs postgres`
- System logs: `journalctl -u docker`

## Scaling and Load Balancing

### Horizontal Scaling

To scale backend services:
```bash
docker-compose -f docker-compose.prod.yml up -d --scale backend=3
```

Update nginx upstream configuration for load balancing.

### Vertical Scaling

Adjust resource limits in `docker-compose.prod.yml`:
```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
```

## Maintenance Windows

### Rolling Updates

1. Build new images
2. Update one service at a time
3. Verify health checks pass
4. Continue with next service

### Zero-Downtime Deployment

1. Deploy to staging environment
2. Run full test suite
3. Use blue-green deployment strategy
4. Switch traffic with load balancer

## Support and Monitoring

### Metrics Collection

Enable monitoring in `.env.prod`:
```bash
ENABLE_MONITORING=true
```

### Error Tracking

Configure Sentry for error tracking:
```bash
SENTRY_DSN=your_sentry_dsn_here
```

### Alerting

Set up monitoring alerts for:
- Service health check failures
- High resource usage
- Database connection issues
- Error rate thresholds

For additional support, consult the application logs and health check endpoints.