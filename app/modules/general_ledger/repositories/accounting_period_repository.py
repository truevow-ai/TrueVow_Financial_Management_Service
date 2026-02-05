"""Accounting Period Repository"""
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from datetime import date
from app.shared.repositories.base_repository import BaseRepository
from app.modules.general_ledger.models.accounting_period_model import (
    AccountingPeriod,
    PeriodStatus
)


class AccountingPeriodRepository(BaseRepository[AccountingPeriod]):
    """Repository for AccountingPeriod"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, AccountingPeriod)
    
    async def get_by_book_and_date(
        self,
        book_id: UUID,
        period_date: date
    ) -> Optional[AccountingPeriod]:
        """Get period that contains the given date"""
        result = await self.session.execute(
            select(AccountingPeriod).where(
                AccountingPeriod.book_id == book_id,
                AccountingPeriod.period_start <= period_date,
                AccountingPeriod.period_end >= period_date
            )
        )
        return result.scalar_one_or_none()
    
    async def get_by_book_and_start(
        self,
        book_id: UUID,
        period_start: date
    ) -> Optional[AccountingPeriod]:
        """Get period by book and start date"""
        result = await self.session.execute(
            select(AccountingPeriod).where(
                AccountingPeriod.book_id == book_id,
                AccountingPeriod.period_start == period_start
            )
        )
        return result.scalar_one_or_none()
    
    async def list_by_book(
        self,
        book_id: UUID,
        status: Optional[PeriodStatus] = None
    ) -> List[AccountingPeriod]:
        """List periods for a book, optionally filtered by status"""
        query = select(AccountingPeriod).where(
            AccountingPeriod.book_id == book_id
        )
        if status:
            query = query.where(AccountingPeriod.status == status)
        query = query.order_by(AccountingPeriod.period_start.desc())
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_open_period(self, book_id: UUID) -> Optional[AccountingPeriod]:
        """Get the most recent open period for a book"""
        result = await self.session.execute(
            select(AccountingPeriod)
            .where(
                AccountingPeriod.book_id == book_id,
                AccountingPeriod.status == PeriodStatus.OPEN
            )
            .order_by(AccountingPeriod.period_start.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
