# Deployment Readiness Checklist

## ✅ Pre-Deployment Checklist

### 1. Infrastructure (Terraform)
- [x] **Terraform modules created**: VPC, ECS, RDS, Redis, Frontend, Networking
- [x] **Environment configs**: Dev environment configured
- [x] **Free-tier optimized**: All resources configured for free tier
- [x] **NAT Gateway**: Disabled for free tier (saves $32/month)
- [x] **Backend state**: S3 bucket and DynamoDB table setup script ready
- [x] **Variables configured**: terraform.tfvars has all required values

**Status**: ✅ **READY** (26 Terraform files)

### 2. Dockerfiles
- [x] **Backend Dockerfile**: AWS-ready with health checks, system deps, migrations
- [x] **Frontend Dockerfile**: Build-only for S3+CloudFront deployment
- [x] **Health checks**: Configured for ECS

**Status**: ✅ **READY**

### 3. CI/CD Pipelines
- [x] **Terraform workflow**: `.github/workflows/terraform.yml`
- [x] **Backend workflow**: `.github/workflows/backend.yml`
- [x] **Frontend workflow**: `.github/workflows/frontend.yml`
- [x] **GitHub Secrets**: Documentation in `.github/SECRETS.md`

**Status**: ✅ **READY** (Secrets need to be configured in GitHub)

### 4. Deployment Scripts
- [x] **build-and-push.sh**: Builds and pushes to ECR
- [x] **deploy-backend.sh**: Deploys to ECS
- [x] **deploy-frontend.sh**: Deploys to S3+CloudFront
- [x] **setup-terraform-backend.sh**: Sets up S3 and DynamoDB

**Status**: ✅ **READY** (All scripts are executable)

### 5. Configuration Files
- [x] **terraform.tfvars**: Configured with passwords and settings
- [x] **Makefile**: Commands for deployment
- [x] **docker-compose.aws.yml**: Local AWS simulation

**Status**: ✅ **READY**

## ⚠️ Pre-Deployment Actions Required

### Step 1: Set Up Terraform Backend

```bash
# Create S3 bucket and DynamoDB table
../../infrastructure/scripts/setup-terraform-backend.sh dev
```

**Expected output**: S3 bucket `fastship-tf-state-dev` and DynamoDB table `fastship-tf-locks` created.

### Step 2: Configure GitHub Secrets

Go to GitHub → Settings → Secrets and variables → Actions, add:

- `AWS_ACCESS_KEY_ID`: Your AWS access key
- `AWS_SECRET_ACCESS_KEY`: Your AWS secret key
- `CLOUDFRONT_DISTRIBUTION_ID`: (Get after Terraform deploy)

### Step 3: Verify terraform.tfvars

Current configuration looks good:
- ✅ Passwords set (db_password, redis_auth_token)
- ✅ Free-tier settings (256 CPU, 512 MB memory)
- ✅ NAT Gateway disabled (free tier)
- ⚠️ `backend_image = ""` (expected - will be set after first ECR push)

## 🚀 Deployment Steps

### Phase 1: Deploy Infrastructure

```bash
cd ../../infrastructure/terraform/environments/dev

# Initialize Terraform
terraform init

# Verify configuration
terraform fmt -check
terraform validate

# Plan deployment
terraform plan -var-file=terraform.tfvars

# Apply infrastructure
terraform apply -var-file=terraform.tfvars
```

**Expected resources**:
- VPC with public/private subnets
- RDS PostgreSQL (db.t3.micro)
- ElastiCache Redis (cache.t3.micro)
- ECS Cluster
- ALB (Application Load Balancer)
- S3 bucket for frontend
- CloudFront distribution

### Phase 2: Build and Push Backend Image

```bash
# Build and push to ECR
../../infrastructure/scripts/build-and-push.sh dev latest

# Get the image URI
aws ecr describe-images \
  --repository-name fastship-backend \
  --query 'sort_by(imageDetails,&imagePushedAt)[-1].imageTags[0]' \
  --output text

# Update terraform.tfvars with the image URI
# Then update ECS task definition
terraform apply -var-file=terraform.tfvars
```

**Or use CI/CD**: Push to `main` branch, GitHub Actions will build and push automatically.

### Phase 3: Deploy Frontend

```bash
# Deploy to S3 and invalidate CloudFront
../../infrastructure/scripts/deploy-frontend.sh dev
```

**Or use CI/CD**: Push frontend changes to `main` branch.

### Phase 4: Update ECS Service

After backend image is pushed:

```bash
# Update ECS service with new image
../../infrastructure/scripts/deploy-backend.sh dev <image-uri>
```

**Or use CI/CD**: GitHub Actions will update ECS service automatically.

## 📋 Post-Deployment Verification

### 1. Check Infrastructure

```bash
# Get outputs
cd ../../infrastructure/terraform/environments/dev
terraform output

# Should show:
# - alb_dns_name
# - cloudfront_domain_name
# - db_endpoint
# - redis_endpoint
```

### 2. Verify Backend

```bash
# Get ALB DNS name
ALB_DNS=$(terraform output -raw alb_dns_name)

# Check health
curl http://$ALB_DNS/health

# Should return: {"status":"healthy","redis":"connected","service":"FastAPI Backend"}
```

### 3. Verify Frontend

```bash
# Get CloudFront domain
CF_DOMAIN=$(terraform output -raw cloudfront_domain_name)

# Open in browser
echo "Frontend: https://$CF_DOMAIN"
```

### 4. Check ECS Services

```bash
# Check API service
aws ecs describe-services \
  --cluster dev-fastship-cluster \
  --services dev-api \
  --region eu-west-1

# Check Celery worker
aws ecs describe-services \
  --cluster dev-fastship-cluster \
  --services dev-celery-worker \
  --region eu-west-1
```

## 🔍 Current Configuration Summary

### Terraform Configuration
- **Region**: eu-west-1
- **VPC CIDR**: 10.0.0.0/16
- **NAT Gateway**: Disabled (free tier)
- **RDS**: db.t3.micro, 20 GB, single-AZ
- **Redis**: cache.t3.micro, single node
- **ECS API**: 256 CPU, 512 MB, 1 task
- **ECS Worker**: 256 CPU, 512 MB, 1 task

### Dockerfiles
- **Backend**: Python 3.11-slim, health checks, migrations
- **Frontend**: Node 20-alpine, build-only

### CI/CD
- **Terraform**: Auto-validates and applies on push to main
- **Backend**: Auto-builds, pushes to ECR, updates ECS
- **Frontend**: Auto-builds, deploys to S3, invalidates CloudFront

## ⚠️ Known Issues / Notes

1. **backend_image is empty**: This is expected. It will be populated after first ECR push.
2. **First deployment**: You'll need to manually update terraform.tfvars with the ECR image URI after first build, or let CI/CD handle it.
3. **CloudFront Distribution ID**: Get from Terraform output and add to GitHub Secrets.

## ✅ Final Status

**Everything is ready for deployment!**

All files are in place:
- ✅ 26 Terraform files
- ✅ 2 Dockerfiles (backend + frontend)
- ✅ 3 CI/CD workflows
- ✅ 4 deployment scripts
- ✅ Configuration files

**Next step**: Run `../../infrastructure/scripts/setup-terraform-backend.sh dev` to create the S3 backend, then proceed with Terraform deployment.
