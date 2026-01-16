# Fix Database URL Password Encoding Issue

## Problem

The ECS tasks are failing with this error:
```
ValueError: invalid interpolation syntax in 'postgresql+asyncpg://fastship:SE*KL>_z2&|rQwpw^9I1K%GBX>&vX{pY@...' at position 51
```

**Root Cause**: The password contains `%` character, which Python ConfigParser (used by Alembic) interprets as interpolation syntax when passed via `DATABASE_URL` environment variable.

## Solution Applied ✅

Changed from using `DATABASE_URL` to individual `POSTGRES_*` environment variables:
- `POSTGRES_SERVER`
- `POSTGRES_PORT`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_DB`

The application's `DatabaseSettings` class (in `app/config.py`) will automatically construct the database URL from these individual settings, avoiding the interpolation issue.

## Next Step: Apply Terraform Changes

**Run this command**:

```bash
cd infrastructure/terraform/environments/dev
terraform apply -var-file=terraform.tfvars
```

This will:
1. Update ECS task definitions with new environment variables
2. Force a new deployment with corrected configuration
3. Tasks should start successfully

## After Applying

Wait 2-3 minutes for:
1. New tasks to start
2. Health checks to pass
3. ALB to mark targets as healthy

Then test:
```bash
curl http://fastship-dev-alb-1317868336.eu-west-1.elb.amazonaws.com/health
```

Expected response:
```json
{"status":"healthy","redis":"connected","service":"FastAPI Backend"}
```

## Verify Fix

Check ECS logs after applying:
```bash
aws logs tail /ecs/dev-api --follow --region eu-west-1 --profile fastship
```

**Look for**:
- ✅ "Starting application on port 8000..."
- ✅ "✅ Database connection successful"
- ✅ "✅ Redis connection successful"
- ❌ No "invalid interpolation syntax" errors

## Why This Works

The `DatabaseSettings.POSTGRES_URL` property (in `app/config.py` lines 44-65) checks if `DATABASE_URL` is set first. If not, it constructs the URL from individual `POSTGRES_*` settings, which avoids the ConfigParser interpolation issue entirely.
