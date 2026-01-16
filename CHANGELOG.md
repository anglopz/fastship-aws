# Changelog

All notable changes to the FastShip API project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-01-16

### Added
- **AWS Infrastructure Deployment**:
  - Complete Terraform infrastructure for AWS deployment
  - VPC with public/private subnets across multiple AZs
  - ECS Fargate cluster for backend API and Celery workers
  - RDS PostgreSQL database (free-tier compatible)
  - ElastiCache Redis for caching and task queue
  - Application Load Balancer (ALB) for API routing
  - S3 + CloudFront for frontend static hosting
  - ECR for Docker image registry
  - CloudWatch Logs for centralized logging
  - VPC Endpoints (ECR, CloudWatch Logs, S3) for cost optimization
- **FastAPI Middleware**:
  - Redis-based response caching middleware
  - Rate limiting middleware with sliding window algorithm
  - Optimized health check endpoint (non-blocking Redis check)
- **CI/CD Pipelines**:
  - GitHub Actions workflow for Terraform deployments
  - GitHub Actions workflow for backend Docker image builds
  - GitHub Actions workflow for frontend S3/CloudFront deployments
- **Documentation**:
  - Comprehensive AWS deployment guide
  - Architecture Decision Records (ADRs) for key decisions
  - Free-tier compatibility guide
  - Cost optimization documentation

### Fixed
- **Database Connection Issues**:
  - Fixed `ValueError: invalid interpolation syntax` in Alembic migrations
  - Bypassed ConfigParser interpolation for database URLs with special characters
  - URL-encoded passwords in database connection strings
- **Import Errors**:
  - Fixed `NameError: name 'Response' is not defined` in rate limiting middleware
  - Consistent imports across middleware modules
- **AWS Deployment Issues**:
  - Fixed ECS tasks unable to pull images from ECR (VPC endpoints)
  - Fixed celery worker unable to send logs to CloudWatch (VPC endpoint)
  - Fixed root endpoint `/` 504 errors (optimized middleware skip paths)
  - Fixed health check timeout issues (added Redis ping timeout)
- **RDS Configuration**:
  - Updated PostgreSQL version to 15.15 (latest 15.x available in eu-west-1)
  - Fixed backup retention period for free-tier (1 day max)
  - Fixed password validation (removed invalid characters)

### Changed
- **Cost Optimization**:
  - Replaced NAT Gateway with VPC Endpoints (~$28/month vs ~$32/month)
  - Configured free-tier compatible instance sizes (db.t3.micro, cache.t3.micro)
  - Reduced RDS backup retention to 1 day (free-tier max)
- **Infrastructure**:
  - Modular Terraform structure with reusable modules
  - Environment-specific configurations (dev/prod)
  - S3 backend for Terraform state with DynamoDB locking
- **Middleware Order**:
  - Rate limiting → Caching → Logging (optimized for performance)
  - Skip paths for static/documentation endpoints

### Security
- Rate limiting on authentication endpoints (10 req/min)
- Rate limiting on signup endpoints (5 req/5min)
- IP-based identification with X-Forwarded-For support
- Graceful degradation (fail-open) if Redis unavailable

## [1.2.0] - 2026-01-13

### Added
- Section 15: API Testing Enhancements
  - Centralized test data module (`tests/example.py`)
  - Authentication fixtures (seller_token, partner_token, client_with_auth)
  - ASGITransport for better FastAPI testing
  - Session-scoped fixtures for performance
- Database initialization script (`scripts/init_db.py`)
- Comprehensive API documentation (Section 13)
  - General metadata (contact, license, servers)
  - Endpoint metadata (12 endpoints documented)
  - Model metadata (11 schemas documented)
  - 30+ response examples
- Sections 16-17: Frontend Integration
  - React frontend application
  - Seller and delivery partner dashboards
  - Shipment tracking interface
- Sections 18-20: Deployment
  - Docker optimization
  - Production deployment guide
  - Render.com deployment configuration

### Fixed
- Exception handler print shadowing bug
- Import errors in test files (relative imports)
- Database initialization (all models now imported)
- Test compatibility with new fixtures
- Frontend form submission handlers
- API endpoint routing issues
- CORS configuration

### Changed
- Enhanced `create_db_tables()` to import all models
- Updated test infrastructure with new fixtures
- Improved error handling documentation
- Renumbered sections from 16-35 to 1-20 for clarity

## [1.1.0] - 2026-01-07

### Added
- Section 12: API Middleware
  - Request logging with performance metrics
  - Request ID generation and tracking
  - Async logging via Celery
  - Response headers (X-Request-ID)
- Section 11: Error Handling
  - Custom exception hierarchy (FastShipError)
  - Automatic exception handler registration
  - Consistent JSON error responses
  - Domain-specific exceptions
- Section 9: Celery Integration
  - Distributed task queue with Redis
  - Background email/SMS tasks
  - Task retry logic with exponential backoff
  - Celery worker container

### Changed
- Replaced FastAPI BackgroundTasks with Celery
- Enhanced error handling system
- Improved request logging

## [1.0.0] - 2025-12-30

### Added
- Section 5: Email Confirmation
  - Email verification for sellers and partners
  - Redis token storage (24-hour expiry)
  - Rate-limited confirmation attempts
- Section 6: Password Reset
  - Secure password reset functionality
  - Reset tokens with expiration (1 hour)
  - Email notifications
- Section 7: SMS Verification
  - Twilio SMS integration
  - 6-digit verification codes
  - Email fallback when phone not provided
- Section 8: Review System
  - 5-star rating system
  - Token-based review submission
  - One review per shipment enforcement
  - HTML review form

### Changed
- Added client contact fields to shipments (email required, phone optional)
- Enhanced email service with SMS support

## [0.9.0] - 2025-12-22

### Added
- Core API functionality (Sections 1-4)
- JWT authentication (sellers and delivery partners)
- Shipment management
- PostgreSQL database with UUID support
- Redis integration (cache and token blacklist)
- Docker Compose setup
- Basic test suite

### Changed
- Unified security configuration
- Cleaned up main.py structure
- Improved code organization

---

## Version History

- **1.2.0**: Sections 1-20 complete, production-ready
- **1.1.0**: Infrastructure enhancements (Celery, middleware, error handling)
- **1.0.0**: Authentication enhancements (email, SMS, reviews)
- **0.9.0**: Initial release with core functionality

---

**Format**: [Version] - Date  
**Categories**: Added, Changed, Deprecated, Removed, Fixed, Security
