"""Sync Cursor Repository"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from app.shared.repositories.base_repository import BaseRepository
from app.modules.treasury.models.sync_cursor_model import SyncCursor


class SyncCursorRepository(BaseRepository[SyncCursor]):
    """Repository for SyncCursor"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, SyncCursor)
    
    async def get_cursor(
        self,
        entity_id: UUID,
        source_system: str,
        object_type: str
    ) -> Optional[SyncCursor]:
        """Get sync cursor"""
        result = await self.session.execute(
            select(SyncCursor).where(
                SyncCursor.legal_entity_id == entity_id,
                SyncCursor.source_system == source_system,
                SyncCursor.object_type == object_type
            )
        )
        return result.scalar_one_or_none()
    
    async def update_cursor(
        self,
        entity_id: UUID,
        source_system: str,
        object_type: str,
        cursor_value: str
    ) -> SyncCursor:
        """Update or create sync cursor"""
        cursor = await self.get_cursor(entity_id, source_system, object_type)
        
        if cursor:
            await self.update(cursor.id, cursor_value=cursor_value, last_sync_at=datetime.now())
            await self.session.commit()
            return await self.get_by_id(cursor.id)
        else:
            cursor = await self.create(
                legal_entity_id=entity_id,
                source_system=source_system,
                object_type=object_type,
                cursor_value=cursor_value,
                last_sync_at=datetime.now()
            )
            await self.session.commit()
            return cursor
