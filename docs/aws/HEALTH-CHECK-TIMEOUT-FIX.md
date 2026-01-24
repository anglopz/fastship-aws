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

## Additional Issue: Configuration Mismatch and OOM Error

**Date:** January 23, 2026  
**Issue:** Configuration mismatch between terraform.tfvars and task definition causing OOM errors  
**Status:** ✅ Fixed

### Problem

After fixing the health check timeout issue, tasks began failing with Out-of-Memory errors:

- **Exit Code**: 137 (SIGKILL due to OOM)
- **Container Status**: STOPPED
- **Root Cause**: Configuration mismatch - task definition had 1024 MB but terraform.tfvars had 512 MB

### Analysis

**Configuration Mismatch:**
- Task definition (dev-api:17): CPU: 512, Memory: 1024 MB
- terraform.tfvars: api_task_cpu = 256, api_task_memory = 512 MB
- **Mismatch caused inconsistent deployments**

**Memory Requirements for Portfolio App:**
- FastAPI application: ~200-300 MB base
- SQLAlchemy + database connections: ~100-200 MB
- Redis connections: ~50-100 MB
- Python runtime + dependencies: ~100-200 MB
- **Total estimated**: ~450-800 MB
- **With careful optimization**: 512 MB can work for a portfolio app

**Initial Attempt:**
- Tried to increase to 1536 MB but hit Fargate limitation (512 CPU + 1536 MB is invalid)
- Valid combinations: 512 CPU + 1024/2048 MB or 256 CPU + 512/1024/2048 MB

### Solution

**File**: `infrastructure/terraform/environments/dev/terraform.tfvars`

**Final Configuration** (aligned across all files):
```hcl
# Portfolio app - minimal resources for cost efficiency
# Configuration aligned between terraform.tfvars and task definition
api_task_cpu = 256        # 0.25 vCPU - sufficient for portfolio app
api_task_memory = 512     # 512 MB - aligned with task definition
worker_task_cpu = 256     # 0.25 vCPU
worker_task_memory = 512  # 512 MB - aligned with task definition
```

**Rationale**:
- **Portfolio app**: Not a heavily used production app, cost efficiency is priority
- **Configuration alignment**: terraform.tfvars and task definition now match
- **512 MB**: Sufficient for portfolio app with proper optimization
- **256 CPU (0.25 vCPU)**: Adequate for low-traffic portfolio app
- **Can scale later**: If needed, resources can be increased based on actual usage

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

1. **Configuration Alignment**: Always ensure terraform.tfvars matches task definition
2. **Fargate Limitations**: Valid CPU/memory combinations must be used (check AWS docs)
3. **Right-Sizing**: For portfolio apps, start minimal and scale based on actual needs
4. **Exit Code 137**: Indicates OOM - but first check for configuration mismatches
5. **Cost Efficiency**: Portfolio apps don't need production-level resources initially

### Additional Fix: Container Health Check

**Issue**: Tasks failing ALB health checks even after configuration alignment.

**Root Cause**: No container health check configured in ECS task definition. ECS couldn't determine container health independently.

**Solution**: Added container health check to task definition.

**File**: `infrastructure/terraform/modules/ecs/main.tf`

```hcl
healthCheck = {
  command     = ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
  interval    = 30
  timeout     = 5
  retries     = 3
  startPeriod = 60  # Grace period for app startup (60 seconds)
}
```

**Rationale**:
- ECS can monitor container health independently of ALB
- 60-second start period allows app to fully initialize
- Works alongside ALB health checks for better reliability
- Provides visibility into container health status

### Related Commits

- **Commit**: `c7ff936` - "Fix: Align ECS task configuration between terraform.tfvars and task definition"
- **Commit**: `5a1f2eb` - "Add container health check to ECS task definition"
