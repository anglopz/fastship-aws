# Initiative 01: AWS Infrastructure

**Scope:** ECS deployment, Terraform IaC, RDS/Redis provisioning, CI/CD pipeline, HTTPS, monitoring
**Covers:** Full AWS production deployment with free-tier optimization

---

## Phase 0 — Terraform Foundation (Complete)

- [x] Step 1: VPC setup — public/private subnets across eu-west-1a/1b, CIDR 10.0.0.0/16
- [x] Step 2: RDS PostgreSQL — db.t3.micro free-tier, PostgreSQL 15.15, private subnet, 1-day backup
- [x] Step 3: ElastiCache Redis — cache.t3.micro free-tier, single node (dev), private subnet
- [x] Step 4: ECR repository — fastship-backend image registry with lifecycle policies
- [x] Step 5: VPC Endpoints — ECR, CloudWatch Logs, S3 (cost optimization vs NAT Gateway)
- [x] Step 6: Security groups — ALB, ECS tasks, RDS, Redis isolated

## Phase 1 — ECS Deployment (Complete)

- [x] Step 1: ECS Fargate cluster — dev-fastship-cluster
- [x] Step 2: API service — 512 CPU / 1024MB RAM task definition, auto-scaling configured
- [x] Step 3: Celery worker — 256 CPU / 512MB RAM, separate ECS service
- [x] Step 4: ALB — target groups, health checks
- [x] Step 5: CloudWatch Logs — /aws/ecs/dev-api and /aws/ecs/dev-celery-worker

## Phase 2 — Frontend Deployment (Complete)

- [x] Step 1: S3 bucket — fastship-dev-frontend, static file hosting
- [x] Step 2: CloudFront distribution — gzip compression, security headers
- [x] Step 3: Route53 — fastship-api.com zone, api/app/root subdomain records

## Phase 3 — HTTPS & Custom Domain (Complete)

- [x] Step 1: ACM certificate for ALB — api.fastship-api.com (eu-west-1), DNS validated
- [x] Step 2: ACM certificate for CloudFront — fastship-api.com, www, app (us-east-1), DNS validated
- [x] Step 3: HTTPS listener on ALB (port 443) with TLS 1.3 policy
- [x] Step 4: HTTP→HTTPS redirect on ALB (port 80, HTTP 301)
- [x] Step 5: CloudFront custom SSL with SNI, TLSv1.2 minimum
- [x] Step 6: Frontend updated to use HTTPS API URL

## Phase 4 — CI/CD Pipeline (Complete)

- [x] Step 1: Backend CI/CD — GitHub Actions: pytest → Docker build → ECR push → ECS deploy
- [x] Step 2: Frontend CI/CD — GitHub Actions: Vite build → S3 deploy → CloudFront invalidation
- [x] Step 3: Terraform CI/CD — GitHub Actions: fmt → validate → plan → apply (main only)

## Phase 5 — Production Hardening (Not Started)

- [ ] Step 1: CloudWatch alarms — ECS CPU/memory, RDS connections, ALB 5xx rate, Redis memory
- [ ] Step 2: WAF on ALB — rate limiting, IP filtering, SQL injection protection
- [ ] Step 3: Multi-AZ RDS — enable for production high availability
- [ ] Step 4: Auto-scaling policies — define ECS scaling triggers (CPU, request count)
- [ ] Step 5: Enhanced monitoring — RDS Performance Insights, ECS Container Insights
- [ ] Step 6: Backup strategy review — increase RDS retention, S3 versioning
- [ ] Step 7: Cost monitoring — AWS Budgets, Cost Explorer alerts
