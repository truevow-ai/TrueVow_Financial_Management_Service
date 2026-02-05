"""Bank Transaction Repository"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from datetime import date, datetime
from app.shared.repositories.base_repository import BaseRepository
from app.modules.treasury.models.bank_transaction_model import BankTransaction, TransactionType


class BankTransactionRepository(BaseRepository[BankTransaction]):
    """Repository for BankTransaction"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, BankTransaction)
    
    async def get_by_external_id(self, external_id: str) -> Optional[BankTransaction]:
        """Get transaction by external ID (for dedupe)"""
        result = await self.session.execute(
            select(BankTransaction).where(BankTransaction.external_id == external_id)
        )
        return result.scalar_one_or_none()
    
    async def list_by_account(
        self,
        bank_account_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        is_reconciled: Optional[bool] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[BankTransaction]:
        """List transactions for an account with filters"""
        query = select(BankTransaction).where(
            BankTransaction.bank_account_id == bank_account_id
        )
        
        if start_date:
            query = query.where(BankTransaction.transaction_date >= start_date)
        if end_date:
            query = query.where(BankTransaction.transaction_date <= end_date)
        if is_reconciled is not None:
            query = query.where(BankTransaction.is_reconciled == is_reconciled)
        
        query = query.order_by(
            BankTransaction.transaction_date.desc(),
            BankTransaction.created_at.desc()
        )
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def list_with_cursor(
        self,
        bank_account_id: Optional[UUID] = None,
        updated_after: Optional[datetime] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> tuple[List[BankTransaction], Optional[str]]:
        """List transactions with cursor pagination"""
        query = select(BankTransaction)
        
        if bank_account_id:
            query = query.where(BankTransaction.bank_account_id == bank_account_id)
        if updated_after:
            query = query.where(BankTransaction.updated_at > updated_after)
        if cursor:
            # Cursor is the ID of the last item from previous page
            query = query.where(BankTransaction.id > UUID(cursor))
        
        query = query.order_by(BankTransaction.updated_at, BankTransaction.id)
        query = query.limit(limit + 1)  # Fetch one extra to check if there's more
        
        result = await self.session.execute(query)
        transactions = list(result.scalars().all())
        
        # Determine next cursor
        next_cursor = None
        if len(transactions) > limit:
            transactions = transactions[:limit]
            next_cursor = str(transactions[-1].id)
        
        return transactions, next_cursor
    
    async def list_unreconciled(
        self,
        bank_account_id: UUID,
        limit: int = 1000
    ) -> List[BankTransaction]:
        """List unreconciled transactions"""
        return await self.list_by_account(
            bank_account_id=bank_account_id,
            is_reconciled=False,
            limit=limit
        )
