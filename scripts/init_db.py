#!/usr/bin/env python3
"""
Database initialization script
Creates all database tables from SQLModel metadata

Usage:
    python scripts/init_db.py
    or
    docker-compose exec api python scripts/init_db.py
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import SQLModel

from app.config import settings
from app.database.models import (
    Seller,
    DeliveryPartner,
    Shipment,
    ShipmentEvent,
    Location,
    ServicableLocation,
    Review,
    Tag,
)


async def init_database():
    """Initialize database by creating all tables"""
    print("🔄 Initializing database...")
    
    engine = create_async_engine(
        url=settings.POSTGRES_URL,
        echo=False,
    )
    
    try:
        async with engine.begin() as connection:
            print("📦 Creating tables from SQLModel metadata...")
            await connection.run_sync(SQLModel.metadata.create_all)
            print("✅ Database tables created successfully!")
            
            # List created tables
            from sqlalchemy import inspect
            inspector = inspect(connection.sync_engine)
            tables = inspector.get_table_names()
            print(f"\n📊 Created {len(tables)} tables:")
            for table in sorted(tables):
                print(f"   - {table}")
                
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(init_database())

