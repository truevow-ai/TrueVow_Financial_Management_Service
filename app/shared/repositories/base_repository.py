"""Base repository class"""
from typing import Generic, TypeVar, Type, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from uuid import UUID
from app.shared.models.base_model import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations and soft-delete support."""
    
    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model
    
    async def get_by_id(self, id: UUID, include_deleted: bool = False) -> Optional[T]:
        """Get entity by ID.
        
        Args:
            id: Entity ID
            include_deleted: If True, include soft-deleted records
        """
        query = select(self.model).where(self.model.id == id)
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.where(self.model.deleted_at.is_(None))
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def create(self, **kwargs) -> T:
        """Create new entity"""
        entity = self.model(**kwargs)
        self.session.add(entity)
        await self.session.flush()
        return entity
    
    async def update(self, id: UUID, **kwargs) -> Optional[T]:
        """Update entity"""
        await self.session.execute(
            update(self.model)
            .where(self.model.id == id)
            .values(**kwargs)
        )
        return await self.get_by_id(id)
    
    async def delete(self, id: UUID, hard: bool = False, deleted_by: UUID = None) -> bool:
        """Delete entity.
        
        Args:
            id: Entity ID
            hard: If True, permanently delete. If False, soft-delete.
            deleted_by: User ID performing the deletion (for soft-delete audit)
        
        Returns:
            True if deleted, False if not found
        """
        if hard:
            result = await self.session.execute(
                delete(self.model).where(self.model.id == id)
            )
            return result.rowcount > 0
        else:
            # Soft delete
            if not hasattr(self.model, 'soft_delete'):
                raise ValueError(f"Model {self.model.__name__} does not support soft_delete")
            
            entity = await self.get_by_id(id, include_deleted=True)
            if entity is None:
                return False
            
            entity.soft_delete(deleted_by_user_id=deleted_by)
            await self.session.flush()
            return True
    
    async def restore(self, id: UUID) -> Optional[T]:
        """Restore a soft-deleted entity.
        
        Args:
            id: Entity ID
            
        Returns:
            The restored entity, or None if not found
        """
        entity = await self.get_by_id(id, include_deleted=True)
        if entity is None:
            return None
        
        if hasattr(entity, 'restore'):
            entity.restore()
            await self.session.flush()
        
        return entity
    
    async def list_all(self, limit: int = 100, offset: int = 0, include_deleted: bool = False) -> List[T]:
        """List all entities with pagination.
        
        Args:
            limit: Maximum results
            offset: Offset for pagination
            include_deleted: If True, include soft-deleted records
        """
        query = select(self.model)
        if not include_deleted and hasattr(self.model, 'deleted_at'):
            query = query.where(self.model.deleted_at.is_(None))
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def list_deleted(self, limit: int = 100, offset: int = 0) -> List[T]:
        """List soft-deleted entities only.
        
        Args:
            limit: Maximum results
            offset: Offset for pagination
        """
        if not hasattr(self.model, 'deleted_at'):
            return []
        
        query = select(self.model).where(self.model.deleted_at.isnot(None))
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())
