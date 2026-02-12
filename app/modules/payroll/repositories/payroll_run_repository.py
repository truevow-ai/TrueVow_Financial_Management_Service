"""Payroll Run Repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date
from app.shared.repositories.base_repository import BaseRepository
from app.modules.payroll.models.payroll_run_model import (
    PayrollRun,
    PayrollRunItem,
    PayrollRunComponentLine,
    PayrollRunStatus
)


class PayrollRunRepository(BaseRepository[PayrollRun]):
    """Repository for PayrollRun"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, PayrollRun)
    
    async def get_by_run_number(self, run_number: str) -> Optional[PayrollRun]:
        """Get payroll run by run number"""
        result = await self.session.execute(
            select(PayrollRun).where(PayrollRun.run_number == run_number)
        )
        return result.scalar_one_or_none()
    
    async def list_by_pay_group(
        self,
        pay_group_id: UUID,
        status: Optional[PayrollRunStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PayrollRun]:
        """List payroll runs for a pay group"""
        query = select(PayrollRun).where(PayrollRun.pay_group_id == pay_group_id)
        if status:
            query = query.where(PayrollRun.status == status)
        query = query.order_by(PayrollRun.pay_period_end.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def list_by_entity(
        self,
        entity_id: UUID,
        status: Optional[PayrollRunStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PayrollRun]:
        """List payroll runs for an entity"""
        query = select(PayrollRun).where(PayrollRun.legal_entity_id == entity_id)
        if status:
            query = query.where(PayrollRun.status == status)
        query = query.order_by(PayrollRun.pay_period_end.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())


class PayrollRunItemRepository(BaseRepository[PayrollRunItem]):
    """Repository for PayrollRunItem"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, PayrollRunItem)
    
    async def list_by_run(self, run_id: UUID) -> List[PayrollRunItem]:
        """List items for a payroll run"""
        result = await self.session.execute(
            select(PayrollRunItem)
            .where(PayrollRunItem.payroll_run_id == run_id)
            .order_by(PayrollRunItem.hr_employee_id)
        )
        return list(result.scalars().all())
    
    async def get_by_run_and_employee(
        self,
        run_id: UUID,
        employee_id: UUID
    ) -> Optional[PayrollRunItem]:
        """Get run item for employee"""
        result = await self.session.execute(
            select(PayrollRunItem).where(
                PayrollRunItem.payroll_run_id == run_id,
                PayrollRunItem.hr_employee_id == employee_id
            )
        )
        return result.scalar_one_or_none()


class PayrollRunComponentLineRepository(BaseRepository[PayrollRunComponentLine]):
    """Repository for PayrollRunComponentLine"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, PayrollRunComponentLine)
    
    async def list_by_run_item(self, run_item_id: UUID) -> List[PayrollRunComponentLine]:
        """List component lines for a run item"""
        result = await self.session.execute(
            select(PayrollRunComponentLine)
            .where(PayrollRunComponentLine.payroll_run_item_id == run_item_id)
        )
        return list(result.scalars().all())
