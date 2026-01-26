# FastShip Backend - Local Development Guide

This guide helps you set up a local development environment to test and debug the application before deploying to AWS.

**Location:** This file is in `src/backend/dev/` - development-specific documentation and scripts.

## Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Git

## Quick Start

### 1. Set Up Virtual Environment

```bash
cd src/backend

# Option 1: Use Makefile (recommended)
make dev-setup

# Option 2: Use setup script
chmod +x dev/setup-venv.sh
./dev/setup-venv.sh

# Option 3: Manual setup
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your local settings
# For Docker Compose, defaults should work
```

### 3. Start Docker Services (PostgreSQL & Redis)

```bash
# Start database and Redis
docker-compose up -d db redis

# Check services are running
docker-compose ps

# View logs
docker-compose logs -f db redis
```

### 4. Run Database Migrations

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Run migrations
alembic upgrade head
```

### 5. Start Development Server

```bash
# With auto-reload (recommended for development)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or without reload
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 6. Test the Application

```bash
# Health check
curl http://localhost:8000/health

# API docs
open http://localhost:8000/docs
```

## Development Workflows

### Option A: Run Everything in Docker

```bash
# Start all services (API, DB, Redis, Celery)
docker-compose up -d

# View logs
docker-compose logs -f api

# Execute commands in container
docker-compose exec api alembic upgrade head
docker-compose exec api python -c "from app.main import app; print('App loaded')"

# Stop services
docker-compose down
```

### Option B: Run API Locally, Services in Docker (Recommended for Debugging)

```bash
# Start only database and Redis
docker-compose up -d db redis celery_worker

# Run API locally with virtual environment
source .venv/bin/activate
uvicorn app.main:app --reload
```

This allows you to:
- Use your IDE debugger
- See real-time logs in terminal
- Make code changes without rebuilding Docker image
- Test application-level issues without network complications

## Testing

### Run Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health.py -v
```

### Test Health Endpoint

```bash
# Test root health endpoint
curl -v http://localhost:8000/health

# Test API health endpoint (includes Redis check)
curl -v http://localhost:8000/api/v1/health
```

## Debugging

### Check Application Logs

```bash
# If running in Docker
docker-compose logs -f api

# If running locally, logs appear in terminal
# Check logs/ directory for file logs
tail -f logs/file.log
```

### Debug Celery Tasks

```bash
# Start Celery worker (if not using Docker)
source .venv/bin/activate
celery -A app.celery_app worker --loglevel=info

# Monitor Celery tasks
celery -A app.celery_app inspect active
```

### Test Database Connection

```bash
# Python shell
source .venv/bin/activate
python3 -c "
import asyncio
from app.database.session import engine
from sqlalchemy import text

async def test():
    async with engine.begin() as conn:
        result = await conn.execute(text('SELECT 1'))
        print('✅ Database connection successful')
        print(result.fetchone())

asyncio.run(test())
"
```

### Test Redis Connection

```bash
# Python shell
source .venv/bin/activate
python3 -c "
import asyncio
from app.database.redis import get_redis

async def test():
    try:
        redis = await get_redis()
        await redis.ping()
        print('✅ Redis connection successful')
    except Exception as e:
        print(f'❌ Redis connection failed: {e}')

asyncio.run(test())
"
```

## Common Issues

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process or use different port
uvicorn app.main:app --reload --port 8001
```

### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker-compose ps db

# Check connection string
echo $DATABASE_URL

# Test connection manually
psql -h localhost -U postgres -d fastapi_db
```

### Redis Connection Failed

```bash
# Check if Redis is running
docker-compose ps redis

# Test Redis connection
redis-cli -h localhost ping
```

### Module Not Found Errors

```bash
# Make sure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check Python path
python3 -c "import sys; print(sys.path)"
```

## Environment Variables Reference

See `.env.example` for all available environment variables.

Key variables for local development:
- `DATABASE_URL` or `POSTGRES_*` - Database connection
- `REDIS_URL` or `REDIS_*` - Redis connection
- `JWT_SECRET` - Secret key for JWT tokens
- `EMAIL_MODE=sandbox` - Use Mailtrap for email testing
- `CORS_ORIGINS` - Allowed CORS origins

## Next Steps

1. **Test Health Endpoint**: Verify `/health` responds quickly
2. **Test API Endpoints**: Use `/docs` for interactive API testing
3. **Monitor Logs**: Watch for any errors or warnings
4. **Test Celery Tasks**: Trigger background tasks and verify they execute
5. **Debug Issues**: Use IDE debugger or print statements

## Troubleshooting AWS Deployment Issues Locally

If you encounter issues on AWS:

1. **Reproduce Locally**: Run the same code locally with Docker
2. **Check Logs**: Compare local logs with CloudWatch logs
3. **Test Dependencies**: Verify database and Redis connections work
4. **Test Health Endpoint**: Ensure `/health` responds quickly
5. **Check Memory**: Monitor memory usage locally
6. **Test Middleware**: Verify middleware doesn't block requests

This local setup mirrors the AWS environment, making it easier to debug application-level issues before deployment.
