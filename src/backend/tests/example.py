"""
Test data constants and helper functions
Section 30: API Testing Integration
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.database.models import DeliveryPartner, Location, Seller
from app.services.user import password_context

# Test data constants
SELLER = {
    "name": "RainForest",
    "email": "rainforest@xmailg.one",
    "password": "lovetrees",
}

DELIVERY_PARTNER = {
    "name": "PHL",
    "email": "phl@xmailg.one",
    "password": "tough",
    "servicable_locations": [11001, 11002, 11003, 11004, 11005],  # Updated to servicable_locations
    "max_handling_capacity": 2,
}

SHIPMENT = {
    "content": "Bananas",
    "weight": 1.25,
    "destination": 11004,
    "client_contact_email": "py@xmailg.one",
}


async def create_test_data(session: AsyncSession):
    """
    Create test data in the database.
    
    Section 30: API Testing - Centralized test data creation
    
    Creates:
    - A verified seller with hashed password
    - A verified delivery partner with serviceable locations
    - Links locations via many-to-many relationship
    """
    # Create seller
    seller = Seller(
        name=SELLER["name"],
        email=SELLER["email"],
        email_verified=True,  # Pre-verified for testing
        password_hash=password_context.hash(SELLER["password"]),
    )
    session.add(seller)
    
    # Create delivery partner with serviceable locations
    # Phase 3: Use servicable_locations relationship (not serviceable_zip_codes)
    locations = []
    for zip_code in DELIVERY_PARTNER["servicable_locations"]:
        # Check if location already exists
        existing_location = await session.scalar(
            select(Location).where(Location.zip_code == zip_code)
        )
        if not existing_location:
            location = Location(zip_code=zip_code)
            session.add(location)
            locations.append(location)
        else:
            locations.append(existing_location)
    
    partner = DeliveryPartner(
        name=DELIVERY_PARTNER["name"],
        email=DELIVERY_PARTNER["email"],
        email_verified=True,  # Pre-verified for testing
        password_hash=password_context.hash(DELIVERY_PARTNER["password"]),
        max_handling_capacity=DELIVERY_PARTNER["max_handling_capacity"],
        servicable_locations=locations,  # Link via relationship
    )
    session.add(partner)
    
    await session.commit()

