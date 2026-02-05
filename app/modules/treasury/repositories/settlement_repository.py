"""Settlement Repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date
from app.shared.repositories.base_repository import BaseRepository
from app.modules.treasury.models.settlement_model import Settlement, SettlementSource


class SettlementRepository(BaseRepository[Settlement]):
    """Repository for Settlement"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Settlement)
    
    async def get_by_external_id(self, external_settlement_id: str) -> Optional[Settlement]:
        """Get settlement by external ID (for dedupe)"""
        result = await self.session.execute(
            select(Settlement).where(Settlement.external_settlement_id == external_settlement_id)
        )
        return result.scalar_one_or_none()
    
    async def list_by_entity(
        self,
        entity_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        source: Optional[SettlementSource] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Settlement]:
        """List settlements for an entity"""
        query = select(Settlement).where(Settlement.legal_entity_id == entity_id)
        
        if start_date:
            query = query.where(Settlement.settlement_date >= start_date)
        if end_date:
            query = query.where(Settlement.settlement_date <= end_date)
        if source:
            query = query.where(Settlement.source == source)
        
        query = query.order_by(Settlement.settlement_date.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
