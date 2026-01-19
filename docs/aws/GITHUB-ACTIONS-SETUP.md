# GitHub Actions Setup Guide

## Required Secrets

Configure the following secrets in your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

### Required Secrets

1. **AWS_ACCESS_KEY_ID**
   - Your AWS access key ID
   - Used by all workflows (Terraform, Backend, Frontend)

2. **AWS_SECRET_ACCESS_KEY**
   - Your AWS secret access key
   - Used by all workflows

3. **CLOUDFRONT_DISTRIBUTION_ID**
   - CloudFront distribution ID for cache invalidation
   - Value: `E3H0EDHBMNOSGI`
   - Used by: Frontend workflow

### Optional Secrets (for Terraform)

These are optional but recommended for production:

4. **DB_PASSWORD**
   - RDS PostgreSQL password
   - **Important**: This is passed to ECS as `POSTGRES_PASSWORD` (not in `DATABASE_URL`)
   - Individual POSTGRES_* variables are used to avoid URL encoding/interpolation issues with special characters
   - Can contain special characters like: `*`, `>`, `_`, `|`, `%`, `{`, `}`, etc.
   - If not set, uses default from `terraform.tfvars.example`
   - Used by: Terraform workflow

5. **REDIS_AUTH_TOKEN**
   - ElastiCache Redis authentication token
   - **Note**: Currently passed in `REDIS_URL` format: `redis://:TOKEN@HOST:PORT`
   - Redis tokens are typically hexadecimal and don't have special character issues
   - If not set, uses default from `terraform.tfvars.example`
   - Used by: Terraform workflow

6. **ACM_CERTIFICATE_ARN**
   - ACM certificate ARN for ALB (eu-west-1)
   - Get with: `aws acm list-certificates --region eu-west-1 --query 'CertificateSummaryList[?DomainName==`api.fastship-api.com`].CertificateArn' --output text`
   - Current value: `arn:aws:acm:eu-west-1:337573345298:certificate/872b2b04-d0c4-432c-bbbd-e291df9afdd3`
   - Used by: Terraform workflow

7. **BACKEND_IMAGE**
   - ECR image URI for backend
   - Format: `ACCOUNT.dkr.ecr.REGION.amazonaws.com/REPO:TAG`
   - Current value: `337573345298.dkr.ecr.eu-west-1.amazonaws.com/fastship-backend:latest`
   - Used by: Terraform workflow

## Workflow Configuration

### Frontend CI/CD

**Triggers:**
- Push to `main` branch
- Changes in `src/frontend/**`

**Steps:**
1. Checkout code
2. Configure AWS credentials
3. Build React app (`npm ci && npm run build`)
4. Deploy to S3 (`fastship-dev-frontend`)
5. Invalidate CloudFront cache

**Required Secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `CLOUDFRONT_DISTRIBUTION_ID` (optional, but recommended)

### Backend CI/CD

**Triggers:**
- Push to `main` branch
- Changes in `src/backend/**` or `.github/workflows/backend.yml`

**Steps:**
1. Checkout code
2. Configure AWS credentials
3. Login to ECR
4. Build and push Docker image
5. Update ECS service

**Required Secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

### Terraform CI/CD

**Triggers:**
- Push to `main` branch
- Changes in `infrastructure/terraform/**`
- Pull requests to `main`

**Steps:**
1. Checkout code
2. Setup Terraform
3. Create `terraform.tfvars` from example
4. Update sensitive values from secrets
5. Terraform Init
6. Terraform Format Check
7. Terraform Validate
8. Terraform Plan
9. Terraform Apply (only on push to main)

**Required Secrets:**
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`

**Optional Secrets:**
- `DB_PASSWORD`
- `REDIS_AUTH_TOKEN`
- `ACM_CERTIFICATE_ARN`
- `BACKEND_IMAGE`

## How Terraform Workflow Handles terraform.tfvars

Since `terraform.tfvars` is gitignored (contains sensitive data), the workflow:

1. **Copies** `terraform.tfvars.example` to `terraform.tfvars`
2. **Updates** sensitive values from GitHub secrets if provided:
   - `db_password` from `DB_PASSWORD` secret
   - `redis_auth_token` from `REDIS_AUTH_TOKEN` secret
   - `acm_certificate_arn` from `ACM_CERTIFICATE_ARN` secret
   - `backend_image` from `BACKEND_IMAGE` secret
3. **Uses** the generated `terraform.tfvars` for plan/apply

If secrets are not set, it uses default values from `terraform.tfvars.example`.

## Setting Up Secrets

### Via GitHub Web UI

1. Go to your repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add each secret with its value
5. Click **Add secret**

### Via GitHub CLI

```bash
gh secret set AWS_ACCESS_KEY_ID --body "YOUR_ACCESS_KEY"
gh secret set AWS_SECRET_ACCESS_KEY --body "YOUR_SECRET_KEY"
gh secret set CLOUDFRONT_DISTRIBUTION_ID --body "E3H0EDHBMNOSGI"
gh secret set DB_PASSWORD --body "YOUR_DB_PASSWORD"
gh secret set REDIS_AUTH_TOKEN --body "YOUR_REDIS_TOKEN"
gh secret set ACM_CERTIFICATE_ARN --body "arn:aws:acm:eu-west-1:337573345298:certificate/872b2b04-d0c4-432c-bbbd-e291df9afdd3"
gh secret set BACKEND_IMAGE --body "337573345298.dkr.ecr.eu-west-1.amazonaws.com/fastship-backend:latest"
```

## Troubleshooting

### Frontend Workflow Fails

**Error: "No such file or directory: src/frontend/dist/"**
- ✅ Fixed: Workflow now changes directory before syncing

**Error: "CLOUDFRONT_DISTRIBUTION_ID not found"**
- Set the `CLOUDFRONT_DISTRIBUTION_ID` secret
- Or the workflow will skip cache invalidation (with warning)

### Terraform Workflow Fails

**Error: "terraform.tfvars not found"**
- ✅ Fixed: Workflow now creates `terraform.tfvars` from example

**Error: "Backend configuration error"**
- Ensure S3 bucket `fastship-tf-state-dev` exists
- Ensure DynamoDB table `fastship-tf-locks` exists
- Check AWS credentials have permissions

**Error: "Invalid credentials"**
- Verify `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` are correct
- Check IAM user has required permissions

### Backend Workflow Fails

**Error: "ECR login failed"**
- Check AWS credentials
- Verify ECR repository exists: `fastship-backend`

**Error: "ECS service update failed"**
- Check ECS cluster exists: `dev-fastship-cluster`
- Check ECS service exists: `dev-api`
- Verify IAM permissions for ECS

## Required IAM Permissions

Your AWS user/role needs:

- **EC2**: VPC, subnets, security groups, load balancers
- **ECS**: Clusters, services, task definitions, tasks
- **RDS**: Database instances, subnet groups
- **ElastiCache**: Replication groups, subnet groups
- **S3**: Buckets, objects (for Terraform state and frontend)
- **CloudFront**: Distributions, invalidations
- **ECR**: Repositories, images
- **IAM**: Roles and policies (for ECS)
- **CloudWatch**: Logs
- **ACM**: Certificates (read)
- **DynamoDB**: Tables (for Terraform state locking)

## Testing Workflows

### Test Frontend Workflow

```bash
# Make a small change to frontend
echo "// test" >> src/frontend/app/lib/api.ts
git add src/frontend/app/lib/api.ts
git commit -m "test: trigger frontend workflow"
git push origin main
```

### Test Backend Workflow

```bash
# Make a small change to backend
echo "# test" >> src/backend/app/main.py
git add src/backend/app/main.py
git commit -m "test: trigger backend workflow"
git push origin main
```

### Test Terraform Workflow

```bash
# Make a small change to Terraform (add a comment)
echo "# test" >> infrastructure/terraform/modules/vpc/main.tf
git add infrastructure/terraform/modules/vpc/main.tf
git commit -m "test: trigger terraform workflow"
git push origin main
```

---

**Last Updated**: January 19, 2026
