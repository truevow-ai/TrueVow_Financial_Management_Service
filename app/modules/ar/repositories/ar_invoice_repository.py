"""AR Invoice Repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date
from app.shared.repositories.base_repository import BaseRepository
from app.modules.ar.models.ar_invoice_model import ARInvoice, InvoiceStatus


class ARInvoiceRepository(BaseRepository[ARInvoice]):
    """Repository for ARInvoice"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ARInvoice)
    
    async def get_by_external_id(self, external_invoice_id: str) -> Optional[ARInvoice]:
        """Get invoice by external ID (Billing invoice ID)"""
        result = await self.session.execute(
            select(ARInvoice).where(ARInvoice.external_invoice_id == external_invoice_id)
        )
        return result.scalar_one_or_none()
    
    async def list_by_customer(
        self,
        customer_id: UUID,
        status: Optional[InvoiceStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ARInvoice]:
        """List invoices for a customer"""
        query = select(ARInvoice).where(ARInvoice.ar_customer_id == customer_id)
        if status:
            query = query.where(ARInvoice.status == status)
        query = query.order_by(ARInvoice.invoice_date.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def list_overdue(
        self,
        entity_id: UUID,
        as_of_date: date,
        limit: int = 1000
    ) -> List[ARInvoice]:
        """List overdue invoices"""
        result = await self.session.execute(
            select(ARInvoice)
            .where(
                ARInvoice.legal_entity_id == entity_id,
                ARInvoice.due_date < as_of_date,
                ARInvoice.outstanding_amount > 0
            )
            .order_by(ARInvoice.due_date)
            .limit(limit)
        )
        return list(result.scalars().all())
