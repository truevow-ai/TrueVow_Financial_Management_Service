"""Reconciliation Adjustment Posting Service"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.modules.general_ledger.repositories.reconciliation_adjustment_batch_repository import (
    ReconciliationAdjustmentBatchRepository
)
from app.modules.general_ledger.models.reconciliation_adjustment_batch_model import (
    AdjustmentBatchStatus
)
from app.modules.general_ledger.services.journal_entry_service import JournalEntryService
from app.modules.general_ledger.repositories.gl_account_repository import GLAccountMappingRepository
from app.core.exceptions import NotFoundError, ValidationError
from app.core.row_version import check_row_version


class ReconciliationAdjustmentPostingService:
    """Service for posting reconciliation adjustment batches to journal entries"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.batch_repo = ReconciliationAdjustmentBatchRepository(session)
        self.je_service = JournalEntryService(session)
        self.mapping_repo = GLAccountMappingRepository(session)
    
    async def post_adjustment_batch(
        self,
        batch_id: UUID,
        posted_by: UUID,
        row_version: Optional[int] = None
    ) -> UUID:
        """Post reconciliation adjustment batch to journal entry"""
        batch = await self.batch_repo.get_by_id(batch_id)
        if not batch:
            raise NotFoundError(f"Reconciliation adjustment batch {batch_id} not found")
        
        # Check row_version for optimistic locking
        check_row_version(batch.row_version, row_version, "reconciliation adjustment batch")
        
        if batch.status != AdjustmentBatchStatus.APPROVED:
            raise ValidationError(
                f"Cannot post adjustment batch in status {batch.status.value}. "
                "Must be APPROVED."
            )
        
        # Get reconciliation session to get period
        from app.modules.general_ledger.repositories.reconciliation_repository import ReconciliationSessionRepository
        session_repo = ReconciliationSessionRepository(self.session)
        session = await session_repo.get_by_id(batch.reconciliation_session_id)
        if not session:
            raise NotFoundError(f"Reconciliation session {batch.reconciliation_session_id} not found")
        
        # Get period for session end date
        from app.modules.general_ledger.repositories.accounting_period_repository import AccountingPeriodRepository
        period_repo = AccountingPeriodRepository(self.session)
        period = await period_repo.get_by_book_and_date(batch.book_id, session.period_end)
        if not period:
            raise NotFoundError(f"No period found for date {session.period_end}")
        
        # Get account mappings
        cash_account = await self._get_account_mapping(
            batch.legal_entity_id,
            batch.book_id,
            "CASH_BANK"
        )
        adjustment_account = await self._get_account_mapping(
            batch.legal_entity_id,
            batch.book_id,
            "ADJ_RECONCILIATION"
        )
        
        # Create journal entry
        entry = await self.je_service.create_draft_entry(
            book_id=batch.book_id,
            entry_date=session.period_end,
            description=f"Reconciliation adjustment: {batch.batch_number}",
            reference_number=batch.batch_number,
            source_service="fm",
            source_type="reconciliation_adjustment",
            source_id=batch.id
        )
        
        # Post adjustment: Dr/Cr cash, Cr/Dr adjustment account
        # If total_amount is positive, it's a deposit adjustment
        if batch.total_amount > 0:
            # Dr Cash, Cr Adjustment
            await self.je_service.add_line(
                journal_entry_id=entry.id,
                gl_account_id=cash_account,
                debit_fc=batch.total_amount,
                credit_fc=Decimal("0.00"),
                currency=batch.currency
            )
            await self.je_service.add_line(
                journal_entry_id=entry.id,
                gl_account_id=adjustment_account,
                debit_fc=Decimal("0.00"),
                credit_fc=batch.total_amount,
                currency=batch.currency
            )
        else:
            # Cr Cash, Dr Adjustment (for negative adjustments)
            await self.je_service.add_line(
                journal_entry_id=entry.id,
                gl_account_id=cash_account,
                debit_fc=Decimal("0.00"),
                credit_fc=abs(batch.total_amount),
                currency=batch.currency
            )
            await self.je_service.add_line(
                journal_entry_id=entry.id,
                gl_account_id=adjustment_account,
                debit_fc=abs(batch.total_amount),
                credit_fc=Decimal("0.00"),
                currency=batch.currency
            )
        
        # Post entry with source_key
        source_key = f"RECON_ADJ:POST:{batch_id}"
        await self.je_service.post_entry(
            entry.id,
            posted_by,
            require_dimensions=False,
            source_key=source_key
        )
        
        # Update batch (increment row_version)
        batch.row_version += 1
        await self.batch_repo.update(
            batch_id,
            status=AdjustmentBatchStatus.POSTED,
            posted_by=posted_by,
            posted_at=date.today(),
            journal_entry_id=entry.id,
            row_version=batch.row_version
        )
        
        await self.session.commit()
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
            raise NotFoundError(f"Account mapping '{map_key}' not found for entity {entity_id}, book {book_id}")
        return mapping.gl_account_id
