# Terraform Setup Instructions

## Prerequisites

1. **AWS CLI configured** with credentials:
   ```bash
   aws configure
   ```

2. **Terraform installed** (>= 1.5.0):
   ```bash
   terraform version
   ```

## Initial Setup

### Step 1: Create S3 Backend and DynamoDB Table

Run the setup script:

```bash
# From project root
./infrastructure/scripts/setup-terraform-backend.sh dev
```

Or manually (see `README-BACKEND.md` in this directory for details).

For AWS deployment guides, see `../../docs/aws/`.

### Step 2: Configure Terraform Variables

Copy the example variables file:

```bash
cd infrastructure/terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your values:

```hcl
aws_region = "eu-west-1"

vpc_cidr            = "10.0.0.0/16"
public_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
private_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24"]
availability_zones = ["eu-west-1a", "eu-west-1b"]

database_name = "fastship"
username      = "fastship"
db_password   = "your-secure-password-here"

redis_auth_token = "your-redis-token-here"

backend_image = ""  # Will be set after first ECR push

instance_class       = "db.t3.micro"
rds_allocated_storage = 20

node_type           = "cache.t3.micro"
redis_num_cache_nodes = 1

api_task_cpu       = 512
api_task_memory    = 1024
api_desired_count  = 1

worker_task_cpu      = 256
worker_task_memory   = 512
worker_desired_count = 1

log_retention_days = 7
```

### Step 3: Initialize Terraform

```bash
cd infrastructure/terraform/environments/dev
terraform init
```

You should see:
```
Initializing the backend...
Successfully configured the backend "s3"!
Terraform has been successfully initialized!
```

### Step 4: Verify Configuration

```bash
# Format check
terraform fmt -check

# Validate
terraform validate

# Plan (dry-run)
terraform plan -var-file=terraform.tfvars
```

### Step 5: Apply Infrastructure

```bash
terraform apply -var-file=terraform.tfvars
```

Type `yes` when prompted, or use `-auto-approve` flag.

## Common Commands

```bash
# Initialize
terraform init

# Format code
terraform fmt

# Validate
terraform validate

# Plan
terraform plan -var-file=terraform.tfvars

# Apply
terraform apply -var-file=terraform.tfvars

# Destroy (careful!)
terraform destroy -var-file=terraform.tfvars

# Show outputs
terraform output

# Show state
terraform show
```

## Troubleshooting

### Backend Initialization Errors

**Error**: "Failed to get existing workspaces: NoSuchBucket"

**Solution**: Create the S3 bucket first:
```bash
./infrastructure/scripts/setup-terraform-backend.sh dev
```

**Error**: "Error locking state: ResourceNotFoundException"

**Solution**: Create the DynamoDB table:
```bash
./infrastructure/scripts/setup-terraform-backend.sh dev
```

### Access Denied Errors

Ensure your AWS credentials have the necessary permissions:

- S3: `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject`, `s3:ListBucket`
- DynamoDB: `dynamodb:GetItem`, `dynamodb:PutItem`, `dynamodb:DeleteItem`

### State Locked

If Terraform fails and leaves a lock:

```bash
# Check for locks
aws dynamodb scan --table-name fastship-tf-locks --region eu-west-1

# Manually delete lock item (use with caution!)
aws dynamodb delete-item \
  --table-name fastship-tf-locks \
  --key '{"LockID":{"S":"your-lock-id"}}' \
  --region eu-west-1
```

## Next Steps

After infrastructure is deployed:

1. **Get outputs**:
   ```bash
   terraform output
   ```

2. **Update GitHub Secrets** with CloudFront distribution ID:
   ```bash
   terraform output cloudfront_distribution_id
   ```

3. **Build and push backend image**:
   ```bash
   ./infrastructure/scripts/build-and-push.sh dev
   ```

4. **Deploy frontend**:
   ```bash
   ./infrastructure/scripts/deploy-frontend.sh dev
   ```
