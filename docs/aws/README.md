# AWS Deployment Documentation

This directory contains comprehensive documentation for deploying FastShip to AWS.

## Documentation Files

- **[DEPLOYMENT-AWS.md](DEPLOYMENT-AWS.md)** - Complete AWS deployment guide with architecture overview, HTTPS setup, and custom domain configuration

## Deployment Status

✅ **Production Ready** - All infrastructure deployed and configured:
- ✅ VPC with public/private subnets
- ✅ ECS Fargate cluster with API and Celery worker
- ✅ RDS PostgreSQL database
- ✅ ElastiCache Redis cache
- ✅ Application Load Balancer with HTTPS/TLS
- ✅ HTTP to HTTPS redirect configured
- ✅ S3 + CloudFront for frontend hosting
- ✅ Custom domain configured (`api.fastship-api.com`, `app.fastship-api.com`)
- ✅ SSL/TLS certificates validated and active

### Live URLs

- **API**: `https://api.fastship-api.com`
- **Frontend**: `https://app.fastship-api.com`

## Quick Links

### Getting Started
1. Follow [DEPLOYMENT-AWS.md](DEPLOYMENT-AWS.md) for complete step-by-step deployment guide
2. Includes HTTPS setup, custom domain configuration, and troubleshooting

### Key Features
- **HTTPS/TLS**: Full SSL/TLS encryption for API and frontend
- **Custom Domain**: Production-ready custom domain configuration
- **Cost Optimized**: Free-tier compatible with VPC endpoints (no NAT Gateway)
- **CI/CD Ready**: GitHub Actions workflows for automated deployment

## Related Documentation

- **[../DEPLOYMENT.md](../DEPLOYMENT.md)** - General deployment guide (Docker, Render, etc.)
- **[../ARCHITECTURE.md](../ARCHITECTURE.md)** - System architecture
- **[../DEVELOPMENT.md](../DEVELOPMENT.md)** - Development setup
