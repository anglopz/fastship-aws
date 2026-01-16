from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlmodel import SQLModel

from app.config import settings


# Create a database engine to connect with database
engine = create_async_engine(
    url=settings.POSTGRES_URL,
    echo=True,
)


async def create_db_tables():
    """Create all database tables from SQLModel metadata"""
    async with engine.begin() as connection:
        # Import all models to ensure they're registered with SQLModel
        from .models import (
            Seller,
            DeliveryPartner,
            Shipment,
            ShipmentEvent,
            Location,
            ServicableLocation,
            Review,
            Tag,
        )
        await connection.run_sync(SQLModel.metadata.create_all)


async def get_session():
    async_session = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async with async_session() as session:
        yield session
