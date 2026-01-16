# AWS Deployment Workflow

## Overview

This document outlines the step-by-step workflow for deploying FastShip to AWS. The deployment is done in phases to handle dependencies correctly.

## Deployment Phases

### Phase 1: Deploy Infrastructure (First Time)

Deploy all infrastructure **except ECS services** since the Docker image doesn't exist yet:

1. **Comment out ECS module** temporarily in `infrastructure/terraform/environments/dev/main.tf`:
   ```hcl
   # module "ecs" {
   #   ... (comment out entire module block)
   # }
   ```

2. **Run Terraform**:
   ```bash
   cd infrastructure/terraform/environments/dev
   terraform plan -var-file=terraform.tfvars
   terraform apply -var-file=terraform.tfvars
   ```

   This creates:
   - ✅ VPC, subnets, networking
   - ✅ RDS PostgreSQL database
   - ✅ ElastiCache Redis
   - ✅ Application Load Balancer
   - ✅ S3 bucket and CloudFront for frontend
   - ✅ **ECR repository** (new!)

### Phase 2: Build and Push Docker Image

1. **Get ECR repository URI**:
   ```bash
   cd infrastructure/terraform/environments/dev
   terraform output ecr_repository_uri
   ```

   Output example: `337573345298.dkr.ecr.eu-west-1.amazonaws.com/fastship-backend`

2. **Login to ECR**:
   ```bash
   aws ecr get-login-password --region eu-west-1 --profile fastship | \
     docker login --username AWS --password-stdin \
     337573345298.dkr.ecr.eu-west-1.amazonaws.com
   ```

3. **Build Docker image**:
   ```bash
   cd /home/angelo/proyectos/cursos/fastship-aws/src/backend
   docker build -t fastship-backend:latest .
   ```

4. **Tag for ECR**:
   ```bash
   REPO_URI=$(cd ../../infrastructure/terraform/environments/dev && terraform output -raw ecr_repository_uri)
   docker tag fastship-backend:latest ${REPO_URI}:latest
   ```

5. **Push to ECR**:
   ```bash
   docker push ${REPO_URI}:latest
   ```

   Or use the provided script:
   ```bash
   cd /home/angelo/proyectos/cursos/fastship-aws
   ENV=dev ./infrastructure/scripts/build-and-push.sh
   ```

### Phase 3: Deploy ECS Services

1. **Update terraform.tfvars**:
   ```bash
   cd infrastructure/terraform/environments/dev
   
   # Get ECR repository URI
   REPO_URI=$(terraform output -raw ecr_repository_uri)
   
   # Update terraform.tfvars (add or update backend_image)
   # Replace line: backend_image = ""
   # With: backend_image = "${REPO_URI}:latest"
   ```

   Or manually edit `terraform.tfvars`:
   ```hcl
   # ECR Image (set after building and pushing)
   backend_image = "337573345298.dkr.ecr.eu-west-1.amazonaws.com/fastship-backend:latest"
   ```

2. **Uncomment ECS module** in `main.tf`:
   ```hcl
   module "ecs" {
     source = "../../modules/ecs"
     # ... (uncomment the entire module block)
   }
   ```

3. **Deploy ECS**:
   ```bash
   terraform plan -var-file=terraform.tfvars
   terraform apply -var-file=terraform.tfvars
   ```

   This creates:
   - ✅ ECS cluster
   - ✅ ECS task definitions (API and Celery worker)
   - ✅ ECS services

### Phase 4: Verify Deployment

1. **Check ECS services**:
   ```bash
   aws ecs describe-services \
     --cluster dev-fastship-cluster \
     --services dev-api \
     --region eu-west-1 \
     --profile fastship
   ```

2. **Get API URL**:
   ```bash
   terraform output api_url
   ```

3. **Test API**:
   ```bash
   API_URL=$(terraform output -raw api_url)
   curl ${API_URL}/health
   ```

---

## Alternative: Single-Phase Deployment (Recommended)

If you want to deploy everything at once, use this workflow:

### Step 1: Deploy Infrastructure + ECR

```bash
cd infrastructure/terraform/environments/dev
terraform apply -var-file=terraform.tfvars
```

The ECS module will fail because `backend_image` is empty - **this is expected!**

### Step 2: Build and Push Image

```bash
# Get ECR repository URI
REPO_URI=$(terraform output -raw ecr_repository_uri)

# Build and push
cd /home/angelo/proyectos/cursos/fastship-aws
ENV=dev ./infrastructure/scripts/build-and-push.sh

# Or manually:
aws ecr get-login-password --region eu-west-1 --profile fastship | \
  docker login --username AWS --password-stdin ${REPO_URI}
cd src/backend
docker build -t fastship-backend:latest .
docker tag fastship-backend:latest ${REPO_URI}:latest
docker push ${REPO_URI}:latest
```

### Step 3: Update and Redeploy

```bash
# Update terraform.tfvars with image URI
sed -i "s|backend_image = \"\"|backend_image = \"${REPO_URI}:latest\"|" terraform.tfvars

# Or manually edit terraform.tfvars:
# backend_image = "337573345298.dkr.ecr.eu-west-1.amazonaws.com/fastship-backend:latest"

# Apply again
terraform apply -var-file=terraform.tfvars
```

---

## Quick Reference Commands

### Get ECR Repository URI
```bash
cd infrastructure/terraform/environments/dev
terraform output ecr_repository_uri
```

### Login to ECR
```bash
aws ecr get-login-password --region eu-west-1 --profile fastship | \
  docker login --username AWS --password-stdin \
  $(terraform output -raw ecr_repository_uri)
```

### Build and Push (using script)
```bash
cd /home/angelo/proyectos/cursos/fastship-aws
ENV=dev ./infrastructure/scripts/build-and-push.sh
```

### Check ECS Services
```bash
aws ecs list-services \
  --cluster dev-fastship-cluster \
  --region eu-west-1 \
  --profile fastship
```

### View ECS Logs
```bash
aws logs tail /ecs/dev-api --follow --region eu-west-1 --profile fastship
```

---

## Troubleshooting

### Error: "Container.image should not be null or empty"

**Cause**: `backend_image` in `terraform.tfvars` is empty, but ECS task definitions require a valid image URI.

**Solution**:
1. Complete Phase 2 (Build and Push Docker Image) first
2. Update `terraform.tfvars` with the ECR repository URI
3. Run `terraform apply` again

### Error: "RepositoryNotFoundException"

**Cause**: ECR repository doesn't exist yet.

**Solution**: Ensure Phase 1 is complete and the ECR module is included in `main.tf`.

### ECS Service Not Starting

**Check**:
1. Task definition uses correct image URI
2. Security groups allow traffic
3. Subnet routing is correct
4. CloudWatch logs for errors:
   ```bash
   aws logs tail /ecs/dev-api --follow --region eu-west-1 --profile fastship
   ```

---

## Next Steps After Deployment

1. ✅ Configure GitHub Secrets for CI/CD
2. ✅ Set up GitHub Actions workflows
3. ✅ Configure custom domain (optional)
4. ✅ Set up CloudWatch alarms
5. ✅ Configure backup policies

For detailed instructions, see [DEPLOYMENT-AWS.md](./DEPLOYMENT-AWS.md).
