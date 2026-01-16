"""
Example tests using Section 30 fixtures and test data
Section 30: API Testing Integration - Demonstration
"""
import pytest
from httpx import AsyncClient

# Import test data - use relative import
from . import example


@pytest.mark.asyncio
async def test_submit_shipment_auth(client: AsyncClient):
    """
    Test that shipment creation requires authentication.
    
    Section 30: Using new fixtures and example data.
    """
    response = await client.post(
        "/shipment/",
        json={},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_submit_shipment(client_with_seller_auth: AsyncClient):
    """
    Test shipment creation with authenticated seller.
    
    Section 30: Using client_with_seller_auth fixture for pre-authenticated requests.
    """
    # Submit Shipment using example data
    response = await client_with_seller_auth.post(
        "/shipment/",
        json=example.SHIPMENT,
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["content"] == example.SHIPMENT["content"]
    assert data["weight"] == example.SHIPMENT["weight"]
    assert data["destination"] == example.SHIPMENT["destination"]
    
    # Get Shipment
    shipment_id = data["id"]
    response = await client_with_seller_auth.get(
        "/shipment/",
        params={"id": shipment_id},
    )
    
    # Check if the shipment is created
    assert response.status_code == 200
    shipment_data = response.json()
    assert shipment_data["id"] == shipment_id
    assert shipment_data["content"] == example.SHIPMENT["content"]


@pytest.mark.asyncio
async def test_submit_shipment_with_token(client: AsyncClient, seller_token: str):
    """
    Test shipment creation using seller_token fixture.
    
    Section 30: Using seller_token fixture for manual token usage.
    """
    response = await client.post(
        "/shipment/",
        json=example.SHIPMENT,
        headers={"Authorization": f"Bearer {seller_token}"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["content"] == example.SHIPMENT["content"]


@pytest.mark.asyncio
async def test_get_shipment_public(client: AsyncClient, seller_token: str):
    """
    Test that shipment retrieval is public (no auth required).
    
    Section 30: Demonstrates public endpoint testing.
    """
    # First create a shipment
    create_response = await client.post(
        "/shipment/",
        json=example.SHIPMENT,
        headers={"Authorization": f"Bearer {seller_token}"},
    )
    assert create_response.status_code == 200
    shipment_id = create_response.json()["id"]
    
    # Get shipment without authentication (public endpoint)
    response = await client.get(
        "/shipment/",
        params={"id": shipment_id},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == shipment_id
    assert data["content"] == example.SHIPMENT["content"]

