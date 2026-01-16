"""
Pytest configuration and fixtures for FastAPI tests
Section 30: API Testing Integration
"""
import os
import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

# Set TESTING environment variable before imports
os.environ["TESTING"] = "true"

from app.main import app
from app.database.session import get_session
from app.database.redis import close_redis

# Import all models to ensure they're registered with SQLModel
from app.database.models import Seller, Shipment, DeliveryPartner  # noqa: F401

# Section 30: Import test data constants
# Use relative import since tests is not a package
try:
    from . import example
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    tests_dir = Path(__file__).parent
    sys.path.insert(0, str(tests_dir))
    import example

# Test database URL - Use PostgreSQL for UUID and ARRAY support
# In Docker, use 'db' as host; locally use 'localhost'
# Fallback to environment variable or use test database
TEST_DB_HOST = os.getenv("TEST_DB_HOST", "db" if os.path.exists("/.dockerenv") else "localhost")
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    f"postgresql+asyncpg://postgres:password@{TEST_DB_HOST}:5432/fastapi_db"
)


@pytest.fixture(scope="function")
async def test_engine():
    """Create a test engine for each test"""
    engine = create_async_engine(
        url=TEST_DATABASE_URL,
        echo=False,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def test_db(test_engine):
    """Create test database tables for each test"""
    # Create tables
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield
    
    # Drop tables after test
    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(scope="function")
async def test_session(test_db, test_engine):
    """Create a test database session and override dependency"""
    # Create a new session maker for each test
    async_session_maker = async_sessionmaker(
        bind=test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def override_get_session():
        async with async_session_maker() as session:
            yield session

    # Override the dependency
    app.dependency_overrides[get_session] = override_get_session

    yield async_session_maker

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
async def client(test_session):
    """
    Create a test client.
    
    Section 30: Updated to use ASGITransport for better FastAPI app testing.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as test_client:
        yield test_client
    # Clean up Redis connections after each test
    await close_redis()


# Section 30: Authentication fixtures for easier testing
@pytest.fixture(scope="function")
async def seller_token(client: AsyncClient, test_session):
    """
    Get authentication token for test seller.
    
    Section 30: API Testing - Authentication helper fixture
    
    Creates a seller, verifies email, and returns JWT token.
    """
    from app.database.models import Seller
    from sqlalchemy import select
    
    # Create seller if it doesn't exist
    async with test_session() as session:
        seller = await session.scalar(
            select(Seller).where(Seller.email == example.SELLER["email"])
        )
        
        if not seller:
            # Create seller
            from app.services.user import password_context
            seller = Seller(
                name=example.SELLER["name"],
                email=example.SELLER["email"],
                email_verified=True,  # Pre-verified for testing
                password_hash=password_context.hash(example.SELLER["password"]),
            )
            session.add(seller)
            await session.commit()
        elif not seller.email_verified:
            # Verify email if not already verified
            seller.email_verified = True
            await session.commit()
    
    # Login to get token
    response = await client.post(
        "/seller/token",
        data={
            "username": example.SELLER["email"],
            "password": example.SELLER["password"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 200, f"Login failed: {response.json()}"
    data = response.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.fixture(scope="function")
async def partner_token(client: AsyncClient, test_session):
    """
    Get authentication token for test delivery partner.
    
    Section 30: API Testing - Authentication helper fixture
    
    Creates a delivery partner, verifies email, and returns JWT token.
    """
    from app.database.models import DeliveryPartner, Location
    from sqlalchemy import select
    
    # Create delivery partner if it doesn't exist
    async with test_session() as session:
        partner = await session.scalar(
            select(DeliveryPartner).where(DeliveryPartner.email == example.DELIVERY_PARTNER["email"])
        )
        
        if not partner:
            # Create locations and partner
            from app.services.user import password_context
            
            locations = []
            for zip_code in example.DELIVERY_PARTNER["servicable_locations"]:
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
                name=example.DELIVERY_PARTNER["name"],
                email=example.DELIVERY_PARTNER["email"],
                email_verified=True,  # Pre-verified for testing
                password_hash=password_context.hash(example.DELIVERY_PARTNER["password"]),
                max_handling_capacity=example.DELIVERY_PARTNER["max_handling_capacity"],
                servicable_locations=locations,
            )
            session.add(partner)
            await session.commit()
        elif not partner.email_verified:
            # Verify email if not already verified
            partner.email_verified = True
            await session.commit()
    
    # Login to get token
    response = await client.post(
        "/partner/token",
        data={
            "username": example.DELIVERY_PARTNER["email"],
            "password": example.DELIVERY_PARTNER["password"],
        },
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    
    assert response.status_code == 200, f"Login failed: {response.json()}"
    data = response.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.fixture(scope="function")
async def client_with_seller_auth(client: AsyncClient, seller_token: str):
    """
    Create a test client with seller authentication pre-configured.
    
    Section 30: API Testing - Pre-authenticated client fixture
    
    Returns client with Authorization header set for seller.
    """
    client.headers["Authorization"] = f"Bearer {seller_token}"
    yield client
    # Clean up header after test
    if "Authorization" in client.headers:
        del client.headers["Authorization"]


@pytest.fixture(scope="function")
async def client_with_partner_auth(client: AsyncClient, partner_token: str):
    """
    Create a test client with delivery partner authentication pre-configured.
    
    Section 30: API Testing - Pre-authenticated client fixture
    
    Returns client with Authorization header set for delivery partner.
    """
    client.headers["Authorization"] = f"Bearer {partner_token}"
    yield client
    # Clean up header after test
    if "Authorization" in client.headers:
        del client.headers["Authorization"]


# Section 30: Optional session-scoped fixtures for faster test execution
# These are optional and can be used alongside function-scoped fixtures
@pytest.fixture(scope="session")
async def session_test_engine():
    """
    Create a session-scoped test engine (optional, for faster tests).
    
    Section 30: API Testing - Session-scoped fixture for performance
    
    Note: Use with caution as it shares state across tests.
    Prefer function-scoped fixtures for better test isolation.
    """
    engine = create_async_engine(
        url=TEST_DATABASE_URL,
        echo=False,
    )
    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def session_test_db(session_test_engine):
    """
    Create session-scoped test database tables (optional).
    
    Section 30: API Testing - Session-scoped database setup
    
    Creates tables once per test session for faster execution.
    """
    # Create tables
    async with session_test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    
    yield
    
    # Drop tables after all tests
    async with session_test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture(scope="session")
async def session_setup_and_teardown(session_test_db, session_test_engine):
    """
    Session-scoped setup and teardown (optional, not autouse).
    
    Section 30: API Testing - Centralized test data creation
    
    Creates test data once per session using example.py module.
    
    **Usage:** Add this fixture to tests that want to use session-scoped database.
    By default, function-scoped fixtures are used for better isolation.
    """
    async_session_maker = async_sessionmaker(
        bind=session_test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async def override_get_session():
        async with async_session_maker() as session:
            yield session
    
    # Override the dependency
    app.dependency_overrides[get_session] = override_get_session
    
    # Create test data using example.py
    async with async_session_maker() as session:
        await example.create_test_data(session)
    
    yield
    
    # Clean up
    app.dependency_overrides.clear()
    await close_redis()
