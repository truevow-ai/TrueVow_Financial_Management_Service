"""Bonus Repository"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.shared.repositories.base_repository import BaseRepository
from app.modules.payroll.models.bonus_model import BonusPlan, BonusResult


class BonusPlanRepository(BaseRepository[BonusPlan]):
    """Repository for BonusPlan"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, BonusPlan)
    
    async def get_by_code(self, plan_code: str) -> BonusPlan:
        """Get bonus plan by code"""
        result = await self.session.execute(
            select(BonusPlan).where(BonusPlan.plan_code == plan_code)
        )
        return result.scalar_one_or_none()


class BonusResultRepository(BaseRepository[BonusResult]):
    """Repository for BonusResult"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, BonusResult)
    
    async def list_unpaid_by_employee(
        self,
        employee_id: UUID,
        limit: int = 100
    ) -> List[BonusResult]:
        """List unpaid bonuses for an employee"""
        result = await self.session.execute(
            select(BonusResult)
            .where(
                BonusResult.hr_employee_id == employee_id,
                BonusResult.is_paid == False
            )
            .order_by(BonusResult.bonus_date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
