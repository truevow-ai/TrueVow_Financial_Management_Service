"""AR Payment Repository"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.shared.repositories.base_repository import BaseRepository
from app.modules.ar.models.ar_payment_model import ARPayment


class ARPaymentRepository(BaseRepository[ARPayment]):
    """Repository for ARPayment"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ARPayment)
    
    async def get_by_external_id(self, external_payment_id: str) -> Optional[ARPayment]:
        """Get payment by external ID (Billing payment ID)"""
        result = await self.session.execute(
            select(ARPayment).where(ARPayment.external_payment_id == external_payment_id)
        )
        return result.scalar_one_or_none()
