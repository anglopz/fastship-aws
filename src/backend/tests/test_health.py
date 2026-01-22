"""
Tests for health check endpoint
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test the GET /health endpoint (root level for ALB)"""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "service" in data
    assert data["status"] == "healthy"
    assert data["service"] == "FastAPI Backend"
    # Root /health endpoint no longer includes Redis (for fast ALB health checks)
    # Redis status is available at /api/v1/health


@pytest.mark.asyncio
async def test_health_endpoint_detailed(client: AsyncClient):
    """Test the GET /api/v1/health endpoint (detailed with Redis status)"""
    response = await client.get("/api/v1/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "redis" in data  # Detailed endpoint includes Redis status
    assert "service" in data
    assert data["status"] == "healthy"
    assert data["service"] == "FastAPI Backend"
    assert data["redis"] in ["connected", "disconnected"]  # Can be either

