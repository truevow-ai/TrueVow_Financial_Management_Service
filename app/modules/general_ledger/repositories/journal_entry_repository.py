"""Journal Entry Repository"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.shared.repositories.base_repository import BaseRepository
from app.modules.general_ledger.models.journal_entry_model import (
    JournalEntry,
    JournalLine,
    JournalEntryStatus
)


class JournalEntryRepository(BaseRepository[JournalEntry]):
    """Repository for JournalEntry"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, JournalEntry)
    
    async def get_by_entry_number(self, entry_number: str) -> Optional[JournalEntry]:
        """Get entry by entry number"""
        result = await self.session.execute(
            select(JournalEntry).where(JournalEntry.entry_number == entry_number)
        )
        return result.scalar_one_or_none()
    
    async def get_by_idempotency_key(
        self,
        idempotency_key: str
    ) -> Optional[JournalEntry]:
        """Get entry by idempotency key"""
        result = await self.session.execute(
            select(JournalEntry).where(
                JournalEntry.idempotency_key == idempotency_key
            )
        )
        return result.scalar_one_or_none()
    
    async def list_by_book(
        self,
        book_id: UUID,
        status: Optional[JournalEntryStatus] = None,
        period_id: Optional[UUID] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[JournalEntry]:
        """List entries for a book with filters"""
        query = select(JournalEntry).where(JournalEntry.book_id == book_id)
        
        if status:
            query = query.where(JournalEntry.status == status)
        if period_id:
            query = query.where(JournalEntry.period_id == period_id)
        
        query = query.order_by(JournalEntry.entry_date.desc(), JournalEntry.entry_number.desc())
        query = query.limit(limit).offset(offset)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def verify_balance(self, journal_entry_id: UUID) -> bool:
        """Verify that journal entry balances (debits == credits)"""
        result = await self.session.execute(
            select(
                func.sum(JournalLine.debit_fc).label("total_debits"),
                func.sum(JournalLine.credit_fc).label("total_credits")
            ).where(JournalLine.journal_entry_id == journal_entry_id)
        )
        row = result.first()
        if not row:
            return False
        return row.total_debits == row.total_credits


class JournalLineRepository(BaseRepository[JournalLine]):
    """Repository for JournalLine"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, JournalLine)
    
    async def list_by_entry(self, journal_entry_id: UUID) -> List[JournalLine]:
        """List all lines for a journal entry"""
        result = await self.session.execute(
            select(JournalLine)
            .where(JournalLine.journal_entry_id == journal_entry_id)
            .order_by(JournalLine.line_number)
        )
        return list(result.scalars().all())
    
    async def get_account_balance(
        self,
        book_id: UUID,
        gl_account_id: UUID,
        as_of_date: Optional[date] = None
    ) -> dict[str, Decimal]:
        """Get account balance (debits and credits)"""
        query = select(
            func.sum(JournalLine.debit_fc).label("total_debits"),
            func.sum(JournalLine.credit_fc).label("total_credits")
        ).join(JournalEntry).where(
            JournalLine.book_id == book_id,
            JournalLine.gl_account_id == gl_account_id,
            JournalEntry.status == JournalEntryStatus.POSTED
        )
        
        if as_of_date:
            query = query.where(JournalEntry.entry_date <= as_of_date)
        
        result = await self.session.execute(query)
        row = result.first()
        
        return {
            "debits": row.total_debits or Decimal("0.00"),
            "credits": row.total_credits or Decimal("0.00"),
            "balance": (row.total_debits or Decimal("0.00")) - (row.total_credits or Decimal("0.00"))
        }
