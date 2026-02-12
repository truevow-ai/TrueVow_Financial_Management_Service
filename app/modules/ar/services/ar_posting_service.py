"""AR Posting Service - Posts AR invoices to ACCRUAL book"""
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.modules.general_ledger.services.journal_entry_service import JournalEntryService
from app.modules.general_ledger.repositories.gl_account_repository import GLAccountMappingRepository
from app.modules.general_ledger.repositories.book_repository import BookRepository
from app.modules.general_ledger.models.book_model import BookType
from app.modules.ar.repositories.ar_invoice_repository import ARInvoiceRepository
from app.modules.ar.repositories.ar_invoice_line_repository import ARInvoiceLineRepository
from app.modules.ar.models.ar_invoice_model import ARInvoice, InvoiceStatus
from app.core.exceptions import NotFoundError, ValidationError


class ARPostingService:
    """Service for posting AR invoices to ACCRUAL book"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.je_service = JournalEntryService(session)
        self.mapping_repo = GLAccountMappingRepository(session)
        self.book_repo = BookRepository(session)
        self.invoice_repo = ARInvoiceRepository(session)
        self.line_repo = ARInvoiceLineRepository(session)
    
    async def post_invoice(
        self,
        invoice_id: UUID,
        posted_by: UUID
    ) -> UUID:
        """Post invoice to ACCRUAL book"""
        invoice = await self.invoice_repo.get_by_id(invoice_id)
        if not invoice:
            raise NotFoundError(f"Invoice {invoice_id} not found")
        
        if invoice.status != InvoiceStatus.ISSUED:
            raise ValidationError(f"Cannot post invoice with status {invoice.status.value}")
        
        # Get ACCRUAL book
        accrual_book = await self.book_repo.get_by_entity_and_type(
            invoice.legal_entity_id,
            BookType.ACCRUAL
        )
        if not accrual_book:
            raise NotFoundError(f"ACCRUAL book not found for entity {invoice.legal_entity_id}")
        
        # Get period
        from app.modules.general_ledger.repositories.accounting_period_repository import AccountingPeriodRepository
        period_repo = AccountingPeriodRepository(self.session)
        accounting_period = await period_repo.get_by_book_and_date(
            accrual_book.id,
            invoice.invoice_date
        )
        if not accounting_period:
            raise NotFoundError(f"No period found for date {invoice.invoice_date}")
        
        # Get account mappings
        ar_account = await self._get_account_mapping(
            invoice.legal_entity_id,
            accrual_book.id,
            "AR"
        )
        
        # Get invoice lines
        lines = await self.line_repo.list_by_invoice(invoice_id)
        
        # Create journal entry
        entry = await self.je_service.create_draft_entry(
            book_id=accrual_book.id,
            entry_date=invoice.invoice_date,
            description=f"Invoice {invoice.invoice_number}: {invoice.description or 'AR Invoice'}",
            reference_number=invoice.invoice_number,
            source_service="billing",
            source_type="invoice_issued",
            source_id=invoice.id,
            idempotency_key=f"billing_invoice_{invoice.external_invoice_id}"
        )
        
        # Post each line
        for line in lines:
            if line.is_deferrable:
                # Deferrable line: Dr AR, Cr Deferred Revenue
                deferred_rev_account = await self._get_account_mapping(
                    invoice.legal_entity_id,
                    accrual_book.id,
                    "DEFERRED_REV"
                )
                
                await self.je_service.add_line(
                    journal_entry_id=entry.id,
                    gl_account_id=ar_account,
                    debit_fc=line.line_amount,
                    credit_fc=Decimal("0.00"),
                    currency=line.currency
                )
                
                await self.je_service.add_line(
                    journal_entry_id=entry.id,
                    gl_account_id=deferred_rev_account,
                    debit_fc=Decimal("0.00"),
                    credit_fc=line.line_amount,
                    currency=line.currency
                )
            else:
                # Immediate revenue: Dr AR, Cr Revenue
                revenue_account = await self._get_account_mapping(
                    invoice.legal_entity_id,
                    accrual_book.id,
                    "REV_SUBSCRIPTION"  # Or based on line type
                )
                
                await self.je_service.add_line(
                    journal_entry_id=entry.id,
                    gl_account_id=ar_account,
                    debit_fc=line.line_amount,
                    credit_fc=Decimal("0.00"),
                    currency=line.currency
                )
                
                await self.je_service.add_line(
                    journal_entry_id=entry.id,
                    gl_account_id=revenue_account,
                    debit_fc=Decimal("0.00"),
                    credit_fc=line.line_amount,
                    currency=line.currency
                )
        
        # Post entry with source_key: Use external_invoice_id if available, otherwise INTERNAL:invoice_id
        if invoice.external_invoice_id:
            source_key = f"AR_INVOICE:POST:{invoice.external_invoice_id}"
        else:
            source_key = f"AR_INVOICE:POST:INTERNAL:{invoice_id}"
        await self.je_service.post_entry(
            entry.id, 
            posted_by, 
            require_dimensions=False,
            source_key=source_key
        )
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
