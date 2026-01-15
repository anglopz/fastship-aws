# FastShip API - Architecture Documentation

## Overview

FastShip is a shipping management API built with FastAPI, designed for scalability, maintainability, and production readiness. The system manages sellers, delivery partners, and shipments with real-time notifications and comprehensive tracking.

## System Architecture

### High-Level Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   FastAPI   │────▶│ PostgreSQL  │     │    Redis    │
│   (API)     │     │  (Database) │     │ (Cache/Queue)│
└─────────────┘     └─────────────┘     └─────────────┘
      │                    │                    │
      └────────────────────┴────────────────────┘
                           │
                    ┌─────────────┐
                    │   Celery     │
                    │   Worker     │
                    └─────────────┘
```

### Technology Stack

- **Web Framework**: FastAPI 0.115.6
- **Database**: PostgreSQL 15 with SQLModel ORM
- **Cache/Queue**: Redis 7
- **Task Queue**: Celery 5.3.4 with Redis broker
- **Authentication**: JWT (python-jose, PyJWT)
- **Email**: FastAPI-Mail
- **SMS**: Twilio
- **Testing**: Pytest with httpx
- **Containerization**: Docker & Docker Compose

## Application Structure

### Directory Layout

```
app/
├── api/
│   ├── routers/          # API route handlers
│   │   ├── seller.py
│   │   ├── delivery_partner.py
│   │   └── shipment.py
│   ├── schemas/          # Pydantic models
│   │   ├── seller.py
│   │   ├── delivery_partner.py
│   │   └── shipment.py
│   └── dependencies.py   # Dependency injection
├── core/
│   ├── security.py        # JWT, password hashing
│   ├── exceptions.py      # Custom exceptions
│   ├── exception_handlers.py  # Error handling
│   ├── middleware.py     # Request logging
│   └── mail.py           # Email service
├── database/
│   ├── models.py         # SQLModel models
│   ├── session.py        # Database session
│   └── redis.py          # Redis connection
├── services/
│   ├── base.py           # BaseService pattern
│   ├── user.py           # UserService (auth)
│   ├── seller.py         # SellerService
│   ├── delivery_partner.py  # DeliveryPartnerService
│   ├── shipment.py       # ShipmentService
│   └── event.py          # EventService
└── celery_app.py         # Celery configuration
```

## Design Patterns

### 1. Service Layer Pattern

All business logic is encapsulated in service classes that inherit from `BaseService`:

```python
class BaseService:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get(self, id: UUID) -> Model | None:
        # Generic get method
        pass
```

**Benefits:**
- Separation of concerns
- Reusable business logic
- Easy testing
- Consistent error handling

### 2. Dependency Injection

FastAPI's dependency injection system is used throughout:

```python
async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session

@router.post("/")
async def create_item(
    item: ItemCreate,
    service: ItemService = Depends(get_service)
):
    return await service.add(item)
```

### 3. Repository Pattern (via SQLModel)

SQLModel provides a clean ORM interface:

```python
class Shipment(SQLModel, table=True):
    id: UUID
    content: str
    status: ShipmentStatus
    # Relationships
    delivery_partner: DeliveryPartner = Relationship(...)
```

## Database Architecture

### Entity Relationship Diagram

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│    Seller    │      │   Shipment   │      │DeliveryPartner│
└──────────────┘      └──────────────┘      └──────────────┘
      │                     │                      │
      │                     │                      │
      │                     ├──────────────────────┤
      │                     │                      │
      │              ┌───────┴───────┐             │
      │              │               │             │
      │         ┌────▼────┐     ┌───▼────┐        │
      │         │  Event  │     │  Tag    │        │
      │         └─────────┘     └─────────┘        │
      │                                           │
      │                                    ┌──────▼──────┐
      │                                    │  Location   │
      │                                    └─────────────┘
      │
┌─────▼─────┐
│  Review   │
└───────────┘
```

### Database Models

1. **User** (Base class)
   - `id`: UUID (primary key)
   - `name`: String
   - `email`: EmailStr (unique)
   - `password_hash`: String
   - `email_verified`: Boolean
   - `created_at`: Timestamp

2. **Seller** (inherits User)
   - Additional seller-specific fields

3. **DeliveryPartner** (inherits User)
   - `max_handling_capacity`: Integer
   - `servicable_locations`: Many-to-Many with Location

4. **Shipment**
   - `id`: UUID
   - `content`: String
   - `weight`: Float (max 25kg)
   - `destination`: Integer (zip code)
   - `status`: Enum (placed, in_transit, delivered, etc.)
   - `client_contact_email`: EmailStr
   - `client_contact_phone`: Optional String
   - Relationships: delivery_partner, events, tags, review

5. **Location**
   - `zip_code`: Integer (primary key)
   - Many-to-Many with DeliveryPartner

6. **ShipmentEvent**
   - `id`: UUID
   - `shipment_id`: UUID (foreign key)
   - `status`: Enum
   - `location`: Integer
   - `description`: String
   - `timestamp`: Timestamp

7. **Review**
   - `id`: UUID
   - `shipment_id`: UUID (one-to-one)
   - `rating`: Integer (1-5)
   - `comment`: Optional String
   - `created_at`: Timestamp

8. **Tag**
   - `id`: UUID
   - `name`: Enum (express, fragile, etc.)
   - Many-to-Many with Shipment

## Authentication & Authorization

### JWT Authentication

Two separate OAuth2 schemes:
- **Seller Authentication**: `/seller/token`
- **Delivery Partner Authentication**: `/partner/token`

**Flow:**
1. User registers → receives email verification link
2. User verifies email → can login
3. User logs in → receives JWT token
4. Token used in `Authorization: Bearer <token>` header

### Token Blacklist

Redis stores blacklisted tokens:
- Token blacklisted on logout
- Token checked on each authenticated request
- Automatic expiration

## Background Tasks

### Celery Integration

**Purpose**: Replace FastAPI BackgroundTasks with distributed task queue

**Tasks:**
- Email sending (verification, notifications)
- SMS sending (delivery notifications)
- Request logging (async log writes)

**Configuration:**
- Broker: Redis
- Backend: Redis
- Worker: Separate Docker container
- Retry: Exponential backoff (max 3 retries)

## API Design

### RESTful Principles

- **GET**: Retrieve resources
- **POST**: Create resources
- **PATCH**: Update resources (partial)
- **DELETE**: Remove resources (if applicable)

### Response Format

**Success:**
```json
{
  "id": "uuid",
  "name": "string",
  ...
}
```

**Error:**
```json
{
  "error": "ErrorClassName",
  "message": "Human-readable message",
  "status_code": 404
}
```

### Status Codes

- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `404`: Not Found
- `409`: Conflict
- `422`: Validation Error
- `500`: Internal Server Error

## Middleware

### Request Logging Middleware

**Features:**
- Request ID generation (8-char UUID)
- Performance metrics (duration)
- Request/response logging
- Async logging via Celery

**Headers:**
- `X-Request-ID`: Unique request identifier

## Error Handling

### Exception Hierarchy

```
FastShipError (base)
├── EntityNotFound (404)
├── AlreadyExists (409)
├── BadCredentials (401)
├── ClientNotAuthorized (401)
├── ClientNotVerified (401)
├── NothingToUpdate (400)
└── DeliveryPartnerNotAvailable (406)
```

**Automatic Registration**: Exception handlers auto-registered via `__subclasses__()`

## Security

### Password Security
- Bcrypt hashing (passlib)
- Password strength validation
- Secure password reset flow

### Token Security
- JWT with HS256 algorithm
- Configurable expiration
- Redis blacklist
- Secure token generation

### Input Validation
- Pydantic models for all inputs
- Email validation
- Type checking
- Constraint validation

## Scalability Considerations

### Database
- UUID primary keys (distributed-friendly)
- Indexed foreign keys
- Connection pooling
- Async queries

### Caching
- Redis for token storage
- Redis for verification codes
- Future: Response caching

### Task Queue
- Celery for async processing
- Horizontal scaling (multiple workers)
- Task retry logic
- Task monitoring

## Monitoring & Logging

### Request Logging
- All requests logged
- Performance metrics
- Request ID tracking
- Error logging

### Log Storage
- File-based logging (`logs/` directory)
- Celery async writes
- Structured log format

## Testing Architecture

### Test Structure
- **Fixtures**: Function-scoped for isolation
- **Test Data**: Centralized constants (`tests/example.py`)
- **Authentication**: Pre-authenticated clients
- **Database**: PostgreSQL test database

### Test Types
- Unit tests (services)
- Integration tests (API endpoints)
- Authentication tests
- Error handling tests

## Deployment Architecture

### Docker Services
- **api**: FastAPI application
- **db**: PostgreSQL database
- **redis**: Redis cache/queue
- **celery_worker**: Celery worker

### Health Checks
- Database health check
- Redis connection check
- API health endpoint

## Future Enhancements

1. **API Gateway**: Rate limiting, load balancing
2. **Monitoring**: Prometheus metrics
3. **Tracing**: Distributed tracing (OpenTelemetry)
4. **Caching**: Response caching layer
5. **WebSockets**: Real-time updates
6. **GraphQL**: Alternative API interface

---

**Last Updated**: January 8, 2026  
**Version**: 1.2.0

