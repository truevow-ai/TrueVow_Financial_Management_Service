"""Transfer Repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date
from app.shared.repositories.base_repository import BaseRepository
from app.modules.treasury.models.transfer_model import Transfer, TransferType


class TransferRepository(BaseRepository[Transfer]):
    """Repository for Transfer"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Transfer)
    
    async def get_by_external_id(self, external_id: str) -> Optional[Transfer]:
        """Get transfer by external ID"""
        result = await self.session.execute(
            select(Transfer).where(Transfer.external_id == external_id)
        )
        return result.scalar_one_or_none()
    
    async def list_by_entity(
        self,
        entity_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        transfer_type: Optional[TransferType] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transfer]:
        """List transfers for an entity"""
        query = select(Transfer).where(Transfer.legal_entity_id == entity_id)
        
        if start_date:
            query = query.where(Transfer.transfer_date >= start_date)
        if end_date:
            query = query.where(Transfer.transfer_date <= end_date)
        if transfer_type:
            query = query.where(Transfer.transfer_type == transfer_type)
        
        query = query.order_by(Transfer.transfer_date.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def list_intercompany(
        self,
        from_entity_id: UUID,
        to_entity_id: Optional[UUID] = None,
        limit: int = 100
    ) -> List[Transfer]:
        """List intercompany transfers"""
        query = select(Transfer).where(
            Transfer.legal_entity_id == from_entity_id,
            Transfer.transfer_type == TransferType.INTERCOMPANY
        )
        if to_entity_id:
            query = query.where(Transfer.to_entity_id == to_entity_id)
        
        query = query.order_by(Transfer.transfer_date.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
