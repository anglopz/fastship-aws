# Initiative 01: AWS Infrastructure — Findings

---

## Architectural Decisions

### AD-01: VPC Endpoints over NAT Gateway
Chose VPC endpoints for ECR, CloudWatch Logs, and S3 instead of NAT Gateway. VPC endpoints cost ~$28/month vs NAT Gateway ~$32/month plus data processing charges. More importantly, VPC endpoints provide private connectivity without internet routing.

### AD-02: Fargate over EC2 for ECS
Chose Fargate (serverless) over EC2 launch type. No instance management, automatic patching, pay-per-use. Trade-off: slightly higher per-task cost but zero operational overhead for a small team.

### AD-03: Separate ECS services for API and Celery
API and Celery worker run as independent ECS services with different resource allocations (512/1024 vs 256/512). Allows independent scaling and deployment — API can scale horizontally without affecting worker count.

### AD-04: Modular Terraform structure
Infrastructure split into modules (networking, ecs, rds, redis, ecr, frontend, vpc). Each module has its own variables, outputs, and state references. Environments (dev/prod) consume modules with different configurations.

### AD-05: S3 + CloudFront for frontend
Static React app served from S3 via CloudFront CDN. No server-side rendering required. CloudFront provides global edge caching, gzip compression, and security headers. Cost-effective for static content.

### AD-06: Conditional HTTPS listener creation
ALB HTTPS listener and HTTP→HTTPS redirect use Terraform conditionals (`count = var.acm_certificate_arn != "" ? 1 : 0`). Allows infrastructure to work both with and without certificates — useful for initial deployment before cert validation.

### AD-07: TLS 1.3 on ALB, TLS 1.2 minimum on CloudFront
ALB uses `ELBSecurityPolicy-TLS13-1-2-Res-PQ-2025-09` (latest post-quantum ready). CloudFront uses `TLSv1.2_2021` minimum protocol version with SNI-only support.

### AD-08: Services toggle for portfolio cost management
Added `services_enabled` boolean that gates all backend modules (ECS, RDS, Redis, ALB) via Terraform `count`. Default is `false` (spun down). This is a common pattern for dev/staging environments — infrastructure exists as code even when not running. Portfolio value comes from the Terraform, CI/CD, and architecture, not from 24/7 uptime.

### AD-09: VPC Interface Endpoints removed (public subnet architecture)
Removed ECR API, ECR DKR, and CloudWatch Logs Interface endpoints (~$44/month). ECS tasks run in public subnets with `api_use_public_subnets = true`, so they access AWS services directly via the Internet Gateway. Interface endpoints only benefit private subnet workloads.

---

## Infrastructure Trade-offs

### IT-01: Single-AZ Redis in dev
ElastiCache Redis runs single-node in dev for cost savings. Production config enables cluster mode with multi-AZ failover. Risk: dev Redis failure causes downtime, but acceptable for non-production.

### IT-02: 1-day RDS backup retention in dev
Minimal backup retention for free-tier compliance. Production should use 7+ day retention. Trade-off: limited point-in-time recovery window in dev.

### IT-03: ECS task sizing increased from initial spec
API task bumped from 256 CPU / 512MB to 512 CPU / 1024MB for stability. FastAPI + SQLAlchemy + Celery client requires more memory than initially estimated.

---

## AWS Cost Considerations

- Free-tier instances used everywhere possible (db.t3.micro, cache.t3.micro)
- VPC endpoints preferred over NAT Gateway to reduce data transfer costs
- Single-AZ deployments in dev to minimize cross-AZ charges
- CloudFront free tier covers 1TB/month data transfer
- ECS Fargate pricing: ~$0.04048/vCPU/hour + $0.004445/GB/hour

---

## Risks Identified

- **No WAF**: ALB currently unprotected against application-layer attacks
- **No CloudWatch alarms**: Infrastructure running without alerting — failures only detected by manual observation
- **Single instance**: ECS services running with desired count of 1 — no redundancy
- **Documentation drift**: HTTPS-STATUS.md was not updated after certs validated — caused confusion about actual state

---

## Open Questions

- Should we move to a production Terraform workspace with multi-AZ, or keep iterating on dev?
- What monitoring/alerting thresholds are appropriate for the current traffic level?
- What's the cost impact of enabling Container Insights and Performance Insights?
