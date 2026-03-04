# Cost Optimization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Reduce AWS monthly cost from $112 to ~$1-3 by removing wasteful VPC endpoints and adding a Terraform-driven services toggle with spin-up/spin-down scripts.

**Architecture:** Add a `services_enabled` boolean variable that gates RDS, Redis, networking (ALB), and ECS modules via `count`. When false, only VPC, S3+CloudFront, ECR, and Route53 remain. VPC Interface Endpoints are removed permanently since ECS runs in public subnets.

**Tech Stack:** Terraform (HCL), Bash scripts, AWS CLI

---

### Task 1: Remove VPC Interface Endpoints (permanent)

**Files:**
- Modify: `infrastructure/terraform/modules/vpc/vpc_endpoints.tf`

**Step 1: Remove the 3 Interface endpoints and their security group**

Replace the entire file content with only the free S3 Gateway endpoint:

```hcl
# S3 Gateway endpoint (free, allows S3 access without NAT Gateway)
resource "aws_vpc_endpoint" "s3" {
  vpc_id            = aws_vpc.main.id
  service_name      = "com.amazonaws.${data.aws_region.current.name}.s3"
  vpc_endpoint_type = "Gateway"
  route_table_ids   = aws_route_table.private[*].id

  tags = {
    Name = "${var.environment}-fastship-s3-endpoint"
  }
}

data "aws_region" "current" {}
```

This removes:
- `aws_vpc_endpoint.ecr_api` (~$14.60/month)
- `aws_vpc_endpoint.ecr_dkr` (~$14.60/month)
- `aws_vpc_endpoint.cloudwatch_logs` (~$14.60/month)
- `aws_security_group.vpc_endpoint`

**Step 2: Validate syntax**

Run: `cd infrastructure/terraform/environments/dev && terraform validate`
Expected: Success

**Step 3: Commit**

```bash
git add infrastructure/terraform/modules/vpc/vpc_endpoints.tf
git commit -m "infra: remove unused VPC Interface Endpoints

ECS tasks run in public subnets (api_use_public_subnets=true),
so Interface Endpoints for ECR API, ECR DKR, and CloudWatch Logs
are unnecessary. Saves ~$44/month. S3 Gateway endpoint kept (free)."
```

---

### Task 2: Add services_enabled variable

**Files:**
- Modify: `infrastructure/terraform/environments/dev/variables.tf`
- Modify: `infrastructure/terraform/environments/dev/terraform.tfvars`

**Step 1: Add variable definition to variables.tf**

Add at the top of the file (after the aws_region variable):

```hcl
variable "services_enabled" {
  description = "Toggle backend services (ECS, RDS, Redis, ALB). Set false to tear down compute/DB and minimize costs. Frontend (S3+CloudFront), VPC, and ECR remain."
  type        = bool
  default     = false
}
```

**Step 2: Add to terraform.tfvars**

Add after the `enable_nat_gateway` line:

```hcl
# Cost optimization: set to false to tear down ECS, RDS, Redis, ALB (~$68/month savings)
# Use spin-up.sh / spin-down.sh scripts to toggle
services_enabled = false
```

**Step 3: Validate syntax**

Run: `cd infrastructure/terraform/environments/dev && terraform validate`
Expected: Success (variable defined but not yet used)

**Step 4: Commit**

```bash
git add infrastructure/terraform/environments/dev/variables.tf infrastructure/terraform/environments/dev/terraform.tfvars
git commit -m "infra: add services_enabled toggle variable (default false)"
```

---

### Task 3: Gate networking module (ALB + security groups) with count

**Files:**
- Modify: `infrastructure/terraform/environments/dev/main.tf`

**Step 1: Add count to networking module**

Change the networking module block from:

```hcl
module "networking" {
  source = "../../modules/networking"

  project_name        = "fastship"
  environment         = local.environment
  vpc_id              = module.vpc.vpc_id
  public_subnet_ids   = module.vpc.public_subnet_ids
  acm_certificate_arn = var.acm_certificate_arn
}
```

To:

```hcl
module "networking" {
  count  = var.services_enabled ? 1 : 0
  source = "../../modules/networking"

  project_name        = "fastship"
  environment         = local.environment
  vpc_id              = module.vpc.vpc_id
  public_subnet_ids   = module.vpc.public_subnet_ids
  acm_certificate_arn = var.acm_certificate_arn
}
```

**Step 2: Validate syntax**

Run: `cd infrastructure/terraform/environments/dev && terraform validate`
Expected: May warn about references to module.networking outputs — we fix those in Task 5.

**Step 3: Commit**

```bash
git add infrastructure/terraform/environments/dev/main.tf
git commit -m "infra: gate networking module (ALB) with services_enabled"
```

---

### Task 4: Gate RDS and Redis modules with count

**Files:**
- Modify: `infrastructure/terraform/environments/dev/main.tf`

**Step 1: Add count to rds module**

Change:

```hcl
module "rds" {
  source = "../../modules/rds"
```

To:

```hcl
module "rds" {
  count  = var.services_enabled ? 1 : 0
  source = "../../modules/rds"
```

**Step 2: Add count to redis module**

Change:

```hcl
module "redis" {
  source = "../../modules/redis"
```

To:

```hcl
module "redis" {
  count  = var.services_enabled ? 1 : 0
  source = "../../modules/redis"
```

**Step 3: Update RDS module references**

In the rds module block, update the networking reference:

Change:
```hcl
  security_group_id  = module.networking.rds_security_group_id
```

To:
```hcl
  security_group_id  = module.networking[0].rds_security_group_id
```

**Step 4: Update Redis module references**

In the redis module block, update:

Change:
```hcl
  security_group_id  = module.networking.redis_security_group_id
```

To:
```hcl
  security_group_id  = module.networking[0].redis_security_group_id
```

**Step 5: Commit**

```bash
git add infrastructure/terraform/environments/dev/main.tf
git commit -m "infra: gate RDS and Redis modules with services_enabled"
```

---

### Task 5: Gate ECS module with count and fix all cross-references

**Files:**
- Modify: `infrastructure/terraform/environments/dev/main.tf`

**Step 1: Add count to ecs module and update all indexed references**

Change the ECS module block. The full updated block:

```hcl
module "ecs" {
  count  = var.services_enabled ? 1 : 0
  source = "../../modules/ecs"

  project_name          = "fastship"
  environment           = local.environment
  aws_region            = var.aws_region
  backend_image         = var.backend_image
  public_subnet_ids     = module.vpc.public_subnet_ids
  private_subnet_ids    = module.vpc.private_subnet_ids
  ecs_security_group_id = module.networking[0].ecs_security_group_id
  target_group_arn      = module.networking[0].target_group_arn
  api_use_public_subnets = var.api_use_public_subnets

  api_task_cpu    = var.api_task_cpu
  api_task_memory = var.api_task_memory
  api_desired_count = var.api_desired_count

  worker_task_cpu    = var.worker_task_cpu
  worker_task_memory = var.worker_task_memory
  worker_desired_count = var.worker_desired_count
  worker_use_public_subnets = var.worker_use_public_subnets

  log_retention_days = var.log_retention_days

  container_environment = [
    {
      name  = "POSTGRES_SERVER"
      value = module.rds[0].db_address
    },
    {
      name  = "POSTGRES_PORT"
      value = tostring(module.rds[0].db_port)
    },
    {
      name  = "POSTGRES_USER"
      value = var.username
    },
    {
      name  = "POSTGRES_PASSWORD"
      value = var.db_password
    },
    {
      name  = "POSTGRES_DB"
      value = var.database_name
    },
    {
      name  = "REDIS_URL"
      value = "rediss://:${var.redis_auth_token}@${module.redis[0].redis_endpoint}:${module.redis[0].redis_port}?ssl_cert_reqs=required"
    },
    {
      name  = "EMAIL_MODE"
      value = "sandbox"
    },
    {
      name  = "MAILTRAP_USERNAME"
      value = var.mailtrap_username
    },
    {
      name  = "MAILTRAP_PASSWORD"
      value = var.mailtrap_password
    },
    {
      name  = "MAIL_FROM"
      value = "noreply@fastship-api.com"
    },
    {
      name  = "MAIL_FROM_NAME"
      value = "FastShip"
    },
    {
      name  = "APP_DOMAIN"
      value = "api.fastship-api.com"
    },
    {
      name  = "FRONTEND_URL"
      value = "https://app.fastship-api.com"
    },
    {
      name  = "CORS_ORIGINS"
      value = "https://app.fastship-api.com,https://fastship-api.com,https://www.fastship-api.com,http://localhost:3000,http://localhost:5173"
    }
  ]
}
```

Key changes: all `module.rds.` → `module.rds[0].`, `module.redis.` → `module.redis[0].`, `module.networking.` → `module.networking[0].`

When `services_enabled = false` and `count = 0`, Terraform does NOT evaluate the module arguments, so the `[0]` references won't error.

**Step 2: Validate the full configuration**

Run: `cd infrastructure/terraform/environments/dev && terraform validate`
Expected: Success

**Step 3: Commit**

```bash
git add infrastructure/terraform/environments/dev/main.tf
git commit -m "infra: gate ECS module with services_enabled, update all module references to indexed"
```

---

### Task 6: Create spin-down.sh script

**Files:**
- Create: `infrastructure/scripts/spin-down.sh`

**Step 1: Write the script**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Spin down FastShip AWS services to minimize costs
# Keeps: VPC, S3+CloudFront (frontend), ECR, Route53
# Destroys: ECS, RDS, Redis, ALB

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$SCRIPT_DIR/../terraform/environments/dev"
TFVARS="$TF_DIR/terraform.tfvars"

echo "=== FastShip Spin Down ==="
echo "This will destroy: ECS services, RDS database, Redis cache, ALB"
echo "This will keep: Frontend (S3+CloudFront), VPC, ECR, Route53"
echo ""

# Check current state
CURRENT=$(grep -E '^services_enabled' "$TFVARS" | awk '{print $3}')
if [ "$CURRENT" = "false" ]; then
  echo "Services are already disabled in terraform.tfvars"
  echo "Run 'terraform apply' if the resources still exist in AWS."
fi

read -p "Continue? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

# Toggle services_enabled to false
sed -i 's/^services_enabled = true/services_enabled = false/' "$TFVARS"
echo "Set services_enabled = false in terraform.tfvars"

# Run terraform
cd "$TF_DIR"
export AWS_PROFILE="${AWS_PROFILE:-fastship}"
export AWS_REGION="${AWS_REGION:-eu-west-1}"

echo ""
echo "Running terraform plan..."
terraform plan -var-file=terraform.tfvars

echo ""
read -p "Apply this plan? (y/N): " apply_confirm
if [[ ! "$apply_confirm" =~ ^[Yy]$ ]]; then
  echo "Aborted. terraform.tfvars was already updated — revert manually if needed."
  exit 0
fi

terraform apply -var-file=terraform.tfvars -auto-approve

echo ""
echo "=== Spin Down Complete ==="
echo "Destroyed: ECS, RDS, Redis, ALB"
echo "Still running: Frontend at https://app.fastship-api.com"
echo "Estimated monthly cost: ~\$1-3"
echo ""
echo "To spin back up: ./spin-up.sh"
```

**Step 2: Make executable**

Run: `chmod +x infrastructure/scripts/spin-down.sh`

**Step 3: Commit**

```bash
git add infrastructure/scripts/spin-down.sh
git commit -m "infra: add spin-down.sh script for cost optimization"
```

---

### Task 7: Create spin-up.sh script

**Files:**
- Create: `infrastructure/scripts/spin-up.sh`

**Step 1: Write the script**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Spin up FastShip AWS services for demos or development
# Creates: ECS services, RDS database, Redis cache, ALB
# Typical spin-up time: ~8-12 minutes (RDS creation is the bottleneck)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TF_DIR="$SCRIPT_DIR/../terraform/environments/dev"
TFVARS="$TF_DIR/terraform.tfvars"

echo "=== FastShip Spin Up ==="
echo "This will create: ECS services (API + Celery), RDS PostgreSQL, Redis, ALB"
echo "Estimated time: ~8-12 minutes"
echo "Estimated cost while running: ~\$3-5/day"
echo ""

read -p "Continue? (y/N): " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "Aborted."
  exit 0
fi

# Toggle services_enabled to true
sed -i 's/^services_enabled = false/services_enabled = true/' "$TFVARS"
echo "Set services_enabled = true in terraform.tfvars"

# Run terraform
cd "$TF_DIR"
export AWS_PROFILE="${AWS_PROFILE:-fastship}"
export AWS_REGION="${AWS_REGION:-eu-west-1}"

echo ""
echo "Running terraform plan..."
terraform plan -var-file=terraform.tfvars

echo ""
read -p "Apply this plan? (y/N): " apply_confirm
if [[ ! "$apply_confirm" =~ ^[Yy]$ ]]; then
  echo "Aborted. terraform.tfvars was already updated — revert manually if needed."
  exit 0
fi

echo ""
echo "Applying... (this takes ~8-12 minutes)"
terraform apply -var-file=terraform.tfvars -auto-approve

echo ""
echo "=== Spin Up Complete ==="
echo ""
echo "Live URLs:"
echo "  API:      https://api.fastship-api.com"
echo "  Health:   https://api.fastship-api.com/health"
echo "  Docs:     https://api.fastship-api.com/docs"
echo "  Frontend: https://app.fastship-api.com"
echo ""
echo "Note: ECS tasks may take 2-3 minutes after Terraform completes to pass health checks."
echo "Check status: aws ecs describe-services --cluster dev-fastship-cluster --services dev-api --query 'services[0].runningCount' --profile fastship --region eu-west-1"
echo ""
echo "Remember to spin down when done: ./spin-down.sh"
```

**Step 2: Make executable**

Run: `chmod +x infrastructure/scripts/spin-up.sh`

**Step 3: Commit**

```bash
git add infrastructure/scripts/spin-up.sh
git commit -m "infra: add spin-up.sh script for on-demand service creation"
```

---

### Task 8: Validate with terraform plan (dry run)

**Step 1: Run terraform plan to verify the changes**

Run:
```bash
cd infrastructure/terraform/environments/dev
export AWS_PROFILE=fastship
export AWS_REGION=eu-west-1
terraform plan -var-file=terraform.tfvars
```

Expected output should show:
- **Destroy**: VPC Interface Endpoints (3 endpoints + 1 security group)
- **Destroy**: ECS cluster, services, task definitions, log groups, IAM roles
- **Destroy**: RDS instance, subnet group
- **Destroy**: ElastiCache Redis replication group, subnet group
- **Destroy**: ALB, target group, listeners, security groups
- **Keep**: VPC, subnets, S3 bucket, CloudFront, ECR, S3 Gateway endpoint

**Step 2: Verify resource counts**

The plan should show ~25-35 resources to destroy, 0 to add, 0 to change.
Frontend (S3, CloudFront) and VPC resources should NOT appear in the plan.

**Step 3: If validation passes, commit all changes together**

```bash
git add -A
git commit -m "infra: cost optimization - services toggle ready for apply

Removes VPC Interface Endpoints (~$44/month savings).
Adds services_enabled toggle to gate ECS, RDS, Redis, ALB.
Default: services_enabled = false (tear down to ~$1-3/month).
Spin-up/spin-down scripts for on-demand infrastructure."
```

---

### Task 9: Apply terraform (spin down services)

**IMPORTANT: This destroys live AWS resources. Confirm with user before proceeding.**

**Step 1: Apply the plan**

Run:
```bash
cd infrastructure/terraform/environments/dev
export AWS_PROFILE=fastship
export AWS_REGION=eu-west-1
terraform apply -var-file=terraform.tfvars -auto-approve
```

Expected: All backend services destroyed. Takes ~5-10 minutes.

**Step 2: Verify frontend still works**

Run: `curl -s -o /dev/null -w "%{http_code}" https://app.fastship-api.com`
Expected: `200` (CloudFront + S3 still serving)

**Step 3: Verify backend is down**

Run: `curl -s -o /dev/null -w "%{http_code}" https://api.fastship-api.com/health`
Expected: Connection refused or DNS error (ALB destroyed)

---

### Task 10: Update initiative docs

**Files:**
- Modify: `docs/initiatives/01-aws-infrastructure/progress.md`
- Modify: `docs/initiatives/01-aws-infrastructure/findings.md`

**Step 1: Add progress entry**

Add to progress.md after the "Completed" section:

```markdown
## 2026-03-04 — Cost Optimization: Tear Down to Near-Zero

- Removed 3 VPC Interface Endpoints (ECR API, ECR DKR, CloudWatch Logs) — saving ~$44/month
- Added `services_enabled` Terraform toggle to gate ECS, RDS, Redis, ALB
- Created spin-up.sh / spin-down.sh scripts for on-demand infrastructure
- Spun down all backend services — monthly cost reduced from ~$112 to ~$1-3
- Frontend (S3 + CloudFront) remains live at https://app.fastship-api.com
```

**Step 2: Add finding**

Add to findings.md Architectural Decisions section:

```markdown
### AD-08: Services toggle for portfolio cost management
Added `services_enabled` boolean that gates all backend modules (ECS, RDS, Redis, ALB) via Terraform `count`. Default is `false` (spun down). This is a common pattern for dev/staging environments — infrastructure exists as code even when not running. Portfolio value comes from the Terraform, CI/CD, and architecture, not from 24/7 uptime.
```

**Step 3: Commit**

```bash
git add docs/initiatives/
git commit -m "docs: update initiative tracking with cost optimization progress"
```
