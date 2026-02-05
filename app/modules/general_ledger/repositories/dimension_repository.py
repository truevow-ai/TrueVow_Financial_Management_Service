"""Dimension Repository"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.shared.repositories.base_repository import BaseRepository
from app.modules.general_ledger.models.dimension_model import Dimension, DimensionValue


class DimensionRepository(BaseRepository[Dimension]):
    """Repository for Dimension"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Dimension)
    
    async def get_by_code(self, code: str) -> Optional[Dimension]:
        """Get dimension by code"""
        result = await self.session.execute(
            select(Dimension).where(Dimension.code == code)
        )
        return result.scalar_one_or_none()


class DimensionValueRepository(BaseRepository[DimensionValue]):
    """Repository for DimensionValue"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, DimensionValue)
    
    async def get_by_dimension_and_value(
        self, 
        dimension_code: str, 
        value_code: str
    ) -> Optional[DimensionValue]:
        """Get dimension value by dimension and value codes"""
        result = await self.session.execute(
            select(DimensionValue).where(
                DimensionValue.dimension_code == dimension_code,
                DimensionValue.value_code == value_code
            )
        )
        return result.scalar_one_or_none()
    
    async def list_by_dimension(self, dimension_code: str) -> List[DimensionValue]:
        """List all values for a dimension"""
        result = await self.session.execute(
            select(DimensionValue).where(
                DimensionValue.dimension_code == dimension_code
            )
        )
        return list(result.scalars().all())
