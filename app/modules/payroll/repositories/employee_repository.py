"""Employee Repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.shared.repositories.base_repository import BaseRepository
from app.modules.payroll.models.employee_model import HREmployee, EmployeeType


class HREmployeeRepository(BaseRepository[HREmployee]):
    """Repository for HREmployee"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, HREmployee)
    
    async def get_by_code(self, employee_code: str) -> Optional[HREmployee]:
        """Get employee by code"""
        result = await self.session.execute(
            select(HREmployee).where(HREmployee.employee_code == employee_code)
        )
        return result.scalar_one_or_none()
    
    async def list_by_entity(
        self,
        entity_id: UUID,
        active_only: bool = True,
        employee_type: Optional[EmployeeType] = None
    ) -> List[HREmployee]:
        """List employees for an entity"""
        query = select(HREmployee).where(HREmployee.legal_entity_id == entity_id)
        if active_only:
            query = query.where(HREmployee.is_active == True)
        if employee_type:
            query = query.where(HREmployee.employee_type == employee_type)
        query = query.order_by(HREmployee.employee_code)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def list_by_pay_group(
        self,
        pay_group_id: UUID,
        active_only: bool = True
    ) -> List[HREmployee]:
        """List employees in a pay group"""
        query = select(HREmployee).where(HREmployee.pay_group_id == pay_group_id)
        if active_only:
            query = query.where(HREmployee.is_active == True)
        query = query.order_by(HREmployee.employee_code)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
