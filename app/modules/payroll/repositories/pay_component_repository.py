"""Pay Component Repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date
from app.shared.repositories.base_repository import BaseRepository
from app.modules.payroll.models.pay_component_model import (
    PayComponentDefinition,
    PayComponentAssignment,
    ComponentType
)


class PayComponentDefinitionRepository(BaseRepository[PayComponentDefinition]):
    """Repository for PayComponentDefinition"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, PayComponentDefinition)
    
    async def get_by_code(
        self,
        entity_id: UUID,
        component_code: str
    ) -> Optional[PayComponentDefinition]:
        """Get component by code"""
        result = await self.session.execute(
            select(PayComponentDefinition).where(
                PayComponentDefinition.legal_entity_id == entity_id,
                PayComponentDefinition.component_code == component_code
            )
        )
        return result.scalar_one_or_none()
    
    async def list_by_entity(
        self,
        entity_id: UUID,
        component_type: Optional[ComponentType] = None,
        active_only: bool = True
    ) -> List[PayComponentDefinition]:
        """List components for an entity"""
        query = select(PayComponentDefinition).where(
            PayComponentDefinition.legal_entity_id == entity_id
        )
        if component_type:
            query = query.where(PayComponentDefinition.component_type == component_type)
        if active_only:
            query = query.where(PayComponentDefinition.is_active == True)
        query = query.order_by(PayComponentDefinition.component_code)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())


class PayComponentAssignmentRepository(BaseRepository[PayComponentAssignment]):
    """Repository for PayComponentAssignment"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, PayComponentAssignment)
    
    async def list_by_employee(
        self,
        employee_id: UUID,
        effective_date: Optional[date] = None,
        active_only: bool = True
    ) -> List[PayComponentAssignment]:
        """List component assignments for an employee"""
        query = select(PayComponentAssignment).where(
            PayComponentAssignment.hr_employee_id == employee_id
        )
        if active_only:
            query = query.where(PayComponentAssignment.is_active == True)
        if effective_date:
            query = query.where(
                (PayComponentAssignment.effective_from <= effective_date) |
                (PayComponentAssignment.effective_from.is_(None))
            )
            query = query.where(
                (PayComponentAssignment.effective_to >= effective_date) |
                (PayComponentAssignment.effective_to.is_(None))
            )
        query = query.order_by(PayComponentAssignment.pay_component_id)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
