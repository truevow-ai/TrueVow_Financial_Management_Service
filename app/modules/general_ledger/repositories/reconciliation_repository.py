"""Reconciliation Repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.shared.repositories.base_repository import BaseRepository
from app.modules.general_ledger.models.reconciliation_model import (
    ReconciliationSession,
    ReconciliationMatch,
    ReconciliationStatus
)


class ReconciliationSessionRepository(BaseRepository[ReconciliationSession]):
    """Repository for ReconciliationSession"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ReconciliationSession)
    
    async def list_by_account(
        self,
        bank_account_id: UUID,
        status: Optional[ReconciliationStatus] = None
    ) -> List[ReconciliationSession]:
        """List reconciliation sessions for a bank account"""
        query = select(ReconciliationSession).where(
            ReconciliationSession.bank_account_id == bank_account_id
        )
        if status:
            query = query.where(ReconciliationSession.status == status)
        query = query.order_by(ReconciliationSession.period_end.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())


class ReconciliationMatchRepository(BaseRepository[ReconciliationMatch]):
    """Repository for ReconciliationMatch"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, ReconciliationMatch)
    
    async def list_by_session(self, session_id: UUID) -> List[ReconciliationMatch]:
        """List matches for a reconciliation session"""
        result = await self.session.execute(
            select(ReconciliationMatch)
            .where(ReconciliationMatch.reconciliation_session_id == session_id)
        )
        return list(result.scalars().all())
    
    async def get_by_transaction(
        self,
        session_id: UUID,
        bank_transaction_id: UUID
    ) -> Optional[ReconciliationMatch]:
        """Get match by transaction"""
        result = await self.session.execute(
            select(ReconciliationMatch).where(
                ReconciliationMatch.reconciliation_session_id == session_id,
                ReconciliationMatch.bank_transaction_id == bank_transaction_id
            )
        )
        return result.scalar_one_or_none()
