# Architecture Decision Records (ADRs)

This document records architectural decisions made for the FastShip API project.

## Format

Each ADR follows this format:
- **Status**:** Proposed | Accepted | Deprecated | Superseded
- **Context**: The issue motivating this decision
- **Decision**: The change we're proposing or have agreed to implement
- **Consequences**: What becomes easier or more difficult

---

## ADR-001: Use FastAPI Framework

**Status**: Accepted  
**Date**: 2025-12-22

### Context

Need a modern, fast Python web framework for building REST APIs.

### Decision

Use FastAPI as the primary web framework.

### Consequences

**Positive:**
- Automatic OpenAPI/Swagger documentation
- Type hints and validation with Pydantic
- Async/await support
- High performance
- Modern Python features

**Negative:**
- Learning curve for team members
- Less mature ecosystem than Django/Flask

---

## ADR-002: Use SQLModel for ORM

**Status**: Accepted  
**Date**: 2025-12-22

### Context

Need an ORM that works well with FastAPI and provides type safety.

### Decision

Use SQLModel (built on SQLAlchemy) for database operations.

### Consequences

**Positive:**
- Type safety with Pydantic models
- Automatic schema generation
- Works seamlessly with FastAPI
- SQLAlchemy power with Pydantic validation

**Negative:**
- Newer library (less community resources)
- Some SQLAlchemy features may not be available

---

## ADR-003: PostgreSQL as Primary Database

**Status**: Accepted  
**Date**: 2025-12-22

### Context

Need a robust, production-ready database with UUID and ARRAY support.

### Decision

Use PostgreSQL as the primary database (no SQLite fallback in production).

### Consequences

**Positive:**
- UUID support
- ARRAY support (for serviceable locations)
- Production-ready
- Advanced features available

**Negative:**
- Requires PostgreSQL installation
- More complex than SQLite

---

## ADR-004: UUID Primary Keys

**Status**: Accepted  
**Date**: 2025-12-22

### Context

Need primary keys that work well in distributed systems.

### Decision

Use UUID v4 as primary keys for all entities.

### Consequences

**Positive:**
- Globally unique identifiers
- No sequential ID exposure
- Works well in distributed systems
- Better security (no ID enumeration)

**Negative:**
- Slightly larger storage
- Slightly slower than integer keys
- Less human-readable

---

## ADR-005: Service Layer Pattern

**Status**: Accepted  
**Date**: 2025-12-22

### Context

Need to separate business logic from API routes.

### Decision

Implement a service layer pattern with `BaseService` class.

### Consequences

**Positive:**
- Clear separation of concerns
- Reusable business logic
- Easier testing
- Consistent error handling

**Negative:**
- Additional abstraction layer
- More files to maintain

---

## ADR-006: JWT Authentication with Redis Blacklist

**Status**: Accepted  
**Date**: 2025-12-22

### Context

Need stateless authentication that supports logout.

### Decision

Use JWT tokens with Redis blacklist for logout functionality.

### Consequences

**Positive:**
- Stateless authentication
- Scalable
- Supports logout via blacklist
- Fast token validation

**Negative:**
- Requires Redis
- Token size larger than session IDs
- Cannot revoke tokens without blacklist check

---

## ADR-007: Separate Authentication Schemes

**Status**: Accepted  
**Date**: 2025-12-22

### Context

Sellers and delivery partners have different permissions and endpoints.

### Decision

Use separate OAuth2 schemes for sellers and delivery partners.

### Consequences

**Positive:**
- Clear separation of concerns
- Different token endpoints
- Better security (separate scopes possible)
- Clearer API documentation

**Negative:**
- More complex authentication setup
- Two token endpoints to maintain

---

## ADR-008: Celery for Background Tasks

**Status**: Accepted  
**Date**: 2026-01-07

### Context

Need distributed task queue for email/SMS and logging.

### Decision

Replace FastAPI BackgroundTasks with Celery.

### Consequences

**Positive:**
- Distributed task processing
- Task retry logic
- Task monitoring
- Horizontal scaling
- Persistent task queue

**Negative:**
- Additional infrastructure (Celery worker)
- More complex setup
- Requires Redis broker

---

## ADR-009: Custom Exception Hierarchy

**Status**: Accepted  
**Date**: 2026-01-07

### Context

Need consistent error handling across the application.

### Decision

Implement custom exception hierarchy with `FastShipError` base class.

### Consequences

**Positive:**
- Consistent error format
- Automatic handler registration
- Type-safe error handling
- Clear error messages

**Negative:**
- Additional exception classes to maintain
- Need to remember to use custom exceptions

---

## ADR-010: Request Logging Middleware

**Status**: Accepted  
**Date**: 2026-01-07

### Context

Need comprehensive request/response logging for monitoring and debugging.

### Decision

Implement request logging middleware with Celery async logging.

### Consequences

**Positive:**
- All requests logged
- Performance metrics
- Request ID tracking
- Non-blocking logging

**Negative:**
- Additional overhead
- Requires Celery
- Log storage needed

---

## ADR-011: Many-to-Many Relationships

**Status**: Accepted  
**Date**: 2026-01-07

### Context

Need to model relationships like shipment tags and partner locations.

### Decision

Use SQLModel many-to-many relationships instead of ARRAY fields.

### Consequences

**Positive:**
- Normalized database
- Better query performance
- Easier to query relationships
- Standard SQL patterns

**Negative:**
- More complex queries
- Additional join tables
- Breaking change (removed ARRAY field)

---

## ADR-012: Comprehensive API Documentation

**Status**: Accepted  
**Date**: 2026-01-08

### Context

Need production-ready API documentation with examples.

### Decision

Add comprehensive metadata at all levels (app, endpoint, model).

### Consequences

**Positive:**
- Self-documenting API
- Better developer experience
- Code generation possible
- Clear examples

**Negative:**
- More code to maintain
- Documentation can get out of sync

---

## ADR-013: Enhanced Testing Infrastructure

**Status**: Accepted  
**Date**: 2026-01-08

### Context

Need better testing infrastructure with reusable fixtures and test data.

### Decision

Implement centralized test data, authentication fixtures, and ASGITransport.

### Consequences

**Positive:**
- Easier test writing
- Consistent test data
- Pre-authenticated clients
- Better FastAPI testing

**Negative:**
- Additional fixtures to maintain
- More complex test setup

---

## ADR-014: Database Auto-Initialization

**Status**: Accepted  
**Date**: 2026-01-08

### Context

Need tables to be created automatically on startup.

### Decision

Use FastAPI lifespan handler to create tables on startup.

### Consequences

**Positive:**
- No manual migration step
- Tables always exist
- Simpler deployment

**Negative:**
- Less control over migrations
- May create tables in production (if not careful)

---

## Superseded Decisions

### ADR-015: SQLite Fallback (Superseded)

**Status**: Superseded by ADR-003  
**Date**: 2025-12-22

**Original Decision**: Support SQLite as fallback for development.

**Superseded By**: ADR-003 (PostgreSQL as primary database)

**Reason**: UUID and ARRAY support require PostgreSQL. Development should match production.

---

## ADR-015: VPC Endpoints Instead of NAT Gateway (Cost Optimization)

**Status**: Accepted  
**Date**: 2026-01-16

### Context

ECS tasks in private subnets need internet access for:
- Pulling Docker images from ECR
- Sending logs to CloudWatch
- Accessing S3 buckets

NAT Gateway costs ~$32/month, which exceeds free tier budget for portfolio projects.

### Decision

Use VPC Endpoints (Interface and Gateway) instead of NAT Gateway for private subnet connectivity.

**Implementation:**
- **ECR Interface Endpoints** (API + DKR): ~$14/month (2 AZs × $7/AZ)
- **CloudWatch Logs Interface Endpoint**: ~$14/month (2 AZs × $7/AZ)
- **S3 Gateway Endpoint**: Free (no data transfer charges)

**Total Cost**: ~$28/month (vs ~$32/month for NAT Gateway)
**Free Tier Savings**: $32/month avoided

### Consequences

**Positive:**
- Lower cost than NAT Gateway (~12% savings)
- Better security (private connectivity to AWS services)
- No data transfer charges for S3 endpoint
- Suitable for free-tier portfolio projects

**Negative:**
- More complex setup (multiple endpoints)
- Only works for AWS services (not general internet access)
- Interface endpoints charge per AZ (costs scale with AZs)
- Requires careful security group configuration

**Trade-offs:**
- If general internet access is needed, NAT Gateway is still required
- For portfolio/free-tier projects, VPC endpoints are ideal
- Production environments may prefer NAT Gateway for simplicity

---

## ADR-016: FastAPI Response Caching with Redis

**Status**: Accepted  
**Date**: 2026-01-15

### Context

Need to reduce database load and improve API response times for frequently accessed endpoints.

### Decision

Implement Redis-based response caching middleware for FastAPI.

**Features:**
- Cache GET requests only
- Configurable TTL per endpoint
- Cache invalidation support
- Graceful degradation if Redis unavailable

### Consequences

**Positive:**
- Reduced database load
- Faster response times for cached endpoints
- Scalable (Redis handles cache)
- Non-blocking (fail-open if Redis down)

**Negative:**
- Additional Redis dependency
- Cache invalidation complexity
- Memory usage for cached responses

---

## ADR-017: Rate Limiting with Redis Sliding Window

**Status**: Accepted  
**Date**: 2026-01-15

### Context

Need to protect API endpoints from abuse, brute-force attacks, and ensure fair resource usage.

### Decision

Implement Redis-based rate limiting middleware using sliding window algorithm.

**Configuration:**
- Stricter limits for authentication endpoints (10 req/min)
- Stricter limits for signup endpoints (5 req/5min)
- Default: 100 requests per minute
- IP-based identification (considering X-Forwarded-For from ALB)

### Consequences

**Positive:**
- Protection against brute-force attacks
- Fair resource usage
- Configurable per endpoint
- Graceful degradation (fail-open if Redis unavailable)

**Negative:**
- Additional Redis dependency
- Requires accurate IP identification
- May block legitimate users during DDoS

---

**Last Updated**: January 16, 2026

