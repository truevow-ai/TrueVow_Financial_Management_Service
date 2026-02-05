"""External Sync Repository"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from app.shared.repositories.base_repository import BaseRepository
from app.modules.general_ledger.models.external_sync_model import ExternalSyncCursor, SourceObjectMap


class ExternalSyncCursorRepository(BaseRepository[ExternalSyncCursor]):
    """Repository for ExternalSyncCursor"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ExternalSyncCursor)
    
    async def get_cursor(
        self,
        entity_id: UUID,
        source_service: str,
        object_type: str
    ) -> Optional[ExternalSyncCursor]:
        """Get sync cursor"""
        result = await self.session.execute(
            select(ExternalSyncCursor).where(
                ExternalSyncCursor.legal_entity_id == entity_id,
                ExternalSyncCursor.source_service == source_service,
                ExternalSyncCursor.object_type == object_type
            )
        )
        return result.scalar_one_or_none()
    
    async def update_cursor(
        self,
        entity_id: UUID,
        source_service: str,
        object_type: str,
        cursor_value: str
    ) -> ExternalSyncCursor:
        """Update or create sync cursor"""
        cursor = await self.get_cursor(entity_id, source_service, object_type)
        
        if cursor:
            await self.update(
                cursor.id,
                cursor_value=cursor_value,
                last_sync_at=datetime.now()
            )
            await self.session.commit()
            return await self.get_by_id(cursor.id)
        else:
            cursor = await self.create(
                legal_entity_id=entity_id,
                source_service=source_service,
                object_type=object_type,
                cursor_value=cursor_value,
                last_sync_at=datetime.now()
            )
            await self.session.commit()
            return cursor


class SourceObjectMapRepository(BaseRepository[SourceObjectMap]):
    """Repository for SourceObjectMap"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, SourceObjectMap)
    
    async def get_mapping(
        self,
        entity_id: UUID,
        source_service: str,
        object_type: str,
        external_id: str
    ) -> Optional[SourceObjectMap]:
        """Get mapping by external ID"""
        result = await self.session.execute(
            select(SourceObjectMap).where(
                SourceObjectMap.legal_entity_id == entity_id,
                SourceObjectMap.source_service == source_service,
                SourceObjectMap.object_type == object_type,
                SourceObjectMap.external_id == external_id
            )
        )
        return result.scalar_one_or_none()
    
    async def create_mapping(
        self,
        entity_id: UUID,
        source_service: str,
        object_type: str,
        external_id: str,
        internal_id: UUID,
        book_id: Optional[UUID] = None
    ) -> SourceObjectMap:
        """Create or get existing mapping"""
        existing = await self.get_mapping(entity_id, source_service, object_type, external_id)
        if existing:
            return existing
        
        mapping = await self.create(
            legal_entity_id=entity_id,
            source_service=source_service,
            object_type=object_type,
            external_id=external_id,
            internal_id=internal_id,
            book_id=book_id
        )
        await self.session.commit()
        return mapping
