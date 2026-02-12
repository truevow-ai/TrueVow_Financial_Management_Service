"""AR Customer Repository"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.shared.repositories.base_repository import BaseRepository
from app.modules.ar.models.ar_customer_model import ARCustomer


class ARCustomerRepository(BaseRepository[ARCustomer]):
    """Repository for ARCustomer"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ARCustomer)
    
    async def get_by_external_id(self, external_customer_id: str) -> Optional[ARCustomer]:
        """Get customer by external ID (Billing customer ID)"""
        result = await self.session.execute(
            select(ARCustomer).where(ARCustomer.external_customer_id == external_customer_id)
        )
        return result.scalar_one_or_none()
