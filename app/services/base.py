"""
Base service class providing common CRUD operations
"""
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import SQLModel


class BaseService:
    """Base service class with common database operations"""
    
    def __init__(self, model: SQLModel, session: AsyncSession):
        self.model = model
        self.session = session

    async def _get(self, id: UUID):
        """Get an entity by ID"""
        return await self.session.get(self.model, id)
    
    async def _add(self, entity: SQLModel):
        """Add a new entity to the database"""
        self.session.add(entity)
        await self.session.commit()
        await self.session.refresh(entity)
        return entity
    
    async def _update(self, entity: SQLModel):
        """Update an existing entity"""
        return await self._add(entity)
    
    async def _delete(self, entity: SQLModel):
        """Delete an entity from the database"""
        await self.session.delete(entity)
        await self.session.commit()

