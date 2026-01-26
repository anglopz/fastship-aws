# FastShip AWS Deployment - Complete Debugging Guide

## Executive Summary

This document chronicles the complete debugging journey of the FastShip API deployment on AWS ECS Fargate, from initial health check failures to final resolution. It covers root causes, solutions, local development setup, and lessons learned.

**Final Status:** ✅ **RESOLVED** - Health endpoint now responds immediately, task is healthy, service is operational.

---

## Table of Contents

1. [Problem Overview](#problem-overview)
2. [Root Cause Analysis](#root-cause-analysis)
3. [Solution Implementation](#solution-implementation)
4. [Local Development Setup](#local-development-setup)
5. [Errors Encountered](#errors-encountered)
6. [Lessons Learned](#lessons-learned)
7. [Prevention Strategies](#prevention-strategies)

---

## Problem Overview

### Initial Symptoms

- **API tasks failing ALB health checks** with "Request timed out"
- Tasks showing as **UNHEALTHY** in target group
- Deployment stagnation - new tasks couldn't pass health checks
- Service returning **503 Service Temporarily Unavailable**

### Timeline of Issues

1. **Phase 1:** Network/Configuration Issues
   - Tasks in private subnets without internet access
   - Incorrect Docker image tags
   - Database SSL configuration problems

2. **Phase 2:** Resource Constraints
   - Out-of-Memory (OOM) errors (exit code 137)
   - CPU/Memory mismatches in Fargate configuration

3. **Phase 3:** Application-Level Blocking (ROOT CAUSE)
   - Health endpoint requests hanging indefinitely
   - Application not responding despite being "running"
   - Celery middleware blocking HTTP requests

---

## Root Cause Analysis

### Primary Root Cause: Celery Middleware Blocking

**The Problem:**
The `request_logging_middleware` in `src/backend/app/core/middleware.py` was blocking HTTP requests, particularly health check requests, due to:

1. **Synchronous Celery Import:**
   - Celery was imported at module load time
   - If Redis was slow or unavailable, the import could hang
   - This blocked the entire middleware initialization

2. **Blocking Celery Task Calls:**
   - `log_request_task.delay()` was used for logging
   - Even though it's "async", it can block if Redis connection is slow
   - Health endpoint requests were waiting for Celery/Redis operations

3. **No Timeout or Fallback:**
   - No timeout mechanism for Celery operations
   - No early return for health endpoints
   - Health checks should be fast and independent of external services

### Why Health Endpoints Were Affected

Health endpoints (`/health`) are critical for:
- ALB health checks (every 35 seconds)
- Container health checks (every 30 seconds)
- Service availability monitoring

When these endpoints hang:
- ALB marks target as unhealthy
- ECS stops the task
- Service becomes unavailable
- New deployments fail

### Secondary Issues (Resolved Earlier)

1. **Network Configuration:**
   - Tasks in private subnets without NAT Gateway
   - Solution: Use public subnets for API service (temporary)

2. **Resource Allocation:**
   - Insufficient CPU/Memory (256 CPU / 512 MB)
   - Solution: Increased to 512 CPU / 1024 MB

3. **Database SSL:**
   - PostgreSQL connection string missing SSL configuration
   - Solution: Added `ssl=require` for asyncpg compatibility

---

## Solution Implementation

### Fix 1: Skip Celery Logging for Health Endpoints

**File:** `src/backend/app/core/middleware.py`

**Change:**
```python
async def request_logging_middleware(request: Request, call_next) -> Response:
    # ... process request ...
    
    # CRITICAL: Skip Celery logging for health endpoints to prevent blocking
    # Health checks must be fast and not depend on external services
    is_health_endpoint = url.endswith('/health') or '/health' in url
    
    if is_health_endpoint:
        # For health endpoints, use minimal sync logging or skip entirely
        try:
            logger.info(f"Health check: {method} {url} ({status_code}) {time_taken}s")
        except Exception:
            pass  # Don't block health checks
        # Return early - no Celery logging for health checks
        return response
    
    # ... rest of logging logic for non-health endpoints ...
```

**Why This Works:**
- Health endpoints bypass all Celery/Redis operations
- Fast response guaranteed (< 100ms)
- No external dependencies
- Industry standard practice

### Fix 2: Lazy Celery Import with Silent Failure

**Change:**
```python
def _get_log_request_task():
    """Lazy import of Celery task to prevent blocking at module load time"""
    global CELERY_AVAILABLE, _log_request_task
    if _log_request_task is None:
        try:
            from app.celery_app import log_request_task
            _log_request_task = log_request_task
            CELERY_AVAILABLE = True
        except (ImportError, Exception) as e:
            CELERY_AVAILABLE = False
            # Silently fail - don't log to avoid blocking
            pass
    return _log_request_task
```

**Why This Works:**
- Import only happens when needed (lazy)
- Silent failure prevents blocking warnings
- Graceful fallback to sync logging

### Fix 3: Non-Blocking Async Logging

**Change:**
```python
# Use apply_async with ignore_result=True for true fire-and-forget
log_task.apply_async(
    args=[log_message],
    ignore_result=True,
    expires=300  # Expire task after 5 minutes if not processed
)
```

**Why This Works:**
- `apply_async` with `ignore_result=True` is truly fire-and-forget
- Doesn't wait for Redis response
- Task expiration prevents queue buildup

### Infrastructure Fixes

1. **Task Resources:**
   - Updated from 256 CPU / 512 MB to 512 CPU / 1024 MB
   - Prevents OOM errors and provides adequate resources

2. **Health Check Configuration:**
   - ALB timeout: 30s, interval: 35s
   - Container health check: timeout 10s, start period 120s
   - Service grace period: 300s

3. **ECS Exec Enabled:**
   - Added `enable_execute_command = true` to service
   - Added `AmazonSSMManagedInstanceCore` policy to task role
   - Enables direct container debugging

---

## Local Development Setup

### Overview

The local development environment allows you to:
- Test application code before deploying to AWS
- Debug issues locally without network complications
- Use IDE debugger with breakpoints
- See real-time logs in terminal
- Make code changes without Docker rebuilds

### Setup Instructions

#### 1. Create Virtual Environment

```bash
cd src/backend

# Option 1: Use Makefile (recommended)
make dev-setup

# Option 2: Use setup script
./dev/setup-venv.sh

# Option 3: Manual setup
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

#### 2. Configure Environment Variables

```bash
# Copy example file
cp .env.example .env

# Edit .env with your settings
# Key variables:
# - DATABASE_URL or POSTGRES_* variables
# - REDIS_URL or REDIS_* variables
# - JWT_SECRET
# - MAILTRAP_USERNAME and MAILTRAP_PASSWORD (for email testing)
```

#### 3. Start Docker Services

```bash
# Start database and Redis
docker-compose up -d db redis

# Or start everything (API, DB, Redis, Celery)
docker-compose up -d

# Check status
docker-compose ps
```

#### 4. Run Database Migrations

```bash
# Activate virtual environment first
source .venv/bin/activate

# Run migrations
make migrate
# OR
alembic upgrade head
```

#### 5. Start Development Server

```bash
# Option 1: Run locally (recommended for debugging)
make dev
# OR
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Option 2: Run in Docker
docker-compose up api
```

### Development Workflows

#### Workflow A: API Locally, Services in Docker (Recommended)

```bash
# Start only database and Redis in Docker
docker-compose up -d db redis celery_worker

# Run API locally with virtual environment
source .venv/bin/activate
uvicorn app.main:app --reload
```

**Benefits:**
- Use IDE debugger with breakpoints
- See real-time logs in terminal
- Make code changes without Docker rebuilds
- Test application-level issues without network complications

#### Workflow B: Everything in Docker

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Execute commands in container
docker-compose exec api bash
```

### Testing Locally

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test API docs
open http://localhost:8000/docs

# Test detailed health endpoint
curl http://localhost:8000/api/v1/health

# Run tests
make test
# OR
pytest
```

### Useful Commands

```bash
# View logs
docker-compose logs -f api
docker-compose logs -f celery_worker

# Restart a service
docker-compose restart api

# Stop services
docker-compose down

# Rebuild after code changes
docker-compose build api
docker-compose up -d api
```

### File Structure

```
src/backend/
├── dev/                          # Development-specific files
│   ├── setup-venv.sh            # Virtual environment setup
│   └── README.md                # Local development guide
├── docker-compose.yml           # Docker services configuration
├── Makefile                     # Development commands
├── .env.example                 # Environment variables template
├── .env                         # Your local environment (gitignored)
└── ... (application code)
```

---

## Errors Encountered

### Error 1: "Request timed out" - ALB Health Checks

**Symptom:**
- Tasks failing ALB health checks
- Target group showing unhealthy targets
- Service unavailable

**Root Cause:**
- Health endpoint hanging due to Celery middleware blocking

**Solution:**
- Skip Celery logging for health endpoints
- Early return in middleware for `/health` paths

### Error 2: Exit Code 137 - Out of Memory

**Symptom:**
- Tasks terminating with exit code 137
- Container killed by system

**Root Cause:**
- Insufficient memory allocation (512 MB)
- Memory spikes during startup

**Solution:**
- Increased memory to 1024 MB
- Increased CPU to 512 units

### Error 3: Empty NetworkBindings

**Symptom:**
- Container showing empty port bindings
- Port 8000 not accessible

**Root Cause:**
- Missing explicit `hostPort` in task definition
- Container not marked as essential

**Solution:**
- Added explicit `hostPort = 8000` in port mappings
- Set `essential = true` for container

### Error 4: Database Connection - "no encryption"

**Symptom:**
- Database connection errors
- "no pg_hba.conf entry for host ... no encryption"

**Root Cause:**
- RDS requires SSL, but connection string missing SSL parameter
- `asyncpg` uses `ssl=require` not `sslmode=require`

**Solution:**
- Updated `POSTGRES_URL` property to include `ssl=require`
- Convert `sslmode` to `ssl` for asyncpg compatibility

### Error 5: Celery Import Blocking

**Symptom:**
- Requests hanging indefinitely
- Health endpoint timing out
- Application not responding

**Root Cause:**
- Synchronous Celery import at module load
- Blocking Celery task calls
- No timeout or fallback

**Solution:**
- Lazy Celery import
- Skip Celery logging for health endpoints
- Non-blocking `apply_async` with `ignore_result=True`

### Error 6: ECS Exec TargetNotConnectedException

**Symptom:**
- Cannot connect to container via ECS Exec
- "TargetNotConnectedException" error

**Root Cause:**
- Missing IAM permissions on task role
- ECS Exec not enabled on service

**Solution:**
- Added `AmazonSSMManagedInstanceCore` policy to task role
- Set `enable_execute_command = true` on service

### Error 7: Fargate Configuration Mismatch

**Symptom:**
- "No Fargate configuration exists for given values: 512 CPU, 1536 memory"

**Root Cause:**
- Invalid CPU/Memory combination for Fargate
- Fargate has specific valid combinations

**Solution:**
- Use valid Fargate combinations (e.g., 512 CPU / 1024 MB)
- Check AWS documentation for valid combinations

---

## Lessons Learned

### 1. Health Endpoints Must Be Fast and Independent

**Lesson:**
Health endpoints should never depend on external services (Redis, Celery, etc.). They must respond immediately (< 1 second) to pass ALB health checks.

**Best Practice:**
- Skip all async logging for health endpoints
- Use minimal sync logging only
- Return early without external dependencies

### 2. Middleware Can Block Requests

**Lesson:**
Even "async" middleware can block if it waits for external services. Celery operations, even with `delay()`, can block if Redis is slow.

**Best Practice:**
- Use truly fire-and-forget patterns (`apply_async` with `ignore_result=True`)
- Implement timeouts and fallbacks
- Skip expensive operations for health checks

### 3. Lazy Imports Prevent Startup Blocking

**Lesson:**
Importing Celery at module load time can block application startup if Redis is unavailable.

**Best Practice:**
- Use lazy imports for optional dependencies
- Import only when needed
- Gracefully handle import failures

### 4. Local Development is Essential

**Lesson:**
Having a local development environment allows you to:
- Test fixes before deploying
- Debug application-level issues
- Verify changes work correctly

**Best Practice:**
- Set up local Docker Compose environment
- Use virtual environment for Python dependencies
- Test health endpoints locally before deploying

### 5. Resource Allocation Matters

**Lesson:**
Insufficient resources (CPU/Memory) can cause:
- OOM errors
- Slow startup
- Health check failures

**Best Practice:**
- Allocate adequate resources for startup
- Monitor resource usage
- Scale up if needed

### 6. ECS Exec is Invaluable for Debugging

**Lesson:**
Being able to connect directly to containers helps diagnose issues that logs don't reveal.

**Best Practice:**
- Enable ECS Exec for production debugging
- Add necessary IAM permissions
- Use it to test endpoints directly

### 7. Health Check Configuration is Critical

**Lesson:**
Proper health check configuration prevents premature task termination:
- Grace periods allow startup time
- Timeouts should be reasonable
- Intervals must be > timeouts

**Best Practice:**
- Set adequate grace periods (300s for service, 120s for container)
- Configure timeouts based on endpoint response time
- Ensure interval > timeout

---

## Prevention Strategies

### 1. Code-Level Prevention

**Health Endpoint Best Practices:**
```python
# ✅ GOOD: Fast, independent health endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}  # No external dependencies

# ❌ BAD: Health endpoint with external dependencies
@app.get("/health")
async def health_check():
    await redis.ping()  # Can block!
    await db.execute("SELECT 1")  # Can block!
    return {"status": "healthy"}
```

**Middleware Best Practices:**
```python
# ✅ GOOD: Skip expensive operations for health checks
if is_health_endpoint:
    return response  # Early return

# ✅ GOOD: Non-blocking async logging
task.apply_async(args=[log], ignore_result=True, expires=300)

# ❌ BAD: Blocking operations in middleware
log_task.delay(message)  # Can block!
```

### 2. Infrastructure Prevention

**Resource Allocation:**
- Start with adequate resources (512 CPU / 1024 MB minimum)
- Monitor usage and scale as needed
- Use Container Insights for monitoring

**Health Check Configuration:**
- Set appropriate grace periods
- Configure timeouts based on endpoint response time
- Ensure interval > timeout

**Network Configuration:**
- Ensure tasks can reach required services
- Use public subnets if NAT Gateway not available
- Configure security groups correctly

### 3. Testing Prevention

**Local Testing:**
- Test health endpoints locally before deploying
- Verify response times are fast (< 1 second)
- Test with Docker Compose to match production

**Integration Testing:**
- Test health endpoints in staging environment
- Monitor health check success rates
- Verify no blocking operations

### 4. Monitoring Prevention

**CloudWatch Metrics:**
- Monitor task health status
- Track health check success rates
- Alert on unhealthy targets

**Application Logs:**
- Log health endpoint calls
- Monitor response times
- Track any errors or timeouts

---

## Quick Reference

### Health Endpoint Fix Summary

**Problem:** Health endpoint hanging due to Celery middleware blocking

**Solution:**
1. Skip Celery logging for health endpoints (early return)
2. Lazy Celery import with silent failure
3. Non-blocking async logging with `apply_async` and `ignore_result=True`

**Files Changed:**
- `src/backend/app/core/middleware.py`

**Commit:** `2af9a9c` - "Fix: Skip Celery logging for health endpoints to prevent blocking"

### Local Development Quick Start

```bash
cd src/backend

# Setup
make dev-setup
cp .env.example .env

# Start services
make up

# Run migrations
make migrate

# Start dev server
make dev

# Test
curl http://localhost:8000/health
```

### AWS Deployment Checklist

- [ ] Task definition has correct resources (512 CPU / 1024 MB)
- [ ] Health endpoint responds quickly (< 1 second)
- [ ] Celery logging skipped for health endpoints
- [ ] ECS Exec enabled for debugging
- [ ] Health check grace periods configured
- [ ] ALB health check timeouts appropriate
- [ ] Security groups allow traffic on port 8000
- [ ] Database SSL configured correctly

---

## Conclusion

The health check timeout issue was caused by **Celery middleware blocking HTTP requests**, particularly health endpoint requests. The fix involved:

1. **Skipping Celery logging for health endpoints** - Ensures fast, independent responses
2. **Lazy Celery import** - Prevents startup blocking
3. **Non-blocking async logging** - Prevents request blocking

The local development environment setup is **completely separate** from the AWS deployment issues but is essential for:
- Testing fixes before deploying
- Debugging application-level issues
- Verifying changes work correctly

**Key Takeaway:** Health endpoints must be fast, independent, and never block on external services. This is critical for ALB health checks and service availability.

---

## Related Documentation

- [Health Check Timeout Fix](./HEALTH-CHECK-TIMEOUT-FIX.md) - Detailed technical documentation
- [Local Development Guide](../src/backend/dev/README.md) - Complete local setup guide
- [AWS Deployment Guide](./deployment-aws.md) - General deployment documentation

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-24  
**Status:** ✅ Production Stable
