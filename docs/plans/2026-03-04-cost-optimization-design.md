# Design: AWS Cost Optimization — Tear Down to Near-Zero

**Date:** 2026-03-04
**Status:** Approved

---

## Problem

Monthly AWS bill is $112.14 for a portfolio project that was estimated at $20-40/month. The project is used for practicing cloud-native development, not for serving live traffic. Almost no external visitors access the live URLs.

## Cost Breakdown (Current)

| Service | Monthly Cost | Notes |
|---------|-------------|-------|
| VPC Interface Endpoints (3x) | ~$44 | ECR API, ECR DKR, CloudWatch Logs — unnecessary, ECS is in public subnets |
| ECS Fargate (2 tasks 24/7) | ~$33 | API (256 CPU/512MB) + Celery worker (256 CPU/512MB) |
| ALB | ~$18 | Always-on load balancer |
| RDS db.t3.micro | ~$15 | Always-on PostgreSQL |
| ElastiCache Redis | ~$12 | Always-on cache/broker |
| Other (CloudWatch, Route53) | ~$2 | Logs, DNS |
| **Total** | **~$112** | |

## Decision

Implement a "tear down to near-zero" strategy with a Terraform-driven toggle.

### What stays running always (~$1-3/month)
- S3 + CloudFront (frontend stays live, free tier / pennies)
- Route53 hosted zone ($0.50/month)
- ECR (Docker images stored, free tier)
- Terraform state S3 bucket + DynamoDB lock table (pennies)

### What gets removed permanently
- 3 VPC Interface Endpoints (ECR API, ECR DKR, CloudWatch Logs) — serve private subnets but ECS runs in public subnets with `api_use_public_subnets = true`. Pure waste.

### What gets destroyed when spun down (recreatable via Terraform)
- ECS services (API + Celery worker) — desired_count = 0 or destroy
- RDS PostgreSQL instance — destroyed, data lost (acceptable for dev; seed on spin-up)
- ElastiCache Redis — destroyed (no stop option; recreate from Terraform)
- ALB + HTTPS listener — destroyed to save $16/month idle cost

### Implementation: Terraform variable toggle

New variable `services_enabled` (bool):
- `false` (default): ECS, RDS, Redis, ALB/networking all skipped via `count`
- `true`: everything created normally

Two shell scripts:
- `spin-up.sh` — sets `services_enabled = true`, runs `terraform apply`
- `spin-down.sh` — sets `services_enabled = false`, runs `terraform apply`

## Terraform Changes

### 1. Remove VPC Interface Endpoints
**File:** `modules/vpc/vpc_endpoints.tf`
- Delete: `aws_vpc_endpoint.ecr_api`, `aws_vpc_endpoint.ecr_dkr`, `aws_vpc_endpoint.cloudwatch_logs`
- Delete: `aws_security_group.vpc_endpoint` (no longer needed)
- Keep: `aws_vpc_endpoint.s3` (Gateway type, free)

### 2. Add services_enabled toggle
**File:** `environments/dev/terraform.tfvars`
- Add: `services_enabled = false`

**File:** `environments/dev/variables.tf`
- Add: `variable "services_enabled" { type = bool, default = false }`

**File:** `environments/dev/main.tf`
- Wrap RDS module: `count = var.services_enabled ? 1 : 0`
- Wrap Redis module: `count = var.services_enabled ? 1 : 0`
- Wrap networking module (ALB): `count = var.services_enabled ? 1 : 0`
- Wrap ECS module: `count = var.services_enabled ? 1 : 0`
- Frontend module stays always-on (no count)

### 3. Add spin-up/spin-down scripts
**File:** `infrastructure/scripts/spin-up.sh`
- Toggles `services_enabled = true` in terraform.tfvars
- Runs `terraform apply -var-file=terraform.tfvars -auto-approve`
- Prints status and live URLs

**File:** `infrastructure/scripts/spin-down.sh`
- Toggles `services_enabled = false` in terraform.tfvars
- Runs `terraform apply -var-file=terraform.tfvars -auto-approve`
- Confirms resources destroyed

## Cost After Implementation

| State | Monthly Cost |
|-------|-------------|
| Spun down (default) | ~$1-3 |
| Spun up (demo day) | ~$3-5/day prorated |
| **Savings vs current** | **~$109/month (97%)** |

## Data Considerations

- RDS data is lost on spin-down. Database migrations + seed script run on spin-up.
- Redis is ephemeral by nature — no data loss concern.
- ECR images persist — no rebuild needed.
- Frontend on S3 persists — always accessible.
- Terraform state persists in S3 — full infrastructure history preserved.

## Risks

- Spin-up time: ~5-10 minutes for full stack (Terraform apply + ECS task startup)
- RDS creation includes migration time
- ACM certificates may need re-validation if destroyed (keep certs? they're free)
- CI/CD pipelines will fail if services are down (acceptable — manual deploy on spin-up)
