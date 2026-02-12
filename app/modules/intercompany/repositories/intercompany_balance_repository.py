"""Intercompany Balance Repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date
from app.shared.repositories.base_repository import BaseRepository
from app.modules.intercompany.models.intercompany_balance_model import (
    IntercompanyBalance,
    BalanceType
)


class IntercompanyBalanceRepository(BaseRepository[IntercompanyBalance]):
    """Repository for IntercompanyBalance"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, IntercompanyBalance)
    
    async def get_balance(
        self,
        from_entity_id: UUID,
        to_entity_id: UUID,
        as_of_date: date,
        balance_type: BalanceType = BalanceType.NET
    ) -> Optional[IntercompanyBalance]:
        """Get balance snapshot"""
        result = await self.session.execute(
            select(IntercompanyBalance).where(
                IntercompanyBalance.from_entity_id == from_entity_id,
                IntercompanyBalance.to_entity_id == to_entity_id,
                IntercompanyBalance.as_of_date == as_of_date,
                IntercompanyBalance.balance_type == balance_type
            )
        )
        return result.scalar_one_or_none()
    
    async def list_by_entity(
        self,
        entity_id: UUID,
        as_of_date: Optional[date] = None,
        limit: int = 100
    ) -> List[IntercompanyBalance]:
        """List balances for an entity"""
        query = select(IntercompanyBalance).where(
            (IntercompanyBalance.from_entity_id == entity_id) |
            (IntercompanyBalance.to_entity_id == entity_id)
        )
        if as_of_date:
            query = query.where(IntercompanyBalance.as_of_date == as_of_date)
        query = query.order_by(IntercompanyBalance.as_of_date.desc()).limit(limit)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
