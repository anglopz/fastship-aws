.PHONY: help setup venv install deps up down logs test clean dev-setup

help:
	@echo "FastShip Backend - Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make dev-setup  - Set up local development environment (venv + deps)"
	@echo "  make venv       - Create virtual environment only"
	@echo "  make install    - Install dependencies in virtual environment"
	@echo ""
	@echo "Docker:"
	@echo "  make up         - Start Docker services (db, redis, api, celery)"
	@echo "  make down       - Stop Docker services"
	@echo "  make logs       - View Docker logs"
	@echo "  make rebuild    - Rebuild Docker images"
	@echo ""
	@echo "Development:"
	@echo "  make dev        - Start development server (local, not Docker)"
	@echo "  make migrate    - Run database migrations"
	@echo "  make test       - Run tests"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean      - Clean up generated files"
	@echo ""
	@echo "For detailed local development guide, see: dev/README.md"

dev-setup:
	@echo "Setting up local development environment..."
	@chmod +x dev/setup-venv.sh
	@./dev/setup-venv.sh
	@echo ""
	@echo "✅ Local development setup complete!"
	@echo "See dev/README.md for full development guide"

setup: dev-setup
	@echo "Note: 'make setup' is deprecated, use 'make dev-setup'"

venv:
	@if [ ! -d ".venv" ]; then \
		echo "Creating virtual environment..."; \
		python3 -m venv .venv; \
		echo "✅ Virtual environment created"; \
	else \
		echo "⚠️  Virtual environment already exists"; \
	fi

install:
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make venv' first"; \
		exit 1; \
	fi
	@echo "Installing dependencies..."
	@.venv/bin/pip install --upgrade pip
	@.venv/bin/pip install -r requirements.txt
	@echo "✅ Dependencies installed"

up:
	@echo "Starting Docker services..."
	docker-compose up -d
	@echo "✅ Services started"
	@echo "Run 'make logs' to view logs"

down:
	@echo "Stopping Docker services..."
	docker-compose down
	@echo "✅ Services stopped"

logs:
	docker-compose logs -f

rebuild:
	@echo "Rebuilding Docker images..."
	docker-compose build --no-cache
	@echo "✅ Images rebuilt"

dev:
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make dev-setup' first"; \
		exit 1; \
	fi
	@echo "Starting development server..."
	@.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make dev-setup' first"; \
		exit 1; \
	fi
	@echo "Running database migrations..."
	@.venv/bin/alembic upgrade head
	@echo "✅ Migrations complete"

test:
	@if [ ! -d ".venv" ]; then \
		echo "❌ Virtual environment not found. Run 'make dev-setup' first"; \
		exit 1; \
	fi
	@echo "Running tests..."
	@.venv/bin/pytest -v

clean:
	@echo "Cleaning up..."
	rm -rf __pycache__ .pytest_cache .coverage htmlcov
	find . -type d -name __pycache__ -exec rm -r {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "✅ Cleanup complete"
