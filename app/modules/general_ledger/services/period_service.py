"""Accounting Period Service"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date, timedelta
from calendar import monthrange
from app.modules.general_ledger.repositories.accounting_period_repository import (
    AccountingPeriodRepository
)
from app.modules.general_ledger.repositories.book_repository import BookRepository
from app.modules.general_ledger.models.accounting_period_model import (
    AccountingPeriod,
    PeriodStatus
)
from app.core.exceptions import NotFoundError, ValidationError, PeriodLockedError


class PeriodService:
    """Service for accounting period management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.period_repo = AccountingPeriodRepository(session)
        self.book_repo = BookRepository(session)
    
    async def generate_periods(
        self,
        book_id: UUID,
        start_year: int,
        start_month: int,
        num_months: int = 12
    ) -> List[AccountingPeriod]:
        """Generate accounting periods for a book"""
        # Verify book exists
        book = await self.book_repo.get_by_id(book_id)
        if not book:
            raise NotFoundError(f"Book {book_id} not found")
        
        periods = []
        current_date = date(start_year, start_month, 1)
        
        for _ in range(num_months):
            # Get last day of month
            last_day = monthrange(current_date.year, current_date.month)[1]
            period_end = date(current_date.year, current_date.month, last_day)
            
            # Check if period already exists
            existing = await self.period_repo.get_by_book_and_start(book_id, current_date)
            if not existing:
                period_name = current_date.strftime("%Y-%m")
                period = await self.period_repo.create(
                    book_id=book_id,
                    period_start=current_date,
                    period_end=period_end,
                    period_name=period_name,
                    status=PeriodStatus.OPEN
                )
                periods.append(period)
            
            # Move to next month
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)
        
        await self.session.commit()
        return periods
    
    async def get_period(self, period_id: UUID) -> Optional[AccountingPeriod]:
        """Get period by ID"""
        return await self.period_repo.get_by_id(period_id)
    
    async def get_period_for_date(
        self,
        book_id: UUID,
        period_date: date
    ) -> Optional[AccountingPeriod]:
        """Get period that contains the given date"""
        return await self.period_repo.get_by_book_and_date(book_id, period_date)
    
    async def list_periods(
        self,
        book_id: UUID,
        status: Optional[PeriodStatus] = None
    ) -> List[AccountingPeriod]:
        """List periods for a book"""
        return await self.period_repo.list_by_book(book_id, status)
    
    async def close_period(
        self,
        period_id: UUID,
        closed_by: UUID,
        reason: Optional[str] = None
    ) -> AccountingPeriod:
        """Close an accounting period"""
        period = await self.period_repo.get_by_id(period_id)
        if not period:
            raise NotFoundError(f"Period {period_id} not found")
        
        if period.status == PeriodStatus.LOCKED:
            raise PeriodLockedError(f"Period {period_id} is locked and cannot be closed")
        
        if period.status == PeriodStatus.CLOSED:
            raise ValidationError(f"Period {period_id} is already closed")
        
        await self.period_repo.update(
            period_id,
            status=PeriodStatus.CLOSED,
            closed_by=closed_by,
            closed_at=date.today(),
            lock_reason=reason
        )
        await self.session.commit()
        return await self.period_repo.get_by_id(period_id)
    
    async def lock_period(
        self,
        period_id: UUID,
        locked_by: UUID,
        reason: str
    ) -> AccountingPeriod:
        """Lock an accounting period (prevents all postings)"""
        period = await self.period_repo.get_by_id(period_id)
        if not period:
            raise NotFoundError(f"Period {period_id} not found")
        
        if period.status == PeriodStatus.LOCKED:
            raise ValidationError(f"Period {period_id} is already locked")
        
        # Period must be closed before locking
        if period.status != PeriodStatus.CLOSED:
            raise ValidationError("Period must be closed before locking")
        
        await self.period_repo.update(
            period_id,
            status=PeriodStatus.LOCKED,
            closed_by=locked_by,
            lock_reason=reason
        )
        await self.session.commit()
        return await self.period_repo.get_by_id(period_id)
    
    async def soft_close_period(
        self,
        period_id: UUID,
        closed_by: UUID,
        reason: Optional[str] = None
    ) -> AccountingPeriod:
        """Soft close a period (allows postings with elevated role)"""
        period = await self.period_repo.get_by_id(period_id)
        if not period:
            raise NotFoundError(f"Period {period_id} not found")
        
        if period.status in [PeriodStatus.CLOSED, PeriodStatus.LOCKED]:
            raise ValidationError(f"Period {period_id} is already closed or locked")
        
        await self.period_repo.update(
            period_id,
            status=PeriodStatus.SOFT_CLOSED,
            closed_by=closed_by,
            closed_at=date.today(),
            lock_reason=reason
        )
        await self.session.commit()
        return await self.period_repo.get_by_id(period_id)
