"""
Period Close Checklist Service
Computes and manages period close checklist items
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from uuid import UUID
from datetime import datetime

from app.modules.general_ledger.models.period_close_checklist_model import (
    PeriodCloseChecklist,
    ChecklistItemCode,
    ChecklistItemStatus
)
from app.modules.general_ledger.models.accounting_period_model import AccountingPeriod
from app.modules.general_ledger.repositories.accounting_period_repository import AccountingPeriodRepository
from app.core.logging import logger


class PeriodCloseChecklistService:
    """Service for managing period close checklist"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.period_repo = AccountingPeriodRepository(session)
    
    async def compute_checklist(
        self,
        period_id: UUID,
        computed_by: Optional[UUID] = None
    ) -> List[PeriodCloseChecklist]:
        """
        Compute checklist status for a period.
        Creates or updates checklist items based on current period state.
        """
        period = await self.period_repo.get_by_id(period_id)
        if not period:
            raise ValueError(f"Period {period_id} not found")
        
        # Get or create checklist items
        checklist_items = []
        
        for item_code in ChecklistItemCode:
            # Check if item already exists
            stmt = select(PeriodCloseChecklist).where(
                and_(
                    PeriodCloseChecklist.period_id == period_id,
                    PeriodCloseChecklist.item_code == item_code
                )
            )
            result = await self.session.execute(stmt)
            item = result.scalar_one_or_none()
            
            if not item:
                # Create new item
                item = PeriodCloseChecklist(
                    period_id=period_id,
                    item_code=item_code,
                    status=ChecklistItemStatus.PENDING
                )
                self.session.add(item)
            
            # Compute status for this item
            status = await self._compute_item_status(period, item_code)
            item.status = status
            item.computed_at = datetime.utcnow()
            item.computed_by = computed_by
            
            checklist_items.append(item)
        
        await self.session.commit()
        return checklist_items
    
    async def _compute_item_status(
        self,
        period: AccountingPeriod,
        item_code: ChecklistItemCode
    ) -> ChecklistItemStatus:
        """Compute status for a specific checklist item"""
        
        if item_code == ChecklistItemCode.BANK_REC_DONE:
            return await self._check_bank_reconciliations(period)
        
        elif item_code == ChecklistItemCode.REVREC_DONE:
            return await self._check_revrec_complete(period)
        
        elif item_code == ChecklistItemCode.PAYROLL_POSTED:
            return await self._check_payroll_posted(period)
        
        elif item_code == ChecklistItemCode.ROYALTY_POSTED:
            return await self._check_royalty_posted(period)
        
        elif item_code == ChecklistItemCode.AR_AGING_READY:
            return await self._check_ar_aging_ready(period)
        
        elif item_code == ChecklistItemCode.AP_AGING_READY:
            return await self._check_ap_aging_ready(period)
        
        else:
            return ChecklistItemStatus.PENDING
    
    async def _check_bank_reconciliations(
        self,
        period: AccountingPeriod
    ) -> ChecklistItemStatus:
        """Check if all bank reconciliations are closed for the period"""
        from app.modules.general_ledger.models.reconciliation_model import ReconciliationSession, ReconciliationStatus
        from app.modules.treasury.repositories.bank_account_repository import BankAccountRepository
        
        # Get all active bank accounts for the book's entity
        from app.modules.general_ledger.models.book_model import Book
        book_stmt = select(Book).where(Book.id == period.book_id)
        book_result = await self.session.execute(book_stmt)
        book = book_result.scalar_one_or_none()
        
        if not book:
            return ChecklistItemStatus.PENDING
        
        account_repo = BankAccountRepository(self.session)
        accounts = await account_repo.list_by_entity(book.legal_entity_id, active_only=True)
        
        if not accounts:
            # No bank accounts, skip this check
            return ChecklistItemStatus.SKIPPED
        
        # Check if all accounts have closed reconciliations for this period
        for account in accounts:
            rec_stmt = select(ReconciliationSession).where(
                and_(
                    ReconciliationSession.bank_account_id == account.id,
                    ReconciliationSession.period_start <= period.period_end,
                    ReconciliationSession.period_end >= period.period_start
                )
            )
            rec_result = await self.session.execute(rec_stmt)
            reconciliations = rec_result.scalars().all()
            
            if not reconciliations:
                # No reconciliation session for this account/period
                return ChecklistItemStatus.PENDING
            
            # Check if all are closed
            for rec in reconciliations:
                if rec.status != ReconciliationStatus.CLOSED:
                    return ChecklistItemStatus.PENDING
        
        return ChecklistItemStatus.COMPLETE
    
    async def _check_revrec_complete(
        self,
        period: AccountingPeriod
    ) -> ChecklistItemStatus:
        """Check if revenue recognition run is complete for the period"""
        # TODO: Implement when RevRec module is created
        # For now, skip if ACCRUAL book, pending if CASH book
        from app.modules.general_ledger.models.book_model import Book
        from app.modules.general_ledger.models.book_model import BookType
        
        book_stmt = select(Book).where(Book.id == period.book_id)
        book_result = await self.session.execute(book_stmt)
        book = book_result.scalar_one_or_none()
        
        if book and book.book_type == BookType.CASH:
            return ChecklistItemStatus.SKIPPED  # RevRec only for ACCRUAL
        
        # Placeholder: return PENDING until RevRec is implemented
        return ChecklistItemStatus.PENDING
    
    async def _check_payroll_posted(
        self,
        period: AccountingPeriod
    ) -> ChecklistItemStatus:
        """Check if payroll runs are posted for the period"""
        from app.modules.payroll.models.payroll_run_model import PayrollRun, PayrollRunStatus
        
        # Get entity from book
        from app.modules.general_ledger.models.book_model import Book
        book_stmt = select(Book).where(Book.id == period.book_id)
        book_result = await self.session.execute(book_stmt)
        book = book_result.scalar_one_or_none()
        
        if not book:
            return ChecklistItemStatus.PENDING
        
        # Check if any payroll runs exist for this period
        payroll_stmt = select(PayrollRun).where(
            and_(
                PayrollRun.legal_entity_id == book.legal_entity_id,
                PayrollRun.pay_period_start <= period.period_end,
                PayrollRun.pay_period_end >= period.period_start
            )
        )
        payroll_result = await self.session.execute(payroll_stmt)
        payroll_runs = payroll_result.scalars().all()
        
        if not payroll_runs:
            # No payroll runs for this period - skip
            return ChecklistItemStatus.SKIPPED
        
        # Check if all are posted
        for run in payroll_runs:
            if run.status != PayrollRunStatus.POSTED:
                return ChecklistItemStatus.PENDING
        
        return ChecklistItemStatus.COMPLETE
    
    async def _check_royalty_posted(
        self,
        period: AccountingPeriod
    ) -> ChecklistItemStatus:
        """Check if royalty runs are posted for the period"""
        from app.modules.intercompany.models.royalty_model import RoyaltyCalculation, RoyaltyRunStatus
        
        # Get entity from book
        from app.modules.general_ledger.models.book_model import Book
        book_stmt = select(Book).where(Book.id == period.book_id)
        book_result = await self.session.execute(book_stmt)
        book = book_result.scalar_one_or_none()
        
        if not book:
            return ChecklistItemStatus.PENDING
        
        # Check if any royalty calculations exist for this period
        royalty_stmt = select(RoyaltyCalculation).where(
            and_(
                RoyaltyCalculation.period_start <= period.period_end,
                RoyaltyCalculation.period_end >= period.period_start
            )
        )
        royalty_result = await self.session.execute(royalty_stmt)
        royalty_calcs = royalty_result.scalars().all()
        
        if not royalty_calcs:
            # No royalty runs for this period - skip
            return ChecklistItemStatus.SKIPPED
        
        # Check if all are posted (status is POSTED or has journal_entry_id)
        for calc in royalty_calcs:
            if calc.status != RoyaltyRunStatus.POSTED and not calc.journal_entry_id:
                return ChecklistItemStatus.PENDING
        
        return ChecklistItemStatus.COMPLETE
    
    async def _check_ar_aging_ready(
        self,
        period: AccountingPeriod
    ) -> ChecklistItemStatus:
        """Check if AR aging report is ready"""
        # TODO: Implement when AR module is created
        # For now, return COMPLETE as placeholder
        return ChecklistItemStatus.COMPLETE
    
    async def _check_ap_aging_ready(
        self,
        period: AccountingPeriod
    ) -> ChecklistItemStatus:
        """Check if AP aging report is ready"""
        # TODO: Implement when AP module is created
        # For now, return COMPLETE as placeholder
        return ChecklistItemStatus.COMPLETE
    
    async def get_checklist(
        self,
        period_id: UUID
    ) -> List[PeriodCloseChecklist]:
        """Get checklist for a period"""
        stmt = select(PeriodCloseChecklist).where(
            PeriodCloseChecklist.period_id == period_id
        ).order_by(PeriodCloseChecklist.item_code)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
    
    async def mark_item_complete(
        self,
        period_id: UUID,
        item_code: ChecklistItemCode,
        notes: Optional[str] = None,
        user_id: Optional[UUID] = None
    ) -> PeriodCloseChecklist:
        """Manually mark a checklist item as complete"""
        stmt = select(PeriodCloseChecklist).where(
            and_(
                PeriodCloseChecklist.period_id == period_id,
                PeriodCloseChecklist.item_code == item_code
            )
        )
        result = await self.session.execute(stmt)
        item = result.scalar_one_or_none()
        
        if not item:
            item = PeriodCloseChecklist(
                period_id=period_id,
                item_code=item_code,
                status=ChecklistItemStatus.COMPLETE,
                computed_by=user_id,
                computed_at=datetime.utcnow(),
                notes=notes
            )
            self.session.add(item)
        else:
            item.status = ChecklistItemStatus.COMPLETE
            item.computed_by = user_id
            item.computed_at = datetime.utcnow()
            if notes:
                item.notes = notes
        
        await self.session.commit()
        return item
