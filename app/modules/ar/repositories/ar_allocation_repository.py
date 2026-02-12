"""AR Allocation Repository"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.shared.repositories.base_repository import BaseRepository
from app.modules.ar.models.ar_payment_model import ARAllocation


class ARAllocationRepository(BaseRepository[ARAllocation]):
    """Repository for ARAllocation"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ARAllocation)
    
    async def list_by_payment(self, payment_id: UUID) -> List[ARAllocation]:
        """List allocations for a payment"""
        result = await self.session.execute(
            select(ARAllocation)
            .where(ARAllocation.ar_payment_id == payment_id)
        )
        return list(result.scalars().all())
    
    async def list_by_invoice(self, invoice_id: UUID) -> List[ARAllocation]:
        """List allocations for an invoice"""
        result = await self.session.execute(
            select(ARAllocation)
            .where(ARAllocation.ar_invoice_id == invoice_id)
        )
        return list(result.scalars().all())
