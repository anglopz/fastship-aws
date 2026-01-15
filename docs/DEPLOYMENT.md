# FastShip API - Deployment Guide

## Overview

This guide covers deploying the FastShip API to production environments.

## Prerequisites

- Docker & Docker Compose installed
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)
- Domain name (optional, for production)
- SSL certificate (for HTTPS in production)

## Environment Setup

### 1. Environment Variables

Create a `.env` file based on `env.example`:

```bash
# Security
JWT_SECRET=your-very-secure-secret-key-change-in-production
JWT_ALGORITHM=HS256

# Database
POSTGRES_SERVER=db
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-secure-password
POSTGRES_DB=fastapi_db

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_URL=redis://redis:6379

# Email Configuration
EMAIL_MODE=sandbox  # "sandbox" for Mailtrap testing, "production" for real SMTP

# Production SMTP (used when EMAIL_MODE=production)
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_FROM=noreply@fastship.com
MAIL_PORT=587
MAIL_SERVER=smtp.gmail.com
MAIL_FROM_NAME=FastShip
MAIL_STARTTLS=true
MAIL_SSL_TLS=false
USE_CREDENTIALS=true
VALIDATE_CERTS=true

# Mailtrap (used when EMAIL_MODE=sandbox)
MAILTRAP_USERNAME=your-mailtrap-username
MAILTRAP_PASSWORD=your-mailtrap-password
MAILTRAP_SERVER=sandbox.smtp.mailtrap.io
MAILTRAP_PORT=587

# SMS (Twilio)
TWILIO_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_NUMBER=+1234567890
```

### 2. Production Secrets

**Important**: Never commit `.env` files to version control!

- Use strong, unique `JWT_SECRET`
- Use secure database passwords
- Use production SMTP credentials
- Use production Twilio credentials

## Docker Deployment

### Quick Start

```bash
# Clone repository
git clone <repository-url>
cd app

# Copy environment file
cp env.example .env
# Edit .env with production values

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f api

# Verify health
curl http://localhost:8000/health
```

### Production Docker Compose

For production, consider:

1. **Remove volume mounts** (use built images)
2. **Set restart policies**: `restart: always`
3. **Configure resource limits**
4. **Use Docker secrets** for sensitive data
5. **Enable health checks**

Example production `docker-compose.prod.yml`:

```yaml
services:
  api:
    build: .
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 1G
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    # Remove volumes in production
    # volumes:
    #   - .:/code
```

## Database Setup

### Initial Migration

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Or tables auto-create on startup (via lifespan_handler)
```

### Database Backup

```bash
# Backup
docker-compose exec db pg_dump -U postgres fastapi_db > backup.sql

# Restore
docker-compose exec -T db psql -U postgres fastapi_db < backup.sql
```

## Redis Setup

### Redis Persistence

Redis data is persisted in Docker volume `redis_data`.

### Redis Configuration

For production, configure Redis persistence:

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --appendonly yes
  volumes:
    - redis_data:/data
```

## Reverse Proxy (Nginx)

### Nginx Configuration

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name api.fastship.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### SSL/HTTPS

Use Let's Encrypt with Certbot:

```bash
sudo certbot --nginx -d api.fastship.com
```

## Monitoring

### Health Checks

- **API Health**: `GET /health`
- **Email Health**: `GET /health/email` - Verify SMTP connection
- **Database**: PostgreSQL health check in Docker
- **Redis**: Connection check in application

### Logging

Logs are stored in `logs/` directory:
- Request logs via Celery
- Application logs
- Error logs

### Monitoring Tools

Consider integrating:
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **Sentry**: Error tracking
- **Datadog**: APM

## Scaling

### Horizontal Scaling

1. **API**: Run multiple API containers behind load balancer
2. **Celery Workers**: Scale workers based on task volume
3. **Database**: Use read replicas for read-heavy workloads
4. **Redis**: Use Redis Cluster for high availability

### Load Balancer

Use Nginx or cloud load balancer:

```nginx
upstream api_backend {
    least_conn;
    server api1:8000;
    server api2:8000;
    server api3:8000;
}
```

## Security Checklist

- [ ] Strong JWT secret
- [ ] Secure database passwords
- [ ] HTTPS enabled
- [ ] Environment variables secured
- [ ] Database backups configured
- [ ] Rate limiting enabled (if applicable)
- [ ] CORS configured (if needed)
- [ ] Security headers set
- [ ] Regular dependency updates
- [ ] Log monitoring enabled

## Backup Strategy

### Database Backups

```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
docker-compose exec -T db pg_dump -U postgres fastapi_db | gzip > backups/db_$DATE.sql.gz
```

### Redis Backups

Redis data is in Docker volume. Backup the volume:

```bash
docker run --rm -v app_redis_data:/data -v $(pwd)/backups:/backup \
  alpine tar czf /backup/redis_$(date +%Y%m%d).tar.gz /data
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check `POSTGRES_*` environment variables
   - Verify database container is running
   - Check network connectivity

2. **Redis Connection Failed**
   - Check `REDIS_*` environment variables
   - Verify Redis container is running
   - Check Redis logs

3. **Celery Tasks Not Running**
   - Verify Celery worker container is running
   - Check Celery logs
   - Verify Redis connection

4. **Email Not Sending**
   - Check SMTP credentials
   - Verify EMAIL_MODE setting (sandbox vs production)
   - Verify email settings match EMAIL_MODE
   - Test connection: `GET /health/email`
   - Check Celery worker logs

### Debug Mode

For debugging, enable verbose logging:

```bash
# In docker-compose.yml
environment:
  - LOG_LEVEL=DEBUG
```

## Production Checklist

- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL/HTTPS configured
- [ ] Monitoring set up
- [ ] Backups configured
- [ ] Health checks passing
- [ ] Logging configured
- [ ] Security measures in place
- [ ] Performance tested
- [ ] Documentation updated

## Email Configuration

### EMAIL_MODE Setting

The application supports two email modes controlled by the `EMAIL_MODE` environment variable:

#### Sandbox Mode (Testing)
```bash
EMAIL_MODE=sandbox
MAILTRAP_USERNAME=your-mailtrap-username
MAILTRAP_PASSWORD=your-mailtrap-password
MAILTRAP_SERVER=sandbox.smtp.mailtrap.io
MAILTRAP_PORT=587
```

- Uses Mailtrap for email testing
- Emails are captured in Mailtrap inbox, not actually sent
- Perfect for development and testing
- No risk of sending test emails to real users

#### Production Mode
```bash
EMAIL_MODE=production
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
```

- Uses real SMTP server
- Emails are actually sent to recipients
- Use for production deployments
- Requires valid SMTP credentials

### Verifying Email Configuration

Test your email configuration using the health endpoint:

```bash
curl http://localhost:8000/health/email
```

**Success Response:**
```json
{
  "status": "success",
  "message": "SMTP connection verified",
  "mode": "sandbox",
  "server": "sandbox.smtp.mailtrap.io",
  "port": 587,
  "username": "020***"
}
```

**Error Response:**
```json
{
  "status": "error",
  "message": "SMTP connection failed: Authentication failed",
  "mode": "production",
  "server": "smtp.gmail.com",
  "port": 587
}
```

## Render Deployment

### Prerequisites

- Render account (https://render.com)
- GitHub repository with your code
- PostgreSQL database (Render PostgreSQL service)
- Redis instance (Render Redis service)

### Step 1: Create Services on Render

1. **PostgreSQL Database**
   - Create new PostgreSQL service
   - Note the internal database URL
   - Set as `DATABASE_URL` environment variable

2. **Redis Instance**
   - Create new Redis service
   - Note the internal Redis URL
   - Set as `REDIS_URL` environment variable

3. **Web Service (API)**
   - Create new Web Service
   - Connect to your GitHub repository
   - Use `render.yaml` configuration (or manual setup)

### Step 2: Configure Environment Variables

Set the following environment variables in Render dashboard:

**Required:**
```bash
DATABASE_URL=<from-postgres-service>
REDIS_URL=<from-redis-service>
JWT_SECRET=<generate-secure-random-string>
EMAIL_MODE=production
MAIL_USERNAME=<your-smtp-username>
MAIL_PASSWORD=<your-smtp-password>
MAIL_SERVER=<your-smtp-server>
MAIL_FROM=noreply@fastship.com
FRONTEND_URL=<your-frontend-url>
APP_DOMAIN=<your-api-domain>
```

**Optional:**
```bash
TWILIO_SID=<your-twilio-sid>
TWILIO_AUTH_TOKEN=<your-twilio-token>
TWILIO_NUMBER=<your-twilio-number>
CORS_ORIGINS=<comma-separated-origins>
```

### Step 3: Build Configuration

**Build Command:**
```bash
pip install -r requirements.txt
```

**Start Command:**
```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### Step 4: Deploy

1. Push your code to GitHub
2. Render will automatically detect changes and deploy
3. Monitor deployment logs
4. Verify health: `GET https://your-api.onrender.com/health/email`

### Step 5: Background Workers (Celery)

For Celery workers, create a separate Background Worker service:

**Start Command:**
```bash
celery -A app.celery_app worker --loglevel=info
```

**Environment Variables:**
- Same as Web Service
- Ensure `REDIS_URL` points to same Redis instance

### Render-Specific Considerations

1. **Database Migrations**
   - Run migrations on first deploy
   - Use Render shell or add to startup script

2. **Health Checks**
   - Render uses `/health` endpoint
   - Ensure health endpoints are working

3. **Auto-Deploy**
   - Enable auto-deploy on git push
   - Or use manual deploys for production

4. **Scaling**
   - Render supports horizontal scaling
   - Use load balancer for multiple instances

5. **Environment Variables**
   - Use Render's environment variable management
   - Mark sensitive variables as "Secret"

---

**Last Updated**: January 13, 2026

