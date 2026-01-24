FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Expose port 8000
EXPOSE 8000

# AWS-specific: Health check endpoint
# Using /health endpoint (also available at /api/v1/health)
# Note: ECS task definition health check overrides this Docker HEALTHCHECK
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run migrations and start (for AWS, separate in task definition)
# Note: In ECS task definition, migrations can be run as a separate command
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
