# Initiative 01: AWS Infrastructure — Progress

**Current Status:** Phases 0–4 Complete, Phase 5 (Production Hardening) Not Started

---

## Completed — Full AWS Deployment with HTTPS

- Terraform modules implemented: networking, ecs, rds, redis, ecr, frontend, vpc
- ECS Fargate cluster running with API and Celery worker services
- RDS PostgreSQL 15.15 operational on db.t3.micro
- ElastiCache Redis 7 operational on cache.t3.micro
- ALB with HTTPS listener (443) and HTTP→HTTPS redirect (80)
- ACM certificates validated and issued for both ALB (eu-west-1) and CloudFront (us-east-1)
- S3 + CloudFront serving React frontend with custom SSL
- Route53 DNS configured for fastship-api.com (api, app, root subdomains)
- GitHub Actions CI/CD pipelines operational for backend, frontend, and Terraform
- ECR registry storing Docker images with commit SHA tags
- CloudWatch Logs capturing ECS container output
- VPC endpoints for ECR/CloudWatch/S3 (NAT Gateway cost avoidance)
- Live URLs: https://api.fastship-api.com, https://app.fastship-api.com, https://fastship-api.com

### Documentation Note

HTTPS-STATUS.md (Jan 16) shows certificates as PENDING_VALIDATION — this was a point-in-time snapshot. DEPLOYMENT-COMPLETE.md (Jan 19) confirms full HTTPS deployment. The status doc was not updated after cert validation.

---

## 2026-03-04 — Cost Optimization: Tear Down to Near-Zero

- Removed 3 VPC Interface Endpoints (ECR API, ECR DKR, CloudWatch Logs) — saving ~$44/month
- Added `services_enabled` Terraform toggle to gate ECS, RDS, Redis, ALB
- Created spin-up.sh / spin-down.sh scripts for on-demand infrastructure
- Spun down all backend services — monthly cost reduced from ~$112 to ~$1-3
- Frontend (S3 + CloudFront) remains live at https://app.fastship-api.com

---

## Next Up

- Phase 5: Production hardening — CloudWatch alarms, WAF, multi-AZ, auto-scaling policies
