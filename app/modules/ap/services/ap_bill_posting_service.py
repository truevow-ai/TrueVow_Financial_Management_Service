"""AP Bill Posting Service"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.modules.ap.repositories.ap_bill_repository import APBillRepository
from app.modules.ap.repositories.ap_bill_line_repository import APBillLineRepository
from app.modules.general_ledger.services.journal_entry_service import JournalEntryService
from app.modules.general_ledger.repositories.gl_account_repository import GLAccountRepository
from app.modules.general_ledger.repositories.accounting_period_repository import AccountingPeriodRepository
from app.modules.ap.models.ap_bill_model import BillStatus
from app.core.exceptions import NotFoundError, ValidationError, PostingError, PeriodLockedError


class APBillPostingService:
    """Service for posting AP bills to journal entries"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.bill_repo = APBillRepository(session)
        self.line_repo = APBillLineRepository(session)
        self.je_service = JournalEntryService(session)
        self.account_repo = GLAccountRepository(session)
        self.period_repo = AccountingPeriodRepository(session)
    
    async def post_bill(
        self,
        bill_id: UUID,
        posted_by: UUID,
        row_version: Optional[int] = None
    ) -> UUID:
        """Post AP bill to ACCRUAL book"""
        bill = await self.bill_repo.get_by_id(bill_id)
        if not bill:
            raise NotFoundError(f"AP bill {bill_id} not found")
        
        # Check row_version for optimistic locking
        from app.core.row_version import check_row_version
        check_row_version(bill.row_version, row_version, "AP bill")
        
        if bill.status != BillStatus.APPROVED:
            raise ValidationError(f"Cannot post bill with status {bill.status.value}")
        
        # Get account mappings
        ap_expense = await self._get_account_mapping(
            bill.legal_entity_id,
            bill.book_id,
            "EXP_AP"
        )
        ap_liability = await self._get_account_mapping(
            bill.legal_entity_id,
            bill.book_id,
            "LIAB_AP"
        )
        
        # Get bill lines
        lines = await self.line_repo.list_by_bill(bill_id)
        if not lines:
            raise ValidationError("AP bill must have at least one line")
        
        # Create journal entry
        entry = await self.je_service.create_draft_entry(
            book_id=bill.book_id,
            entry_date=bill.bill_date,
            description=f"AP Bill {bill.bill_number}: {bill.description or 'Vendor invoice'}",
            reference_number=bill.bill_number,
            source_service="ap",
            source_type="ap_bill_posted",
            source_id=bill.id
        )
        
        # Dr AP Expense (total amount)
        await self.je_service.add_line(
            journal_entry_id=entry.id,
            gl_account_id=ap_expense,
            debit_fc=bill.total_amount,
            credit_fc=Decimal("0.00"),
            currency=bill.currency
        )
        
        # Cr AP Liability
        await self.je_service.add_line(
            journal_entry_id=entry.id,
            gl_account_id=ap_liability,
            debit_fc=Decimal("0.00"),
            credit_fc=bill.total_amount,
            currency=bill.currency
        )
        
        # Post entry with source_key
        source_key = f"AP_BILL:POST:{bill_id}"
        await self.je_service.post_entry(
            entry.id,
            posted_by,
            require_dimensions=False,
            source_key=source_key
        )
        
        # Update bill (increment row_version)
        bill.row_version += 1
        await self.bill_repo.update(
            bill_id,
            status=BillStatus.POSTED,
            posted_by=posted_by,
            posted_at=date.today(),
            journal_entry_id=entry.id,
            row_version=bill.row_version
        )
        
        await self.session.commit()
        return entry.id
    
    async def _get_account_mapping(
        self,
        legal_entity_id: UUID,
        book_id: UUID,
        map_key: str
    ) -> UUID:
        """Get GL account ID from mapping"""
        from app.modules.general_ledger.repositories.gl_account_repository import GLAccountMappingRepository
        mapping_repo = GLAccountMappingRepository(self.session)
        mapping = await mapping_repo.get_by_key(legal_entity_id, book_id, map_key)
        if not mapping:
            raise ValidationError(f"Account mapping '{map_key}' not found for entity {legal_entity_id}, book {book_id}")
        return mapping.gl_account_id
