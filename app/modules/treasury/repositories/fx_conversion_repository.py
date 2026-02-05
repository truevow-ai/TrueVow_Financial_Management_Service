"""FX Conversion Repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date
from app.shared.repositories.base_repository import BaseRepository
from app.modules.treasury.models.fx_conversion_model import FXConversion


class FXConversionRepository(BaseRepository[FXConversion]):
    """Repository for FXConversion"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, FXConversion)
    
    async def get_by_external_id(self, external_id: str) -> Optional[FXConversion]:
        """Get conversion by external ID"""
        result = await self.session.execute(
            select(FXConversion).where(FXConversion.external_id == external_id)
        )
        return result.scalar_one_or_none()
    
    async def list_by_entity(
        self,
        entity_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[FXConversion]:
        """List FX conversions for an entity"""
        query = select(FXConversion).where(FXConversion.legal_entity_id == entity_id)
        
        if start_date:
            query = query.where(FXConversion.conversion_date >= start_date)
        if end_date:
            query = query.where(FXConversion.conversion_date <= end_date)
        
        query = query.order_by(FXConversion.conversion_date.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
