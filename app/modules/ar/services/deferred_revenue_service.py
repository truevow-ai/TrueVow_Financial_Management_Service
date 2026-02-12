"""Deferred Revenue Service - Revenue recognition"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal
from calendar import monthrange
from app.modules.ar.repositories.deferred_revenue_repository import (
    RevenueScheduleRepository,
    RevenueSchedulePeriodRepository
)
from app.modules.ar.repositories.ar_invoice_line_repository import ARInvoiceLineRepository
from app.modules.general_ledger.services.journal_entry_service import JournalEntryService
from app.modules.general_ledger.repositories.gl_account_repository import GLAccountMappingRepository
from app.modules.general_ledger.repositories.book_repository import BookRepository
from app.modules.general_ledger.models.book_model import BookType
from app.modules.ar.models.deferred_revenue_model import (
    RevenueSchedule,
    RevenueSchedulePeriod,
    ScheduleStatus
)
from app.core.exceptions import NotFoundError, ValidationError


class DeferredRevenueService:
    """Service for deferred revenue recognition"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.schedule_repo = RevenueScheduleRepository(session)
        self.period_repo = RevenueSchedulePeriodRepository(session)
        self.line_repo = ARInvoiceLineRepository(session)
        self.je_service = JournalEntryService(session)
        self.mapping_repo = GLAccountMappingRepository(session)
        self.book_repo = BookRepository(session)
    
    async def create_schedule_from_invoice_line(
        self,
        invoice_line_id: UUID,
        book_id: UUID
    ) -> RevenueSchedule:
        """Create revenue schedule from invoice line"""
        # Get invoice line
        invoice_line = await self.line_repo.get_by_id(invoice_line_id)
        if not invoice_line:
            raise NotFoundError(f"Invoice line {invoice_line_id} not found")
        
        if not invoice_line.is_deferrable:
            raise ValidationError("Invoice line is not deferrable")
        
        if not invoice_line.service_start or not invoice_line.service_end:
            raise ValidationError("Invoice line must have service_start and service_end for deferred revenue")
        
        # Get invoice to get entity_id
        from app.modules.ar.repositories.ar_invoice_repository import ARInvoiceRepository
        invoice_repo = ARInvoiceRepository(self.session)
        invoice = await invoice_repo.get_by_id(invoice_line.ar_invoice_id)
        if not invoice:
            raise NotFoundError(f"Invoice {invoice_line.ar_invoice_id} not found")
        
        # Check if schedule already exists
        existing = await self.schedule_repo.get_by_invoice_line(invoice_line_id)
        if existing:
            return existing
        
        # Create schedule
        schedule = await self.schedule_repo.create(
            legal_entity_id=invoice.legal_entity_id,
            book_id=book_id,
            ar_invoice_id=invoice_line.ar_invoice_id,
            ar_invoice_line_id=invoice_line_id,
            total_amount=invoice_line.line_amount,
            currency=invoice_line.currency,
            service_start=invoice_line.service_start,
            service_end=invoice_line.service_end,
            recognition_cadence="MONTHLY",
            status=ScheduleStatus.ACTIVE
        )
        
        # Generate monthly periods
        await self._generate_periods(schedule)
        
        await self.session.commit()
        return schedule
    
    async def _generate_periods(self, schedule: RevenueSchedule):
        """Generate monthly recognition periods"""
        current_date = schedule.service_start
        total_days = (schedule.service_end - schedule.service_start).days + 1
        daily_amount = schedule.total_amount / Decimal(str(total_days))
        
        while current_date <= schedule.service_end:
            # Get last day of month
            last_day = monthrange(current_date.year, current_date.month)[1]
            period_end = date(current_date.year, current_date.month, last_day)
            if period_end > schedule.service_end:
                period_end = schedule.service_end
            
            # Calculate days in period
            period_days = (period_end - current_date).days + 1
            period_amount = daily_amount * Decimal(str(period_days))
            
            # Create period
            await self.period_repo.create(
                revenue_schedule_id=schedule.id,
                period_start=current_date,
                period_end=period_end,
                recognition_amount=period_amount,
                currency=schedule.currency,
                is_recognized=False
            )
            
            # Move to next month
            if current_date.month == 12:
                current_date = date(current_date.year + 1, 1, 1)
            else:
                current_date = date(current_date.year, current_date.month + 1, 1)
    
    async def run_revenue_recognition(
        self,
        book_id: UUID,
        period_start: date,
        period_end: date,
        posted_by: UUID
    ) -> tuple[int, List[UUID]]:
        """Run revenue recognition for a period
        
        Returns: (recognized_count, journal_entry_ids)
        """
        # Get unrecognized periods
        periods = await self.period_repo.list_unrecognized_by_period(
            period_start=period_start,
            period_end=period_end
        )
        
        # Filter by book - need to load schedules
        book_periods = []
        for p in periods:
            schedule = await self.schedule_repo.get_by_id(p.revenue_schedule_id)
            if schedule and schedule.book_id == book_id:
                book_periods.append(p)
        
        recognized_count = 0
        entry_ids = []
        
        for period in book_periods:
            try:
                # Post recognition entry
                entry_id = await self._post_recognition_entry(period, posted_by)
                entry_ids.append(entry_id)
                
                # Mark period as recognized
                await self.period_repo.update(
                    period.id,
                    is_recognized=True,
                    recognized_at=date.today(),
                    journal_entry_id=entry_id
                )
                recognized_count += 1
            except Exception as e:
                # Log error but continue
                continue
        
        await self.session.commit()
        return recognized_count, entry_ids
    
    async def _post_recognition_entry(
        self,
        period: RevenueSchedulePeriod,
        posted_by: UUID
    ) -> UUID:
        """Post revenue recognition journal entry"""
        schedule = period.schedule
        
        # Get account mappings
        deferred_rev_account = await self._get_account_mapping(
            schedule.legal_entity_id,
            schedule.book_id,
            "DEFERRED_REV"
        )
        revenue_account = await self._get_account_mapping(
            schedule.legal_entity_id,
            schedule.book_id,
            "REV_SUBSCRIPTION"
        )
        
        # Get period for entry date
        from app.modules.general_ledger.repositories.accounting_period_repository import AccountingPeriodRepository
        period_repo = AccountingPeriodRepository(self.session)
        accounting_period = await period_repo.get_by_book_and_date(
            schedule.book_id,
            period.period_start
        )
        if not accounting_period:
            raise NotFoundError(f"No accounting period found for {period.period_start}")
        
        # Create journal entry
        entry = await self.je_service.create_draft_entry(
            book_id=schedule.book_id,
            entry_date=period.period_start,
            description=f"Revenue recognition: {schedule.invoice.invoice_number} - {period.period_start}",
            reference_number=f"REVREC-{schedule.id}-{period.period_start}",
            source_service="fm",
            source_type="revenue_recognition",
            source_id=period.id,
            idempotency_key=f"revrec_{schedule.id}_{period.period_start}"
        )
        
        # Add lines: Dr Deferred Revenue, Cr Revenue
        await self.je_service.add_line(
            journal_entry_id=entry.id,
            gl_account_id=deferred_rev_account,
            debit_fc=period.recognition_amount,
            credit_fc=Decimal("0.00"),
            currency=period.currency
        )
        
        await self.je_service.add_line(
            journal_entry_id=entry.id,
            gl_account_id=revenue_account,
            debit_fc=Decimal("0.00"),
            credit_fc=period.recognition_amount,
            currency=period.currency
        )
        
        # Post entry
        await self.je_service.post_entry(entry.id, posted_by, require_dimensions=False)
        return entry.id
    
    async def _get_account_mapping(
        self,
        entity_id: UUID,
        book_id: UUID,
        map_key: str
    ) -> UUID:
        """Get GL account from mapping"""
        mapping = await self.mapping_repo.get_mapping(entity_id, book_id, map_key)
        if not mapping:
            raise NotFoundError(f"Account mapping not found: {map_key}")
        return mapping.gl_account_id
