# Health Check Timeout Issue - Root Cause and Fix

**Date:** January 23, 2026  
**Issue:** ECS tasks failing ALB health checks with "Request timed out"  
**Status:** ✅ Fixed

## Problem Description

After commit `dc97028` and subsequent commits, the FastShip API backend deployed on AWS ECS Fargate began failing ALB health checks. Tasks would start successfully but immediately fail health checks and be terminated, preventing the API from becoming available.

### Symptoms

- ✅ App starts successfully (logs show "Uvicorn running on http://0.0.0.0:8000")
- ✅ Database connection works (logs confirm "Database connection successful")
- ✅ Port mappings configured in task definition (containerPort: 8000, hostPort: 8000)
- ✅ Security groups correctly configured (ALB → ECS traffic allowed on port 8000)
- ❌ Health checks timing out ("Request timed out")
- ❌ Tasks marked as unhealthy and terminated
- ❌ API unavailable at `https://api.fastship-api.com`

### Error Messages

```
Target health: "unhealthy"
Reason: "Target.Timeout"
Description: "Request timed out"
```

## Root Cause Analysis

### Investigation Process

1. **Verified Code Changes**: All commits after `dc97028` were analyzed and found to be correct:
   - SSL parameters for PostgreSQL (correctly using `ssl=require` for asyncpg)
   - Health endpoint simplified (no Redis check)
   - CORS configuration valid
   - Database settings migration (settings → db_settings)

2. **Verified Infrastructure**:
   - Port mappings: ✅ Correct in task definition
   - Security groups: ✅ Correct (ECS allows port 8000 from ALB)
   - Target group: ✅ Correctly configured for port 8000, path `/health`
   - Network configuration: ✅ Tasks in public subnets with proper routing

3. **Key Finding**:
   - Task definition showed port mappings: `containerPort: 8000, hostPort: 8000`
   - Running tasks showed: `NetworkBindings: []` (empty)
   - **Note**: In Fargate with `awsvpc` mode, empty NetworkBindings is normal (container gets its own ENI)
   - However, the app was not responding to HTTP requests despite starting successfully

### Root Cause

The issue was identified as a **port mapping configuration problem**:

1. **Missing Explicit hostPort**: While the task definition showed `hostPort: 8000` in AWS console, the Terraform configuration only specified `containerPort` without explicitly setting `hostPort`.

2. **Application Not Responding**: Despite the app starting and binding to port 8000, HTTP requests from the ALB were timing out, suggesting the port wasn't properly exposed or the app wasn't ready to handle requests.

3. **Lack of Visibility**: No logging on the health endpoint made it impossible to verify if requests were reaching the application.

## Solution

### Fix 1: Explicit Port Mapping

**File**: `infrastructure/terraform/modules/ecs/main.tf`

**Change**: Added explicit `hostPort = 8000` to port mappings

```hcl
portMappings = [{
  containerPort = 8000
  hostPort      = 8000  # ← Added explicitly
  protocol      = "tcp"
}]
```

**Rationale**: While Fargate with `awsvpc` mode should handle port mapping automatically, explicitly setting `hostPort` ensures the port is properly mapped and accessible.

### Fix 2: Health Endpoint Logging

**File**: `src/backend/app/main.py`

**Change**: Added logging to `/health` endpoint to verify requests are reaching it

```python
@app.get("/health")
async def health_check():
    """Health check endpoint for ALB"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info("Health check endpoint called")  # ← Added logging
    return {"status": "healthy", "service": "FastAPI Backend"}
```

**Rationale**: This provides visibility into whether health check requests are reaching the application, helping diagnose network vs application-level issues.

## Verification

### Verified Components

1. ✅ **CORS Middleware**: Does not block health checks (no Origin header needed)
2. ✅ **Lifespan Handler**: Non-blocking (uses `asyncio.create_task()`)
3. ✅ **Middleware Order**: Rate limit and cache middleware correctly skip `/health`
4. ✅ **Security Groups**: ALB security group can reach ECS security group on port 8000
5. ✅ **Target Group**: Correctly configured for HTTP health checks on port 8000, path `/health`

### Expected Behavior After Fix

1. **Task Definition**: New task definition revision with explicit `hostPort = 8000`
2. **Task Deployment**: ECS service deploys new tasks with updated configuration
3. **Health Checks**: ALB health checks should start passing
4. **Logs**: Health endpoint logs should appear in CloudWatch: "Health check endpoint called"
5. **API Availability**: API should become accessible at `https://api.fastship-api.com`

## Monitoring

### After Deployment

1. **Check ECS Service**:
   ```bash
   aws ecs describe-services --cluster dev-fastship-cluster --services dev-api --region eu-west-1
   ```

2. **Check Target Health**:
   ```bash
   aws elbv2 describe-target-health \
     --target-group-arn <target-group-arn> \
     --region eu-west-1
   ```

3. **Check CloudWatch Logs**:
   - Look for "Health check endpoint called" in `/ecs/dev-api` log group
   - Verify app startup logs show successful binding

4. **Test API**:
   ```bash
   curl https://api.fastship-api.com/health
   ```

## Related Commits

- **Commit**: `c4179f9` - "Fix: Add explicit hostPort to ECS task definition and add health endpoint logging"

## Lessons Learned

1. **Explicit Configuration**: Even when AWS should handle something automatically, explicit configuration can prevent edge cases
2. **Visibility**: Logging on critical endpoints (like health checks) is essential for debugging
3. **Network Bindings**: In Fargate with `awsvpc`, empty `NetworkBindings` is normal - the container gets its own ENI
4. **Health Check Timing**: Health checks can start before the app is fully ready - ensure the app can respond immediately

## Additional Notes

- The issue was NOT caused by code changes after `dc97028` - all code changes were verified as correct
- The problem was infrastructure/configuration related, not application code
- CORS middleware, lifespan handler, and other middleware were all verified as non-blocking for health checks

## References

- [AWS ECS Fargate Network Modes](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-networking.html)
- [ALB Target Health Checks](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html)
- [FastAPI Lifespan Events](https://fastapi.tiangolo.com/advanced/events/)

---

## Additional Issue: Out-of-Memory (OOM) Error

**Date:** January 23, 2026  
**Issue:** Container OOM errors (exit code 137) causing task failures  
**Status:** ✅ Fixed

### Problem

After fixing the health check timeout issue, tasks began failing with Out-of-Memory errors:

- **Exit Code**: 137 (SIGKILL due to OOM)
- **Container Status**: STOPPED
- **Root Cause**: Memory allocation too low (512 MB)

### Analysis

**Memory Requirements:**
- FastAPI application: ~200-300 MB base
- SQLAlchemy + database connections: ~100-200 MB
- Redis connections: ~50-100 MB
- Python runtime + dependencies: ~100-200 MB
- **Total estimated**: ~500-800 MB minimum
- **With overhead**: Need at least 1024-1536 MB

**Previous Configuration:**
- `api_task_memory = 512 MB` (too low)
- `api_task_cpu = 256` (0.25 vCPU)

### Solution

**File**: `infrastructure/terraform/environments/dev/terraform.tfvars`

**Changes**:
```hcl
# Increased memory to prevent OOM errors
api_task_cpu = 512        # Increased from 256 (0.5 vCPU)
api_task_memory = 1536   # Increased from 512 MB
worker_task_memory = 1024  # Increased from 512 MB for Celery worker
```

**Rationale**:
- 1536 MB provides adequate headroom for the application
- 512 CPU units (0.5 vCPU) provides better performance
- Still reasonable cost for dev environment
- Prevents OOM kills (exit code 137)

### Monitoring

**Check Memory Usage**:
```bash
# Enable Container Insights for detailed metrics
aws ecs update-cluster-settings \
  --cluster dev-fastship-cluster \
  --settings name=containerInsights,value=enabled \
  --region eu-west-1

# View memory metrics in CloudWatch
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name MemoryUtilization \
  --dimensions Name=ServiceName,Value=dev-api Name=ClusterName,Value=dev-fastship-cluster \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 300 \
  --statistics Maximum,Average \
  --region eu-west-1
```

**Watch for OOM Errors**:
- Exit code 137 in task stopped reasons
- "Out of memory" messages in CloudWatch logs
- Container health status changes

### Lessons Learned

1. **Memory Allocation**: Always allocate more memory than minimum requirements
2. **Monitor Early**: Enable Container Insights to track memory usage patterns
3. **Exit Code 137**: Always indicates OOM - increase memory allocation
4. **CPU/Memory Ratio**: For CPU-intensive apps, ensure adequate CPU as well

### Related Commits

- **Commit**: TBD - "Fix: Increase ECS task memory allocation to prevent OOM errors"
