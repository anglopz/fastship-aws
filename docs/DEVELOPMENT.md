# FastShip API - Development Guide

## Getting Started

### Prerequisites

- Python 3.11+ (for backend)
- Node.js 20+ (for frontend)
- Docker & Docker Compose
- Git
- Code editor (VS Code recommended)

### Initial Setup

```bash
# Clone repository
git clone <repository-url>
cd app

# Copy environment file
cp env.example .env

# Start services
docker-compose up -d

# Verify setup
curl http://localhost:8000/health

# Frontend will be available at http://localhost:5173
```

## Development Environment

### Local Development (Without Docker)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/fastapi_db"
export REDIS_URL="redis://localhost:6379"

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### Docker Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Execute commands in container
docker-compose exec api python scripts/init_db.py

# Stop services
docker-compose down
```

## Project Structure

```
app/
├── app/                  # Backend (FastAPI)
│   ├── api/              # API layer
│   │   ├── routers/      # Route handlers
│   │   ├── schemas/      # Pydantic models
│   │   └── dependencies.py
│   ├── core/             # Core functionality
│   │   ├── security.py   # JWT, passwords
│   │   ├── exceptions.py # Custom exceptions
│   │   ├── middleware.py # Request logging
│   │   └── mail.py       # Email service
│   ├── database/         # Database layer
│   │   ├── models.py     # SQLModel models
│   │   ├── session.py     # Database session
│   │   └── redis.py      # Redis connection
│   ├── services/         # Business logic
│   │   ├── base.py       # BaseService
│   │   ├── user.py       # UserService
│   │   └── ...
│   └── celery_app.py     # Celery tasks
├── frontend/             # Frontend (React + TypeScript)
│   ├── app/              # Application code
│   │   ├── components/   # React components
│   │   ├── routes/       # Page routes
│   │   ├── contexts/     # React contexts
│   │   └── lib/          # Utilities & API client
│   ├── public/           # Static assets
│   ├── package.json      # Dependencies
│   └── vite.config.ts    # Vite configuration
├── tests/                # Test suite
├── migrations/           # Alembic migrations
├── scripts/             # Utility scripts
└── docs/                # Documentation
```

## Coding Standards

### Python Style

- Follow PEP 8
- Use type hints
- Maximum line length: 88 characters (Black default)
- Use `black` for formatting
- Use `isort` for import sorting

### Code Organization

1. **Services**: Business logic goes in `app/services/`
2. **Routers**: API endpoints in `app/api/routers/`
3. **Schemas**: Pydantic models in `app/api/schemas/`
4. **Models**: Database models in `app/database/models.py`

### Naming Conventions

- **Classes**: PascalCase (`ShipmentService`)
- **Functions**: snake_case (`get_shipment`)
- **Constants**: UPPER_SNAKE_CASE (`MAX_WEIGHT`)
- **Files**: snake_case (`shipment_service.py`)

## Testing

### Running Tests

```bash
# All tests
docker-compose exec api pytest

# Specific test file
docker-compose exec api pytest tests/test_seller.py

# With verbose output
docker-compose exec api pytest -v

# With coverage
docker-compose exec api pytest --cov=app
```

### Writing Tests

1. Use fixtures from `tests/conftest.py`
2. Use test data from `tests/example.py`
3. Use authentication fixtures for authenticated endpoints
4. Test both success and error cases

Example:

```python
@pytest.mark.asyncio
async def test_create_shipment(client_with_seller_auth: AsyncClient):
    response = await client_with_seller_auth.post(
        "/shipment/",
        json=example.SHIPMENT,
    )
    assert response.status_code == 200
```

## Database Migrations

### Creating Migrations

```bash
# Auto-generate migration
docker-compose exec api alembic revision --autogenerate -m "description"

# Create empty migration
docker-compose exec api alembic revision -m "description"
```

### Applying Migrations

```bash
# Apply all migrations
docker-compose exec api alembic upgrade head

# Rollback one migration
docker-compose exec api alembic downgrade -1
```

## Adding New Features

### 1. Database Model

Add to `app/database/models.py`:

```python
class NewModel(SQLModel, table=True):
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    name: str
    # ... other fields
```

### 2. Schema

Add to `app/api/schemas/`:

```python
class NewModelCreate(BaseModel):
    name: str

class NewModelRead(BaseModel):
    id: UUID
    name: str
```

### 3. Service

Add to `app/services/`:

```python
class NewModelService(BaseService[NewModel, NewModelCreate, NewModelUpdate]):
    # Implement business logic
    pass
```

### 4. Router

Add to `app/api/routers/`:

```python
@router.post("/", response_model=NewModelRead)
async def create_item(
    item: NewModelCreate,
    service: NewModelService = Depends(get_service)
):
    return await service.add(item)
```

## Debugging

### API Logs

```bash
# View API logs
docker-compose logs -f api

# View specific service logs
docker-compose logs -f celery_worker
```

### Database Access

```bash
# Connect to database
docker-compose exec db psql -U postgres -d fastapi_db

# Run SQL queries
docker-compose exec db psql -U postgres -d fastapi_db -c "SELECT * FROM seller;"
```

### Redis Access

```bash
# Connect to Redis CLI
docker-compose exec redis redis-cli

# View keys
docker-compose exec redis redis-cli KEYS "*"
```

## Code Quality Tools

### Formatting

```bash
# Format code
black app/ tests/

# Check formatting
black --check app/ tests/
```

### Import Sorting

```bash
# Sort imports
isort app/ tests/

# Check imports
isort --check app/ tests/
```

### Linting

```bash
# Run linter (if configured)
pylint app/
```

## Testing Best Practices

1. **Isolation**: Each test should be independent
2. **Fixtures**: Use fixtures for common setup
3. **Test Data**: Use centralized test data constants
4. **Coverage**: Aim for high test coverage
5. **Naming**: Use descriptive test names

## Git Workflow

### Branch Naming

- `feature/description`: New features
- `fix/description`: Bug fixes
- `docs/description`: Documentation
- `refactor/description`: Code refactoring

### Commit Messages

Follow conventional commits:

```
feat: Add shipment tracking endpoint
fix: Resolve authentication token issue
docs: Update API documentation
refactor: Simplify service layer
```

## Common Tasks

### Adding a New Endpoint

1. Add route handler in `app/api/routers/`
2. Add schema in `app/api/schemas/`
3. Add service method if needed
4. Add tests in `tests/`
5. Update API documentation

### Adding a New Model

1. Add model to `app/database/models.py`
2. Create migration: `alembic revision --autogenerate`
3. Add schemas in `app/api/schemas/`
4. Add service in `app/services/`
5. Add router endpoints
6. Add tests

### Debugging Issues

1. Check logs: `docker-compose logs -f api`
2. Check database: Connect via psql
3. Check Redis: Connect via redis-cli
4. Use debugger: Add breakpoints in code
5. Check tests: Run relevant tests

## Resources

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **SQLModel Docs**: https://sqlmodel.tiangolo.com
- **Pytest Docs**: https://docs.pytest.org
- **Celery Docs**: https://docs.celeryq.dev

## Getting Help

1. Check existing documentation
2. Review code examples in the codebase
3. Check test files for usage examples
4. Review architecture documentation

---

**Last Updated**: January 8, 2026

