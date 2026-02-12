"""AP Bill Repository"""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.shared.repositories.base_repository import BaseRepository
from app.modules.ap.models.ap_bill_model import APBill, BillStatus


class APBillRepository(BaseRepository[APBill]):
    """Repository for AP Bill"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, APBill)

    async def list_by_book(
        self,
        entity_id: UUID,
        book_id: UUID,
        vendor_id: Optional[UUID] = None,
        status: Optional[BillStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[APBill]:
        """List AP bills for a book with optional filters"""
        q = select(APBill).where(
            APBill.legal_entity_id == entity_id,
            APBill.book_id == book_id,
        )
        if vendor_id is not None:
            q = q.where(APBill.ap_vendor_id == vendor_id)
        if status is not None:
            q = q.where(APBill.status == status)
        q = q.order_by(APBill.bill_date.desc()).limit(limit).offset(offset)
        result = await self.session.execute(q)
        return list(result.scalars().all())
