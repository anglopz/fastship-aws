# Terraform State Lock - How to Handle

## Error Message
```
Error: Error acquiring the state lock
Lock Info:
  ID:        43134687-cbb5-3ca3-c46b-63a4d1b80489
  Path:      fastship-tf-state-dev/terraform.tfstate
  Operation: OperationTypeApply
  Who:       runner@runnervmmtnos
  Version:   1.5.0
  Created:   2026-01-22 11:32:39.488694803 +0000 UTC
```

## What This Means
The Terraform state is locked by a GitHub Actions workflow (`runner@runnervmmtnos`). This prevents concurrent modifications to the state file.

## Solutions

### Option 1: Wait for Workflow to Complete (Recommended)
1. Go to **GitHub → Actions → Terraform workflow**
2. Check if the workflow is still running
3. Wait for it to complete (usually 5-15 minutes)
4. Once complete, the lock will be released automatically

### Option 2: Cancel the Workflow
If the workflow is stuck or you need to run Terraform locally:
1. Go to **GitHub → Actions**
2. Find the running Terraform workflow
3. Click **Cancel workflow**
4. Wait 1-2 minutes for the lock to be released

### Option 3: Force Unlock (Use with Caution)
**⚠️ Only use if you're certain the workflow is stuck and won't complete**

```bash
cd infrastructure/terraform/environments/dev

# Force unlock using the lock ID from the error
terraform force-unlock 43134687-cbb5-3ca3-c46b-63a4d1b80489
```

**Warning**: 
- Only do this if the workflow is definitely stuck/failed
- Make sure no one else is running Terraform
- This can cause state corruption if used incorrectly

### Option 4: Check Lock Status
```bash
# Check if lock still exists (requires AWS CLI access to DynamoDB)
aws dynamodb get-item \
  --table-name fastship-tf-locks \
  --key '{"LockID":{"S":"fastship-tf-state-dev/terraform.tfstate-md5"}}' \
  --profile fastship \
  --region eu-west-1
```

## Prevention
- **Don't run Terraform locally while workflows are running**
- **Wait for workflows to complete before local operations**
- **Use `terraform plan` locally, but coordinate `terraform apply` with CI/CD**

## Current Situation
The lock was created at `2026-01-22 11:32:39 UTC` by a GitHub Actions workflow. Check:
1. Is the workflow still running?
2. Did it complete successfully?
3. Is it stuck in a failed state?

## Recommended Action
1. **Check GitHub Actions** first
2. If workflow is running: **Wait for it to complete**
3. If workflow failed/stuck: **Cancel it**, wait 2 minutes, then try again
4. Only use `force-unlock` as a last resort
