# CI/CD Pipeline Verification Guide

## Overview

This document helps verify that all CI/CD pipelines are properly configured and working on GitHub Actions.

## Workflows

### 1. Terraform Workflow (`.github/workflows/terraform.yml`)

**Triggers:**
- Push to `main` branch with changes in `infrastructure/terraform/**`
- Pull requests to `main` with changes in `infrastructure/terraform/**`

**Steps:**
1. ✅ Checkout code
2. ✅ Setup Terraform (v1.5.0)
3. ✅ Configure AWS credentials
4. ✅ Terraform Init (accesses S3 backend)
5. ✅ Terraform Format Check
6. ✅ Terraform Validate
7. ✅ Create terraform.tfvars from example
8. ✅ Terraform Plan
9. ✅ Terraform Apply (only on push to main)

**Required Secrets:**
- `AWS_ACCESS_KEY_ID` ✅
- `AWS_SECRET_ACCESS_KEY` ✅
- `DB_PASSWORD` (optional)
- `REDIS_AUTH_TOKEN` (optional)
- `ACM_CERTIFICATE_ARN` (optional)
- `BACKEND_IMAGE` (optional)

**Status:** ✅ Configured correctly

---

### 2. Backend Workflow (`.github/workflows/backend.yml`)

**Triggers:**
- Push to `main` branch with changes in `src/backend/**` or `.github/workflows/backend.yml`

**Steps:**
1. ✅ Checkout code
2. ✅ Configure AWS credentials
3. ✅ Login to Amazon ECR
4. ✅ Build Docker image
5. ✅ Tag and push to ECR
6. ✅ Update ECS service

**Required Secrets:**
- `AWS_ACCESS_KEY_ID` ✅
- `AWS_SECRET_ACCESS_KEY` ✅

**Status:** ✅ Configured correctly

---

### 3. Frontend Workflow (`.github/workflows/frontend.yml`)

**Triggers:**
- Push to `main` branch with changes in `src/frontend/**`

**Steps:**
1. ✅ Checkout code
2. ✅ Configure AWS credentials
3. ✅ Build React app (`npm ci && npm run build`)
4. ✅ Deploy to S3 (`fastship-dev-frontend`)
5. ✅ Invalidate CloudFront cache

**Required Secrets:**
- `AWS_ACCESS_KEY_ID` ✅
- `AWS_SECRET_ACCESS_KEY` ✅
- `CLOUDFRONT_DISTRIBUTION_ID` ✅ (optional, with warning if missing)

**Status:** ✅ Configured correctly

---

## Verification Checklist

### GitHub Secrets

Verify all required secrets are set in GitHub:
- Settings → Secrets and variables → Actions

**Required for all workflows:**
- ✅ `AWS_ACCESS_KEY_ID`
- ✅ `AWS_SECRET_ACCESS_KEY`

**Required for Terraform:**
- ✅ `DB_PASSWORD` (optional, uses example default if not set)
- ✅ `REDIS_AUTH_TOKEN` (optional, uses example default if not set)
- ✅ `ACM_CERTIFICATE_ARN` (optional)
- ✅ `BACKEND_IMAGE` (optional)

**Required for Frontend:**
- ✅ `CLOUDFRONT_DISTRIBUTION_ID` (optional, workflow continues with warning if missing)

### AWS Resources

Verify these AWS resources exist:

**Terraform Backend:**
- ✅ S3 bucket: `fastship-tf-state-dev`
- ✅ DynamoDB table: `fastship-tf-locks`

**Backend Deployment:**
- ✅ ECR repository: `fastship-backend`
- ✅ ECS cluster: `dev-fastship-cluster`
- ✅ ECS service: `dev-api`

**Frontend Deployment:**
- ✅ S3 bucket: `fastship-dev-frontend`
- ✅ CloudFront distribution: `E3H0EDHBMNOSGI`

### Workflow Files

Verify workflow files exist and are correct:
- ✅ `.github/workflows/terraform.yml`
- ✅ `.github/workflows/backend.yml`
- ✅ `.github/workflows/frontend.yml`

---

## Testing Workflows

### Test Terraform Workflow

Make a small change to trigger the workflow:

```bash
# Add a comment to a Terraform file
echo "# Test" >> infrastructure/terraform/modules/vpc/main.tf
git add infrastructure/terraform/modules/vpc/main.tf
git commit -m "test: trigger terraform workflow"
git push origin main
```

**Expected:** Workflow runs, init succeeds, format/validate pass, plan shows changes

### Test Backend Workflow

Make a small change to trigger the workflow:

```bash
# Add a comment to backend code
echo "# Test" >> src/backend/app/main.py
git add src/backend/app/main.py
git commit -m "test: trigger backend workflow"
git push origin main
```

**Expected:** Workflow runs, builds Docker image, pushes to ECR, updates ECS service

### Test Frontend Workflow

Make a small change to trigger the workflow:

```bash
# Add a comment to frontend code
echo "// Test" >> src/frontend/app/lib/api.ts
git add src/frontend/app/lib/api.ts
git commit -m "test: trigger frontend workflow"
git push origin main
```

**Expected:** Workflow runs, builds React app, deploys to S3, invalidates CloudFront

---

## Common Issues and Fixes

### Issue: Terraform Init Fails

**Error:** `Error: error loading state: AccessDenied`

**Fix:** 
- Verify AWS credentials are set in GitHub secrets
- Verify credentials have S3 and DynamoDB permissions
- Check S3 bucket exists: `fastship-tf-state-dev`
- Check DynamoDB table exists: `fastship-tf-locks`

### Issue: Backend Build Fails

**Error:** `Cannot connect to Docker daemon`

**Fix:**
- This is normal in GitHub Actions - Docker is available
- Check if Dockerfile exists: `src/backend/Dockerfile`
- Check if requirements.txt exists

### Issue: Frontend Build Fails

**Error:** `npm ERR!`

**Fix:**
- Check if `package.json` exists in `src/frontend/`
- Verify Node.js version compatibility
- Check for missing dependencies

### Issue: ECR Push Fails

**Error:** `no basic auth credentials`

**Fix:**
- Verify AWS credentials are correct
- Check ECR repository exists: `fastship-backend`
- Verify IAM user has ECR push permissions

### Issue: ECS Update Fails

**Error:** `Service not found`

**Fix:**
- Verify ECS cluster exists: `dev-fastship-cluster`
- Verify ECS service exists: `dev-api`
- Check service name matches workflow

### Issue: S3 Deploy Fails

**Error:** `AccessDenied`

**Fix:**
- Verify S3 bucket exists: `fastship-dev-frontend`
- Check AWS credentials have S3 write permissions
- Verify bucket policy allows writes

### Issue: CloudFront Invalidation Fails

**Error:** `Distribution not found`

**Fix:**
- Verify CloudFront distribution ID: `E3H0EDHBMNOSGI`
- Check `CLOUDFRONT_DISTRIBUTION_ID` secret is set
- Verify distribution exists in AWS

---

## Workflow Status Check

### Via GitHub Web UI

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Check recent workflow runs:
   - ✅ Green checkmark = Success
   - ❌ Red X = Failed
   - 🟡 Yellow circle = In progress

### Via GitHub CLI

```bash
gh run list --workflow=terraform.yml
gh run list --workflow=backend.yml
gh run list --workflow=frontend.yml
```

### Check Latest Run

```bash
# Get latest run status
gh run list --limit 1

# View logs for latest run
gh run view --log
```

---

## Expected Behavior

### Successful Terraform Workflow

1. ✅ Init completes (accesses S3 backend)
2. ✅ Format check passes
3. ✅ Validate passes
4. ✅ Plan shows changes (or no changes)
5. ✅ Apply completes (on push to main)

### Successful Backend Workflow

1. ✅ Docker image builds
2. ✅ Image pushed to ECR
3. ✅ ECS service updated
4. ✅ New tasks start running

### Successful Frontend Workflow

1. ✅ React app builds
2. ✅ Files deployed to S3
3. ✅ CloudFront cache invalidated
4. ✅ Frontend accessible at `https://app.fastship-api.com`

---

## Monitoring

### GitHub Actions Dashboard

- View all workflow runs: `https://github.com/USERNAME/REPO/actions`
- View specific workflow: `https://github.com/USERNAME/REPO/actions/workflows/WORKFLOW_NAME.yml`

### AWS Console

- **ECS**: Check service status and task health
- **CloudWatch**: View logs from ECS tasks
- **S3**: Verify frontend files are uploaded
- **CloudFront**: Check distribution status

---

## Next Steps

1. ✅ Verify all secrets are set in GitHub
2. ✅ Test each workflow with a small change
3. ✅ Monitor workflow runs in GitHub Actions
4. ✅ Check AWS resources are updated after workflows run
5. ✅ Verify deployments are working (API accessible, frontend loads)

---

**Last Updated**: January 19, 2026
