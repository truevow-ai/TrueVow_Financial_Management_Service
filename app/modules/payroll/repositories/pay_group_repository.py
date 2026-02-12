"""Pay Group Repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.shared.repositories.base_repository import BaseRepository
from app.modules.payroll.models.pay_group_model import PayGroup


class PayGroupRepository(BaseRepository[PayGroup]):
    """Repository for PayGroup"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, PayGroup)
    
    async def get_by_code(self, group_code: str) -> Optional[PayGroup]:
        """Get pay group by code"""
        result = await self.session.execute(
            select(PayGroup).where(PayGroup.group_code == group_code)
        )
        return result.scalar_one_or_none()
    
    async def list_by_entity(
        self,
        entity_id: UUID,
        active_only: bool = True
    ) -> List[PayGroup]:
        """List pay groups for an entity"""
        query = select(PayGroup).where(PayGroup.legal_entity_id == entity_id)
        if active_only:
            query = query.where(PayGroup.is_active == True)
        query = query.order_by(PayGroup.group_code)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
