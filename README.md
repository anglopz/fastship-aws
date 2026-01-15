# FastShip

> A comprehensive shipping management platform with FastAPI backend and React frontend

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.6-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18.2-61DAFB?logo=react)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-3178C6?logo=typescript)](https://www.typescriptlang.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis)](https://redis.io/)

## Quick Start

```bash
# Clone the repository
git clone <repository-url>
cd app

# Start services with Docker Compose
docker-compose up -d

# Access the API
curl http://localhost:8000/health
```

**Frontend:** https://fastship-frontend.onrender.com/  
**API Documentation:** https://fastship-api.onrender.com/docs  
**Alternative Docs:** https://fastship-api.onrender.com/scalar

## Features

- **Authentication**: JWT-based authentication with separate schemes for sellers and delivery partners
- **Shipment Management**: Create, track, and manage shipments with real-time status updates
- **Location-Based Routing**: Automatic assignment of delivery partners based on destination
- **Tagging System**: Add tags to shipments for special handling instructions
- **Email & SMS**: Real-time notifications via email and SMS (Twilio)
- **Review System**: Collect customer reviews after delivery
- **Async Tasks**: Celery-based background task processing
- **Request Logging**: Comprehensive request/response logging with performance metrics
- **API Documentation**: Complete OpenAPI 3.1.0 documentation with examples

## Architecture

### Backend
- **Framework**: FastAPI (async Python web framework)
- **Database**: PostgreSQL 15 with SQLModel ORM
- **Cache/Queue**: Redis (tokens, caching, Celery broker)
- **Task Queue**: Celery with Redis backend
- **Authentication**: JWT tokens with Redis blacklist

### Frontend
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **State Management**: React Context API
- **Data Fetching**: Axios with auto-generated API client
- **UI Components**: Custom component library (shadcn/ui style)

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **CORS**: Configured for frontend-backend communication

## Requirements

- Docker & Docker Compose
- Python 3.11+ (for local backend development)
- Node.js 20+ (for local frontend development)
- PostgreSQL 15 (via Docker)
- Redis 7 (via Docker)

## Installation

### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start the API
uvicorn app.main:app --reload
```

## Documentation

- **[Architecture](docs/ARCHITECTURE.md)** - System design and architecture
- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[Deployment](docs/DEPLOYMENT.md)** - Deployment instructions
- **[Development](docs/DEVELOPMENT.md)** - Development setup and contribution guide
- **[Decisions](docs/DECISIONS.md)** - Architecture decision records (ADRs)

## Testing

```bash
# Run all tests
docker-compose exec api pytest

# Run specific test file
docker-compose exec api pytest tests/test_seller.py

# Run with coverage
docker-compose exec api pytest --cov=app
```

## Project Structure

```
app/
├── app/                   # Backend (FastAPI)
│   ├── api/              # API routers, schemas, dependencies
│   ├── core/             # Security, exceptions, middleware, mail
│   ├── database/         # Models, session, Redis
│   ├── services/         # Business logic services
│   └── templates/        # HTML templates
├── frontend/              # Frontend (React/TypeScript)
│   ├── app/              # React app structure
│   │   ├── components/   # React components
│   │   ├── routes/       # Route components
│   │   ├── contexts/     # React contexts (Auth)
│   │   ├── lib/          # API client and utilities
│   │   └── hooks/        # Custom React hooks
│   ├── package.json      # Node.js dependencies
│   └── vite.config.ts    # Vite configuration
├── tests/                # Backend test suite
├── migrations/           # Alembic database migrations
├── scripts/              # Utility scripts
├── docs/                 # Documentation
├── _reports/             # Section integration reports
└── _section_integration/  # Section integration files
```

## Configuration

Environment variables (see `env.example`):

- **Database**: `POSTGRES_*` variables
- **Redis**: `REDIS_HOST`, `REDIS_PORT`
- **JWT**: `JWT_SECRET`, `JWT_ALGORITHM`
- **Email**: `MAIL_*` variables
- **SMS**: `TWILIO_*` variables

## API Endpoints

### Authentication
- `POST /seller/signup` - Register seller
- `POST /seller/token` - Login seller
- `POST /partner/signup` - Register delivery partner
- `POST /partner/token` - Login delivery partner

### Shipments
- `GET /shipment/` - Get shipment by ID
- `POST /shipment/` - Create shipment
- `PATCH /shipment/` - Update shipment
- `GET /shipment/track` - Track shipment (HTML)
- `POST /shipment/cancel` - Cancel shipment

See [API Reference](docs/API_REFERENCE.md) for complete documentation.

## Status

- **Sections Completed**: 1-20
- **Production Ready**: Yes
- **Test Coverage**: Comprehensive
- **Database**: 10 tables initialized

## Contributing

See [Development Guide](docs/DEVELOPMENT.md) for contribution guidelines.

## License

MIT License - see LICENSE file for details

## Links

- **Frontend**: https://fastship-frontend.onrender.com/
- **API Docs**: https://fastship-api.onrender.com/docs
- **Scalar Docs**: https://fastship-api.onrender.com/scalar
- **Health Check**: https://fastship-api.onrender.com/health
- **Project Analysis**: [_PROJECT_ANALYSIS.md](_PROJECT_ANALYSIS.md)
- **Changelog**: [CHANGELOG.md](CHANGELOG.md)
- **Roadmap**: [ROADMAP.md](ROADMAP.md)

---

**Built with FastAPI**
