"""
Tests for health check endpoint
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_endpoint(client: AsyncClient):
    """Test the GET /health endpoint"""
    response = await client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    
    assert "status" in data
    assert "redis" in data
    assert "service" in data
    assert data["status"] == "healthy"
    assert data["service"] == "FastAPI Backend"
    # Redis status can be "connected" or "disconnected" depending on test environment
    assert data["redis"] in ["connected", "disconnected"]

