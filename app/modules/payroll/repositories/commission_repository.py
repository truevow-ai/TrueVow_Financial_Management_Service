"""Commission Repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date
from app.shared.repositories.base_repository import BaseRepository
from app.modules.payroll.models.commission_model import (
    CommissionPlan,
    CommissionRule,
    CommissionLedger
)


class CommissionPlanRepository(BaseRepository[CommissionPlan]):
    """Repository for CommissionPlan"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, CommissionPlan)
    
    async def get_by_code(self, plan_code: str) -> Optional[CommissionPlan]:
        """Get commission plan by code"""
        result = await self.session.execute(
            select(CommissionPlan).where(CommissionPlan.plan_code == plan_code)
        )
        return result.scalar_one_or_none()
    
    async def list_by_entity(
        self,
        entity_id: UUID,
        active_only: bool = True
    ) -> List[CommissionPlan]:
        """List commission plans for an entity"""
        query = select(CommissionPlan).where(CommissionPlan.legal_entity_id == entity_id)
        if active_only:
            query = query.where(CommissionPlan.is_active == True)
        query = query.order_by(CommissionPlan.plan_code)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())


class CommissionLedgerRepository(BaseRepository[CommissionLedger]):
    """Repository for CommissionLedger"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, CommissionLedger)
    
    async def list_unpaid_by_employee(
        self,
        employee_id: UUID,
        limit: int = 100
    ) -> List[CommissionLedger]:
        """List unpaid commission entries for an employee"""
        result = await self.session.execute(
            select(CommissionLedger)
            .where(
                CommissionLedger.hr_employee_id == employee_id,
                CommissionLedger.is_paid == False
            )
            .order_by(CommissionLedger.period_start.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
    
    async def list_unpaid_by_period(
        self,
        entity_id: UUID,
        period_start: date,
        period_end: date
    ) -> List[CommissionLedger]:
        """List unpaid commissions for a period"""
        result = await self.session.execute(
            select(CommissionLedger).where(
                CommissionLedger.legal_entity_id == entity_id,
                CommissionLedger.period_start >= period_start,
                CommissionLedger.period_end <= period_end,
                CommissionLedger.is_paid == False
            )
        )
        return list(result.scalars().all())
