"""AR Invoice Line Repository"""
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.shared.repositories.base_repository import BaseRepository
from app.modules.ar.models.ar_invoice_model import ARInvoiceLine


class ARInvoiceLineRepository(BaseRepository[ARInvoiceLine]):
    """Repository for ARInvoiceLine"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ARInvoiceLine)
    
    async def list_by_invoice(self, invoice_id: UUID) -> List[ARInvoiceLine]:
        """List lines for an invoice"""
        result = await self.session.execute(
            select(ARInvoiceLine)
            .where(ARInvoiceLine.ar_invoice_id == invoice_id)
            .order_by(ARInvoiceLine.line_number)
        )
        return list(result.scalars().all())
