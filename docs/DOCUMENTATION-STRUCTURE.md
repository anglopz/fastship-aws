# Documentation Structure

This document explains the organization of all documentation in the FastShip project.

## Documentation Organization

### 📁 `docs/` - General Documentation

**Location**: Root-level documentation for the entire project

- **ARCHITECTURE.md** - System design and architecture patterns
- **API_REFERENCE.md** - Complete API endpoint documentation
- **DEPLOYMENT.md** - General deployment guide (Docker, Render, AWS)
- **DEVELOPMENT.md** - Development setup and coding standards
- **DECISIONS.md** - Architecture Decision Records (ADRs)
- **README.md** - Documentation index

### 📁 `docs/aws/` - AWS-Specific Documentation

**Location**: AWS deployment guides and references

**Rationale**: These are general AWS deployment guides that apply to the entire AWS deployment process, not just Terraform operations.

- **DEPLOYMENT-AWS.md** - Complete AWS deployment guide (Terraform, ECS, RDS, etc.)
- **DEPLOYMENT-READINESS.md** - Pre-deployment checklist and verification
- **FREE-TIER-VERIFICATION.md** - Free tier compatibility and cost analysis
- **NAT-GATEWAY-COSTS.md** - NAT Gateway cost optimization guide
- **README.md** - AWS documentation index

### 📁 `infrastructure/terraform/` - Terraform Operational Docs

**Location**: Terraform-specific operational documentation

**Rationale**: These are context-specific to Terraform operations and are best kept near the Terraform code they reference.

- **SETUP.md** - Terraform setup and initialization instructions
- **README-BACKEND.md** - Terraform backend (S3/DynamoDB) setup guide

## Decision Rationale

### Why Some Docs in `docs/aws/` and Others in `infrastructure/terraform/`?

**Moved to `docs/aws/`** (General AWS guides):
- ✅ **DEPLOYMENT-AWS.md** - High-level AWS deployment guide
- ✅ **DEPLOYMENT-READINESS.md** - Pre-deployment checklist (applies to all AWS deployment)
- ✅ **FREE-TIER-VERIFICATION.md** - Cost analysis and free tier guide
- ✅ **NAT-GATEWAY-COSTS.md** - Cost optimization guide

**Kept in `infrastructure/terraform/`** (Operational docs):
- ✅ **SETUP.md** - Step-by-step Terraform setup (context-specific)
- ✅ **README-BACKEND.md** - Backend configuration reference (operational)

### Benefits of This Organization

1. **Clear separation**: General guides vs. operational references
2. **Easy discovery**: AWS docs in one place (`docs/aws/`)
3. **Context preservation**: Terraform operational docs stay with code
4. **Better navigation**: Logical grouping by purpose

## File Paths Reference

### From Project Root

```bash
# General documentation
docs/README.md
docs/DEPLOYMENT.md
docs/ARCHITECTURE.md

# AWS documentation
docs/aws/DEPLOYMENT-AWS.md
docs/aws/DEPLOYMENT-READINESS.md
docs/aws/FREE-TIER-VERIFICATION.md
docs/aws/NAT-GATEWAY-COSTS.md

# Terraform operational docs
infrastructure/terraform/SETUP.md
infrastructure/terraform/README-BACKEND.md
```

### From `docs/aws/`

```bash
# Reference Terraform docs
../../infrastructure/terraform/SETUP.md
../../infrastructure/terraform/README-BACKEND.md

# Reference general docs
../DEPLOYMENT.md
../ARCHITECTURE.md
```

## Quick Links

- **Getting Started**: [docs/README.md](README.md)
- **AWS Deployment**: [docs/aws/DEPLOYMENT-AWS.md](aws/DEPLOYMENT-AWS.md)
- **Deployment Checklist**: [docs/aws/DEPLOYMENT-READINESS.md](aws/DEPLOYMENT-READINESS.md)
- **Terraform Setup**: [infrastructure/terraform/SETUP.md](../../infrastructure/terraform/SETUP.md)
- **Backend Setup**: [infrastructure/terraform/README-BACKEND.md](../../infrastructure/terraform/README-BACKEND.md)
