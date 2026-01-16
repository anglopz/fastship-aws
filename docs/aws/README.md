# AWS Deployment Documentation

This directory contains comprehensive documentation for deploying FastShip to AWS.

## Documentation Files

- **[DEPLOYMENT-AWS.md](DEPLOYMENT-AWS.md)** - Complete AWS deployment guide with architecture overview
- **[DEPLOYMENT-READINESS.md](DEPLOYMENT-READINESS.md)** - Pre-deployment checklist and verification
- **[FREE-TIER-VERIFICATION.md](FREE-TIER-VERIFICATION.md)** - Free tier compatibility verification and cost analysis
- **[NAT-GATEWAY-COSTS.md](NAT-GATEWAY-COSTS.md)** - NAT Gateway cost optimization guide

## Quick Links

### Getting Started
1. Read [DEPLOYMENT-READINESS.md](DEPLOYMENT-READINESS.md) for pre-deployment checklist
2. Follow [DEPLOYMENT-AWS.md](DEPLOYMENT-AWS.md) for step-by-step deployment
3. Check [FREE-TIER-VERIFICATION.md](FREE-TIER-VERIFICATION.md) for cost optimization

### Terraform-Specific Docs
- **Backend Setup**: See `../../infrastructure/terraform/README-BACKEND.md`
- **Terraform Setup**: See `../../infrastructure/terraform/SETUP.md`

## Documentation Structure

```
docs/aws/
├── README.md (this file)
├── DEPLOYMENT-AWS.md          # Main AWS deployment guide
├── DEPLOYMENT-READINESS.md     # Pre-deployment checklist
├── FREE-TIER-VERIFICATION.md  # Free tier compatibility
└── NAT-GATEWAY-COSTS.md        # Cost optimization

infrastructure/terraform/
├── README-BACKEND.md           # Terraform backend setup (operational)
└── SETUP.md                    # Terraform setup instructions (operational)
```

## Related Documentation

- **[../DEPLOYMENT.md](../DEPLOYMENT.md)** - General deployment guide (Docker, Render, etc.)
- **[../ARCHITECTURE.md](../ARCHITECTURE.md)** - System architecture
- **[../DEVELOPMENT.md](../DEVELOPMENT.md)** - Development setup
