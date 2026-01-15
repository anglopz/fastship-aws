"""
Tests for shipment endpoints including Section 19 HTML tracking
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import ShipmentStatus


@pytest.mark.asyncio
async def test_shipment_track_endpoint_exists(client: AsyncClient, test_session: AsyncSession):
    """Test that /shipment/track endpoint exists and returns HTML"""
    # First create a delivery partner (required for shipment assignment)
    partner_data = {
        "name": "Test Partner",
        "email": "testpartner@example.com",
        "password": "testpass123",
        "serviceable_zip_codes": [10001, 20001, 30001],
        "max_handling_capacity": 10
    }
    partner_response = await client.post("/partner/signup", json=partner_data)
    assert partner_response.status_code == 200
    
    # Create a seller
    seller_data = {
        "name": "Test Seller",
        "email": "testseller@example.com",
        "password": "testpassword123"
    }
    seller_response = await client.post("/seller/signup", json=seller_data)
    assert seller_response.status_code == 200
    
    # Phase 2: Verify email before login
    from app.database.models import Seller
    from sqlalchemy import select
    async with test_session() as session:
        seller = await session.scalar(
            select(Seller).where(Seller.email == seller_data["email"])
        )
        assert seller is not None
        seller.email_verified = True
        await session.commit()
    
    # Login to get token
    login_response = await client.post(
        "/seller/token",
        data={"username": seller_data["email"], "password": seller_data["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Create a shipment (Phase 2: client_contact_email is required)
    shipment_data = {
        "content": "Test Package",
        "weight": 5.0,
        "destination": 10001,
        "client_contact_email": "client@example.com"
    }
    shipment_response = await client.post(
        "/shipment/",
        json=shipment_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert shipment_response.status_code == 200
    shipment_id = shipment_response.json()["id"]
    
    # Test track endpoint
    track_response = await client.get(f"/shipment/track?id={shipment_id}")
    
    assert track_response.status_code == 200
    assert track_response.headers["content-type"].startswith("text/html")
    
    # Verify HTML content
    html_content = track_response.text
    assert "FastShip" in html_content
    assert "Order #" in html_content
    assert shipment_data["content"] in html_content
    assert "Order History" in html_content or "timeline" in html_content.lower()


@pytest.mark.asyncio
async def test_shipment_track_not_found(client: AsyncClient, test_session: AsyncSession):
    """Test track endpoint with non-existent shipment ID"""
    from uuid import uuid4
    
    fake_id = uuid4()
    response = await client.get(f"/shipment/track?id={fake_id}")
    
    assert response.status_code == 404
    # Check if response is JSON (error) or HTML (404 page)
    if response.headers.get("content-type", "").startswith("application/json"):
        error_data = response.json()
        # FastAPI exception handler may use "message" or "detail"
        error_text = error_data.get("message", error_data.get("detail", "")).lower()
        assert "not found" in error_text
    else:
        # HTML 404 page
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_shipment_track_with_timeline(client: AsyncClient, test_session: AsyncSession):
    """Test track endpoint displays timeline correctly"""
    # Create delivery partner first
    partner_data = {
        "name": "Timeline Partner",
        "email": "timelinepartner@example.com",
        "password": "testpass123",
        "serviceable_zip_codes": [20001],
        "max_handling_capacity": 10
    }
    await client.post("/partner/signup", json=partner_data)
    
    # Create seller
    seller_data = {
        "name": "Timeline Seller",
        "email": "timelineseller@example.com",
        "password": "testpass123"
    }
    seller_response = await client.post("/seller/signup", json=seller_data)
    assert seller_response.status_code == 200
    
    # Phase 2: Verify email before login
    from app.database.models import Seller
    from sqlalchemy import select
    async with test_session() as session:
        seller = await session.scalar(
            select(Seller).where(Seller.email == seller_data["email"])
        )
        assert seller is not None
        seller.email_verified = True
        await session.commit()
    
    # Login
    login_response = await client.post(
        "/seller/token",
        data={"username": seller_data["email"], "password": seller_data["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    # Create shipment (this should create an initial event) (Phase 2: client_contact_email is required)
    shipment_data = {
        "content": "Timeline Test Package",
        "weight": 3.0,
        "destination": 20001,
        "client_contact_email": "timelineclient@example.com"
    }
    shipment_response = await client.post(
        "/shipment/",
        json=shipment_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert shipment_response.status_code == 200
    shipment_id = shipment_response.json()["id"]
    
    # Get timeline endpoint
    timeline_response = await client.get(f"/shipment/timeline?id={shipment_id}")
    assert timeline_response.status_code == 200
    timeline = timeline_response.json()
    
    # Verify timeline has at least one event (placed event)
    assert len(timeline) >= 1
    assert timeline[0]["status"] == "placed"
    
    # Test track endpoint
    track_response = await client.get(f"/shipment/track?id={shipment_id}")
    assert track_response.status_code == 200
    
    html_content = track_response.text
    # Should contain status information
    assert "placed" in html_content.lower() or "status" in html_content.lower()


@pytest.mark.asyncio
async def test_shipment_track_template_variables(client: AsyncClient, test_session: AsyncSession):
    """Test that track endpoint provides all required template variables"""
    # Create delivery partner first
    partner_data = {
        "name": "Template Partner",
        "email": "templatepartner@example.com",
        "password": "testpass123",
        "serviceable_zip_codes": [30001],
        "max_handling_capacity": 10
    }
    await client.post("/partner/signup", json=partner_data)
    
    # Create seller and shipment
    seller_data = {
        "name": "Template Test Seller",
        "email": "templatetest@example.com",
        "password": "testpass123"
    }
    await client.post("/seller/signup", json=seller_data)
    
    # Phase 2: Verify email before login
    from app.database.models import Seller
    from sqlalchemy import select
    async with test_session() as session:
        seller = await session.scalar(
            select(Seller).where(Seller.email == seller_data["email"])
        )
        assert seller is not None
        seller.email_verified = True
        await session.commit()
    
    login_response = await client.post(
        "/seller/token",
        data={"username": seller_data["email"], "password": seller_data["password"]},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    
    shipment_data = {
        "content": "Template Test",
        "weight": 2.5,
        "destination": 30001,
        "client_contact_email": "templateclient@example.com"
    }
    shipment_response = await client.post(
        "/shipment/",
        json=shipment_data,
        headers={"Authorization": f"Bearer {token}"}
    )
    assert shipment_response.status_code == 200
    shipment_id = shipment_response.json()["id"]
    
    # Get track page
    track_response = await client.get(f"/shipment/track?id={shipment_id}")
    assert track_response.status_code == 200
    
    html = track_response.text
    
    # Verify all template variables are rendered
    assert shipment_data["content"] in html  # content
    assert "Order #" in html  # id.hex
    # Status should be present (even if just in CSS class)
    assert "status" in html.lower() or "placed" in html.lower()
    # Timeline/events should be present
    assert "timeline" in html.lower() or "event" in html.lower() or "history" in html.lower()

