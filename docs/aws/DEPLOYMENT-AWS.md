# FastShip AWS Deployment Guide

This guide covers deploying the FastShip application to AWS using Terraform and CI/CD pipelines.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Infrastructure Setup](#infrastructure-setup)
- [Deployment](#deployment)
- [CI/CD](#cicd)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)

## Architecture Overview

The FastShip application is deployed on AWS using the following services:

- **VPC**: Custom VPC with public and private subnets across multiple availability zones
- **VPC Endpoints**: Interface endpoints for ECR, CloudWatch Logs; Gateway endpoint for S3 (cost-optimized alternative to NAT Gateway)
- **ECS (Fargate)**: Container orchestration for the backend API and Celery workers
- **RDS (PostgreSQL)**: Managed database service
- **ElastiCache (Redis)**: Managed caching and session storage
- **ALB**: Application Load Balancer with HTTPS/TLS and HTTP→HTTPS redirect
- **S3 + CloudFront**: Static frontend hosting with CDN
- **ECR**: Container registry for Docker images
- **CloudWatch Logs**: Centralized logging for ECS tasks
- **ACM**: SSL/TLS certificates for ALB and CloudFront
- **Route53**: DNS management and custom domain configuration

### Architecture Diagram

```
Internet
    |
    v
Route53 (DNS)
    |
    +---> CloudFront (Frontend) ---> S3 Bucket (Static Files)
    |         |
    |         v
    |    https://app.fastship-api.com
    |
    +---> ALB (HTTPS) ---> ECS Fargate (Backend API)
              |                |
              |                +---> RDS PostgreSQL
              |                +---> ElastiCache Redis
              |
              v
    https://api.fastship-api.com
```

## Prerequisites

### Required Tools

1. **AWS CLI** - [Install Guide](https://aws.amazon.com/cli/)
2. **Terraform** >= 1.6.0 - [Install Guide](https://www.terraform.io/downloads)
3. **Docker** - [Install Guide](https://docs.docker.com/get-docker/)
4. **jq** - JSON processor for scripts
5. **AWS Account** with appropriate permissions

### AWS Permissions

Your AWS user/role needs permissions for:
- EC2 (VPC, subnets, security groups)
- ECS (clusters, services, task definitions)
- RDS (database instances)
- ElastiCache (Redis clusters)
- S3 (buckets)
- CloudFront (distributions)
- ECR (repositories)
- IAM (roles and policies)
- CloudWatch (logs)

### Initial AWS Setup

1. **Configure AWS CLI**:
   ```bash
   aws configure
   ```

2. **Create S3 bucket for Terraform state**:
   ```bash
   aws s3 mb s3://fastship-terraform-state --region us-east-1
   ```

3. **Create DynamoDB table for state locking**:
   ```bash
   aws dynamodb create-table \
     --table-name terraform-state-lock \
     --attribute-definitions AttributeName=LockID,AttributeType=S \
     --key-schema AttributeName=LockID,KeyType=HASH \
     --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
     --region us-east-1
   ```

## Infrastructure Setup

### Directory Structure

```
infrastructure/
├── terraform/
│   ├── modules/          # Reusable Terraform modules
│   │   ├── vpc/
│   │   ├── ecs/
│   │   ├── rds/
│   │   ├── redis/
│   │   ├── frontend/
│   │   └── networking/
│   └── environments/     # Environment-specific configs
│       ├── dev/
│       └── prod/
└── scripts/              # Deployment scripts
```

### Environment Configuration

1. **Copy example terraform.tfvars**:
   ```bash
   cd ../../infrastructure/terraform/environments/dev
   cp terraform.tfvars.example terraform.tfvars
   ```

2. **Edit terraform.tfvars** with your values:
   ```hcl
   aws_region = "us-east-1"
   
   db_username = "admin"
   db_password = "your-secure-password"
   
   redis_auth_token = "your-redis-token"
   ```

3. **Initialize Terraform**:
   ```bash
   terraform init
   ```

4. **Plan infrastructure**:
   ```bash
   terraform plan -var-file=terraform.tfvars
   ```

5. **Apply infrastructure**:
   ```bash
   terraform apply -var-file=terraform.tfvars
   ```

### Terraform Variables

Key variables you'll need to configure:

- `aws_region`: AWS region for deployment
- `vpc_cidr`: CIDR block for VPC
- `public_subnet_cidrs`: CIDR blocks for public subnets
- `private_subnet_cidrs`: CIDR blocks for private subnets
- `db_username`: Database master username
- `db_password`: Database master password (use secrets manager in production)
- `redis_auth_token`: Redis authentication token
- `backend_image`: ECR image URI for backend (auto-populated by CI/CD)

## Deployment

### Backend Deployment

1. **Build and push Docker image**:
   ```bash
   ../../infrastructure/scripts/build-and-push.sh dev latest
   ```

2. **Deploy to ECS**:
   ```bash
   ../../infrastructure/scripts/deploy-backend.sh dev <image-uri>
   ```

Or use the Makefile:
```bash
make deploy-backend ENV=dev
```

### Frontend Deployment

```bash
../../infrastructure/scripts/deploy-frontend.sh dev
```

Or update frontend with HTTPS API URL:
```bash
../../infrastructure/scripts/update-frontend-https.sh dev
```

Or use the Makefile:
```bash
make deploy-frontend ENV=dev
```

### Terraform Deployment

```bash
make deploy-terraform ENV=dev
```

Or manually:
```bash
cd ../../infrastructure/terraform/environments/dev
terraform init
terraform plan -var-file=terraform.tfvars
terraform apply -var-file=terraform.tfvars
```

## CI/CD

GitHub Actions workflows are configured for automated deployment:

### Workflows

1. **terraform.yml**: Validates and applies Terraform changes
2. **backend.yml**: Builds, tests, and deploys backend to ECS
3. **frontend.yml**: Builds and deploys frontend to S3/CloudFront

### GitHub Secrets

Configure the following secrets in your GitHub repository:

- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `VITE_API_URL_DEV`: Frontend API URL for dev environment
- `VITE_API_URL_PROD`: Frontend API URL for prod environment

### Workflow Triggers

- **Push to `develop`**: Deploys to dev environment
- **Push to `main`**: Deploys to production environment
- **Pull requests**: Run validation and tests only

## HTTPS & Custom Domain Setup

### Prerequisites

1. **Domain registered** (e.g., `fastship-api.com`)
2. **Route53 hosted zone** created for your domain
3. **ACM certificates** requested:
   - ALB certificate in the same region as ALB (e.g., `eu-west-1`)
   - CloudFront certificate in `us-east-1` (required for CloudFront)

### Certificate Configuration

1. **Request ACM certificates**:
   ```bash
   # ALB certificate (api.fastship-api.com) - same region as ALB
   aws acm request-certificate \
     --domain-name api.fastship-api.com \
     --region eu-west-1 \
     --validation-method DNS
   
   # CloudFront certificate (fastship-api.com, www, app) - us-east-1
   aws acm request-certificate \
     --domain-name fastship-api.com \
     --subject-alternative-names www.fastship-api.com app.fastship-api.com \
     --region us-east-1 \
     --validation-method DNS
   ```

2. **Add DNS validation records** to Route53 (CNAME records from ACM)

3. **Wait for certificate validation** (5-30 minutes)

4. **Update Terraform** with certificate ARNs:
   ```hcl
   # In terraform.tfvars
   # ALB certificate (eu-west-1 region)
   acm_certificate_arn = "arn:aws:acm:eu-west-1:ACCOUNT:certificate/CERT-ID"
   
   # CloudFront certificate (us-east-1 region, required)
   cloudfront_certificate_arn = "arn:aws:acm:us-east-1:ACCOUNT:certificate/CERT-ID"
   
   # CloudFront aliases (custom domains)
   cloudfront_aliases = ["app.fastship-api.com", "fastship-api.com", "www.fastship-api.com"]
   ```

5. **Apply Terraform** to add HTTPS listener and HTTP redirect:
   ```bash
   terraform apply -var-file=terraform.tfvars
   ```

### Route53 DNS Records

Configure A records in Route53:

- `api.fastship-api.com` → ALB DNS name (dualstack)
- `app.fastship-api.com` → CloudFront distribution domain
- `fastship-api.com` → CloudFront distribution domain

### Live URLs

After deployment:
- **API HTTPS**: `https://api.fastship-api.com`
- **API HTTP**: `http://api.fastship-api.com` (redirects to HTTPS)
- **Frontend**: `https://app.fastship-api.com`

## Configuration

### Environment Variables

Backend environment variables are set in the ECS task definition. Common variables:

- `DATABASE_URL`: PostgreSQL connection string (or individual `POSTGRES_*` variables)
- `REDIS_URL`: Redis connection string
- `JWT_SECRET`: JWT signing secret
- `CORS_ORIGINS`: Allowed CORS origins (e.g., `https://app.fastship-api.com`)
- `MAIL_*`: Email configuration

### Database Migrations

Run migrations manually or via CI/CD:

```bash
# Get ECS task ID
TASK_ID=$(aws ecs list-tasks --cluster fastship-dev-cluster --service-name fastship-dev-backend --query 'taskArns[0]' --output text | cut -d'/' -f3)

# Execute migration
aws ecs execute-command \
  --cluster fastship-dev-cluster \
  --task $TASK_ID \
  --container backend \
  --command "alembic upgrade head" \
  --interactive
```

### Secrets Management

For production, use AWS Secrets Manager:

1. Create secrets in AWS Secrets Manager
2. Update ECS task definition to reference secrets
3. Update Terraform to grant ECS access to secrets

## Troubleshooting

### Common Issues

1. **Terraform state locked**:
   ```bash
   # Check for locks in DynamoDB
   aws dynamodb scan --table-name terraform-state-lock
   ```

2. **ECS service not starting**:
   - Check CloudWatch logs
   - Verify task definition is valid
   - Check security group rules
   - Verify image exists in ECR

3. **Database connection issues**:
   - Verify security groups allow traffic from ECS
   - Check database endpoint and credentials
   - Verify database subnet group configuration

4. **Frontend not updating**:
   - Check S3 bucket sync
   - Verify CloudFront invalidation
   - Check CloudFront distribution status

### Useful Commands

```bash
# View ECS service logs
aws logs tail /ecs/fastship-dev-backend --follow

# Check ECS service status
aws ecs describe-services --cluster fastship-dev-cluster --services fastship-dev-backend

# View Terraform outputs
cd ../../infrastructure/terraform/environments/dev
terraform output

# Check RDS status
aws rds describe-db-instances --db-instance-identifier fastship-dev-db

# View CloudFront distribution
aws cloudfront get-distribution --id <distribution-id>
```

## Cost Optimization

- **NAT Gateway disabled** in dev (using VPC endpoints instead)
- **RDS backup retention**: 1 day (free-tier compatible)
- **RDS multi-AZ**: disabled (free-tier compatible)
- **Instance types**: t3.micro (free-tier eligible)
- Use reserved instances for RDS in production
- Enable auto-scaling for ECS based on CPU/memory
- Configure S3 lifecycle policies for old CloudFront logs
- Use CloudWatch alarms to monitor costs
- Consider using Spot instances for non-critical workloads

## Security Best Practices

1. **Never commit secrets** - Use AWS Secrets Manager
2. **Enable encryption** - All data at rest and in transit
3. **Use least privilege** - Minimal IAM permissions
4. **Enable VPC Flow Logs** - Monitor network traffic
5. **Regular security updates** - Keep images and dependencies updated
6. **Use WAF** - Web Application Firewall for ALB (optional)

## Support

For issues or questions:
- Check the [main README](../../README.md)
- Review [architecture documentation](../ARCHITECTURE.md)
- See [deployment readiness checklist](DEPLOYMENT-READINESS.md)
- Open an issue on GitHub
