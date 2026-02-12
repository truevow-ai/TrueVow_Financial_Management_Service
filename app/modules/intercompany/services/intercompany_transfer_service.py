"""Intercompany Transfer Service"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.modules.intercompany.repositories.intercompany_transfer_repository import IntercompanyTransferRepository
from app.modules.general_ledger.repositories.legal_entity_repository import LegalEntityRepository
from app.modules.general_ledger.repositories.book_repository import BookRepository
from app.modules.general_ledger.models.book_model import BookType
from app.modules.general_ledger.services.journal_entry_service import JournalEntryService
from app.modules.general_ledger.repositories.gl_account_repository import GLAccountMappingRepository
from app.modules.intercompany.models.intercompany_transfer_model import IntercompanyTransfer
from app.core.exceptions import NotFoundError, ValidationError


class IntercompanyTransferService:
    """Service for intercompany transfers"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.transfer_repo = IntercompanyTransferRepository(session)
        self.entity_repo = LegalEntityRepository(session)
        self.book_repo = BookRepository(session)
        self.je_service = JournalEntryService(session)
        self.mapping_repo = GLAccountMappingRepository(session)
    
    async def create_transfer(
        self,
        from_entity_id: UUID,
        to_entity_id: UUID,
        transfer_date: date,
        amount: Decimal,
        currency: str,
        transfer_type: str = "CASH",
        description: Optional[str] = None,
        reference_number: Optional[str] = None,
        from_bank_account_id: Optional[UUID] = None,
        to_bank_account_id: Optional[UUID] = None
    ) -> IntercompanyTransfer:
        """Create intercompany transfer"""
        # Verify entities exist
        from_entity = await self.entity_repo.get_by_id(from_entity_id)
        to_entity = await self.entity_repo.get_by_id(to_entity_id)
        
        if not from_entity:
            raise NotFoundError(f"From entity {from_entity_id} not found")
        if not to_entity:
            raise NotFoundError(f"To entity {to_entity_id} not found")
        
        if from_entity_id == to_entity_id:
            raise ValidationError("From and to entities must be different")
        
        # Create transfer
        transfer = await self.transfer_repo.create(
            from_entity_id=from_entity_id,
            to_entity_id=to_entity_id,
            transfer_date=transfer_date,
            amount=amount,
            currency=currency,
            transfer_type=transfer_type,
            description=description,
            reference_number=reference_number,
            from_bank_account_id=from_bank_account_id,
            to_bank_account_id=to_bank_account_id,
            is_reconciled=False
        )
        
        await self.session.commit()
        return transfer
    
    async def post_transfer(
        self,
        transfer_id: UUID,
        posted_by: UUID
    ) -> tuple[UUID, UUID]:
        """Post transfer to both entities' ACCRUAL books
        
        Returns: (from_entity_je_id, to_entity_je_id)
        """
        transfer = await self.transfer_repo.get_by_id(transfer_id)
        if not transfer:
            raise NotFoundError(f"Transfer {transfer_id} not found")
        
        # Get ACCRUAL books for both entities
        from_book = await self.book_repo.get_by_entity_and_type(
            transfer.from_entity_id,
            BookType.ACCRUAL
        )
        to_book = await self.book_repo.get_by_entity_and_type(
            transfer.to_entity_id,
            BookType.ACCRUAL
        )
        
        if not from_book:
            raise NotFoundError(f"ACCRUAL book not found for entity {transfer.from_entity_id}")
        if not to_book:
            raise NotFoundError(f"ACCRUAL book not found for entity {transfer.to_entity_id}")
        
        # Get periods
        from app.modules.general_ledger.repositories.accounting_period_repository import AccountingPeriodRepository
        period_repo = AccountingPeriodRepository(self.session)
        
        from_period = await period_repo.get_by_book_and_date(from_book.id, transfer.transfer_date)
        to_period = await period_repo.get_by_book_and_date(to_book.id, transfer.transfer_date)
        
        if not from_period:
            raise NotFoundError(f"No period found for date {transfer.transfer_date} in from entity")
        if not to_period:
            raise NotFoundError(f"No period found for date {transfer.transfer_date} in to entity")
        
        # Get account mappings
        from_interco_account = await self._get_account_mapping(
            transfer.from_entity_id,
            from_book.id,
            "INTERCO_PAYABLE"
        )
        to_interco_account = await self._get_account_mapping(
            transfer.to_entity_id,
            to_book.id,
            "INTERCO_RECEIVABLE"
        )
        
        # From entity: Dr Intercompany Payable, Cr Cash/Bank
        from_je = await self.je_service.create_draft_entry(
            book_id=from_book.id,
            entry_date=transfer.transfer_date,
            description=f"Intercompany transfer to {to_entity.code}: {transfer.description or transfer.reference_number}",
            reference_number=transfer.reference_number,
            source_service="intercompany",
            source_type="intercompany_transfer",
            source_id=transfer.id,
            idempotency_key=f"interco_transfer_{transfer.id}_from"
        )
        
        await self.je_service.add_line(
            journal_entry_id=from_je.id,
            gl_account_id=from_interco_account,
            debit_fc=transfer.amount,
            credit_fc=Decimal("0.00"),
            currency=transfer.currency
        )
        
        # Cash account (if bank account provided)
        if transfer.from_bank_account_id:
            cash_account = await self._get_account_mapping(
                transfer.from_entity_id,
                from_book.id,
                "CASH_BANK"
            )
            await self.je_service.add_line(
                journal_entry_id=from_je.id,
                gl_account_id=cash_account,
                debit_fc=Decimal("0.00"),
                credit_fc=transfer.amount,
                currency=transfer.currency
            )
        
        # Post from entity entry with source_key
        from_source_key = f"IC_TRANSFER:POST:{transfer_id}:FROM"
        await self.je_service.post_entry(
            from_je.id, 
            posted_by, 
            require_dimensions=False,
            source_key=from_source_key
        )
        
        # To entity: Dr Cash/Bank, Cr Intercompany Receivable
        to_je = await self.je_service.create_draft_entry(
            book_id=to_book.id,
            entry_date=transfer.transfer_date,
            description=f"Intercompany transfer from {from_entity.code}: {transfer.description or transfer.reference_number}",
            reference_number=transfer.reference_number,
            source_service="intercompany",
            source_type="intercompany_transfer",
            source_id=transfer.id,
            idempotency_key=f"interco_transfer_{transfer.id}_to"
        )
        
        if transfer.to_bank_account_id:
            cash_account = await self._get_account_mapping(
                transfer.to_entity_id,
                to_book.id,
                "CASH_BANK"
            )
            await self.je_service.add_line(
                journal_entry_id=to_je.id,
                gl_account_id=cash_account,
                debit_fc=transfer.amount,
                credit_fc=Decimal("0.00"),
                currency=transfer.currency
            )
        
        await self.je_service.add_line(
            journal_entry_id=to_je.id,
            gl_account_id=to_interco_account,
            debit_fc=Decimal("0.00"),
            credit_fc=transfer.amount,
            currency=transfer.currency
        )
        
        # Post to entity entry with source_key
        to_source_key = f"IC_TRANSFER:POST:{transfer_id}:TO"
        await self.je_service.post_entry(
            to_je.id, 
            posted_by, 
            require_dimensions=False,
            source_key=to_source_key
        )
        
        # Update transfer with journal entry IDs
        await self.transfer_repo.update(
            transfer_id,
            from_entity_je_id=from_je.id,
            to_entity_je_id=to_je.id
        )
        
        await self.session.commit()
        return from_je.id, to_je.id
    
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
