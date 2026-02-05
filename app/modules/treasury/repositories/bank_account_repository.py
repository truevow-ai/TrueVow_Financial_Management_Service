"""Bank Account Repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.shared.repositories.base_repository import BaseRepository
from app.modules.treasury.models.bank_account_model import BankAccount


class BankAccountRepository(BaseRepository[BankAccount]):
    """Repository for BankAccount"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, BankAccount)
    
    async def list_by_entity(self, entity_id: UUID, active_only: bool = True) -> List[BankAccount]:
        """List bank accounts for an entity"""
        query = select(BankAccount).where(BankAccount.legal_entity_id == entity_id)
        if active_only:
            query = query.where(BankAccount.is_active == True)
        query = query.order_by(BankAccount.account_name)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_entity_and_currency(
        self,
        entity_id: UUID,
        currency: str
    ) -> List[BankAccount]:
        """Get accounts for entity and currency"""
        result = await self.session.execute(
            select(BankAccount).where(
                BankAccount.legal_entity_id == entity_id,
                BankAccount.currency == currency,
                BankAccount.is_active == True
            )
        )
        return list(result.scalars().all())
