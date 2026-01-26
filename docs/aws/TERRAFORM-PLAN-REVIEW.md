# Terraform Plan Review - CloudFront Import

## Plan Summary
- **CloudFront**: Minor settings updates (safe)
- **ECS**: Task definition replacements (will cause brief downtime)
- **RDS**: Password change (likely false positive)

## Changes Analysis

### ✅ CloudFront Distribution (Safe - No Downtime)
```
~ http_version: "http2and3" -> "http2"
~ price_class: "PriceClass_100" -> "PriceClass_All"
```

**Status**: These are minor configuration differences. The actual distribution has:
- `http2and3` (newer, supports HTTP/3)
- `PriceClass_100` (cheaper, covers US, Canada, Europe)

**Action**: Terraform configuration has been updated to match actual settings. After applying, these changes will disappear.

### ⚠️ ECS Task Definitions (Will Cause Brief Downtime)
```
-/+ task_definition.api: must be replaced
  ~ cpu: "512" -> "256"
  ~ memory: "1024" -> "512"
  ~ subnets: private -> public
```

**Status**: Task definitions will be replaced because:
- CPU/memory is being downgraded (512/1024 → 256/512) to match free tier settings
- Subnets changing from private to public (api_use_public_subnets = true)

**Impact**: 
- Brief service interruption during task replacement (~1-2 minutes)
- New tasks will start with lower resources (256 CPU, 512 MB memory)

**Recommendation**: 
- If API is currently working fine, you might want to keep current CPU/memory
- Or accept the brief downtime to align with free tier settings

### ⚠️ RDS Password (Likely False Positive)
```
~ password: (sensitive value)
```

**Status**: Terraform might be detecting a password change even though it hasn't changed.

**Action**: 
- If password hasn't actually changed, this is safe to ignore
- Terraform will update the password but it will be the same value
- No actual database change will occur

## Recommended Actions

### Option 1: Apply All Changes (Recommended for CloudFront)
```bash
terraform apply
```
- CloudFront will be properly configured
- ECS will have brief downtime (1-2 minutes)
- RDS password update is safe (no actual change)

### Option 2: Apply Only CloudFront (Targeted Apply)
```bash
# Apply only CloudFront changes
terraform apply -target=module.frontend.aws_cloudfront_distribution.frontend
```
- No ECS downtime
- CloudFront will be properly configured
- ECS changes can be applied later

### Option 3: Update ECS Settings to Match Current
If you want to avoid ECS changes, update `terraform.tfvars`:
```hcl
api_task_cpu = 512
api_task_memory = 1024
api_use_public_subnets = false  # If you want to keep private subnets
```

## Next Steps

1. **For CloudFront fix**: Apply the changes (Option 1 or 2)
2. **For ECS**: Decide if you want to keep current resources or downgrade to free tier
3. **After apply**: Verify CloudFront works with custom domain
4. **Delete duplicate**: Remove distribution `ER88UDVCJERIM` after confirming everything works
