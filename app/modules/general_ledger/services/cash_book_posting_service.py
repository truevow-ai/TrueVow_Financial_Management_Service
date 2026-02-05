"""Cash Book Posting Service - Posts Treasury movements to CASH book"""
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.modules.general_ledger.services.journal_entry_service import JournalEntryService
from app.modules.general_ledger.services.treasury_sync_service import TreasurySyncService
from app.modules.general_ledger.repositories.gl_account_repository import GLAccountMappingRepository
from app.modules.general_ledger.repositories.book_repository import BookRepository
from app.modules.general_ledger.models.book_model import BookType
from app.modules.treasury.repositories.bank_account_repository import BankAccountRepository
from app.modules.treasury.models.bank_transaction_model import BankTransaction, TransactionType
from app.modules.treasury.models.settlement_model import Settlement
from app.modules.treasury.models.fx_conversion_model import FXConversion
from app.modules.treasury.models.transfer_model import Transfer
from app.core.exceptions import NotFoundError, ValidationError


class CashBookPostingService:
    """Service for posting Treasury movements to CASH book"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.je_service = JournalEntryService(session)
        self.sync_service = TreasurySyncService(session)
        self.mapping_repo = GLAccountMappingRepository(session)
        self.book_repo = BookRepository(session)
        self.account_repo = BankAccountRepository(session)
    
    async def post_bank_transaction(
        self,
        entity_id: UUID,
        bank_transaction: BankTransaction,
        posted_by: UUID,
        source_key: Optional[str] = None
    ) -> UUID:
        """Post a bank transaction to CASH book"""
        # Get CASH book for entity
        cash_book = await self.book_repo.get_by_entity_and_type(entity_id, BookType.CASH)
        if not cash_book:
            raise NotFoundError(f"CASH book not found for entity {entity_id}")
        
        # Get period for transaction date
        from app.modules.general_ledger.repositories.accounting_period_repository import AccountingPeriodRepository
        period_repo = AccountingPeriodRepository(self.session)
        period = await period_repo.get_by_book_and_date(cash_book.id, bank_transaction.transaction_date)
        if not period:
            raise NotFoundError(f"No period found for date {bank_transaction.transaction_date}")
        
        # Determine posting based on transaction type
        if bank_transaction.transaction_type == TransactionType.DEPOSIT:
            return await self._post_deposit(cash_book, period, bank_transaction, posted_by, source_key)
        elif bank_transaction.transaction_type == TransactionType.WITHDRAWAL:
            return await self._post_withdrawal(cash_book, period, bank_transaction, posted_by, source_key)
        elif bank_transaction.transaction_type == TransactionType.FEE:
            return await self._post_fee(cash_book, period, bank_transaction, posted_by, source_key)
        else:
            # Default: post as cash movement
            return await self._post_cash_movement(cash_book, period, bank_transaction, posted_by, source_key)
    
    async def _post_deposit(
        self,
        book,
        period,
        transaction: BankTransaction,
        posted_by: UUID,
        source_key: Optional[str] = None
    ) -> UUID:
        """Post deposit transaction"""
        # Get account mappings
        bank_account = await self._get_bank_account_mapping(book.legal_entity_id, book.id, "CASH_BANK")
        revenue_account = await self._get_bank_account_mapping(book.legal_entity_id, book.id, "REV_CASH")
        
        # Create journal entry
        entry = await self.je_service.create_draft_entry(
            book_id=book.id,
            entry_date=transaction.transaction_date,
            description=f"Bank deposit: {transaction.description or transaction.reference_number}",
            reference_number=transaction.reference_number,
            source_service="treasury",
            source_type="bank_deposit",
            source_id=transaction.id,
            idempotency_key=f"treasury_tx_{transaction.id}"
        )
        
        # Add lines: Dr Bank Cash, Cr Cash Revenue
        await self.je_service.add_line(
            journal_entry_id=entry.id,
            gl_account_id=bank_account,
            debit_fc=abs(transaction.amount),
            credit_fc=Decimal("0.00"),
            currency=transaction.currency
        )
        
        await self.je_service.add_line(
            journal_entry_id=entry.id,
            gl_account_id=revenue_account,
            debit_fc=Decimal("0.00"),
            credit_fc=abs(transaction.amount),
            currency=transaction.currency
        )
        
        # Post entry with source_key
        await self.je_service.post_entry(entry.id, posted_by, require_dimensions=False, source_key=source_key)
        return entry.id
    
    async def _post_withdrawal(
        self,
        book,
        period,
        transaction: BankTransaction,
        posted_by: UUID,
        source_key: Optional[str] = None
    ) -> UUID:
        """Post withdrawal transaction"""
        bank_account = await self._get_bank_account_mapping(book.legal_entity_id, book.id, "CASH_BANK")
        expense_account = await self._get_bank_account_mapping(book.legal_entity_id, book.id, "EXP_CASH")
        
        entry = await self.je_service.create_draft_entry(
            book_id=book.id,
            entry_date=transaction.transaction_date,
            description=f"Bank withdrawal: {transaction.description or transaction.reference_number}",
            reference_number=transaction.reference_number,
            source_service="treasury",
            source_type="bank_withdrawal",
            source_id=transaction.id,
            idempotency_key=f"treasury_tx_{transaction.id}"
        )
        
        # Add lines: Dr Expense, Cr Bank Cash
        await self.je_service.add_line(
            journal_entry_id=entry.id,
            gl_account_id=expense_account,
            debit_fc=abs(transaction.amount),
            credit_fc=Decimal("0.00"),
            currency=transaction.currency
        )
        
        await self.je_service.add_line(
            journal_entry_id=entry.id,
            gl_account_id=bank_account,
            debit_fc=Decimal("0.00"),
            credit_fc=abs(transaction.amount),
            currency=transaction.currency
        )
        
        await self.je_service.post_entry(entry.id, posted_by, require_dimensions=False, source_key=source_key)
        return entry.id
    
    async def _post_fee(
        self,
        book,
        period,
        transaction: BankTransaction,
        posted_by: UUID
    ) -> UUID:
        """Post fee transaction"""
        bank_account = await self._get_bank_account_mapping(book.legal_entity_id, book.id, "CASH_BANK")
        fee_account = await self._get_bank_account_mapping(book.legal_entity_id, book.id, "EXP_PROCESSING_FEES")
        
        entry = await self.je_service.create_draft_entry(
            book_id=book.id,
            entry_date=transaction.transaction_date,
            description=f"Processing fee: {transaction.description}",
            reference_number=transaction.reference_number,
            source_service="treasury",
            source_type="processing_fee",
            source_id=transaction.id,
            idempotency_key=f"treasury_tx_{transaction.id}"
        )
        
        # Add lines: Dr Processing Fee Expense, Cr Bank Cash
        await self.je_service.add_line(
            journal_entry_id=entry.id,
            gl_account_id=fee_account,
            debit_fc=abs(transaction.amount),
            credit_fc=Decimal("0.00"),
            currency=transaction.currency
        )
        
        await self.je_service.add_line(
            journal_entry_id=entry.id,
            gl_account_id=bank_account,
            debit_fc=Decimal("0.00"),
            credit_fc=abs(transaction.amount),
            currency=transaction.currency
        )
        
        await self.je_service.post_entry(entry.id, posted_by, require_dimensions=False, source_key=source_key)
        return entry.id
    
    async def _post_cash_movement(
        self,
        book,
        period,
        transaction: BankTransaction,
        posted_by: UUID,
        source_key: Optional[str] = None
    ) -> UUID:
        """Post generic cash movement"""
        bank_account = await self._get_bank_account_mapping(book.legal_entity_id, book.id, "CASH_BANK")
        
        entry = await self.je_service.create_draft_entry(
            book_id=book.id,
            entry_date=transaction.transaction_date,
            description=f"Cash movement: {transaction.description}",
            reference_number=transaction.reference_number,
            source_service="treasury",
            source_type="cash_movement",
            source_id=transaction.id,
            idempotency_key=f"treasury_tx_{transaction.id}"
        )
        
        # Simple cash movement (may need adjustment based on transaction type)
        if transaction.amount > 0:
            # Deposit
            await self.je_service.add_line(
                journal_entry_id=entry.id,
                gl_account_id=bank_account,
                debit_fc=transaction.amount,
                credit_fc=Decimal("0.00"),
                currency=transaction.currency
            )
            # Counter account would depend on context
        else:
            # Withdrawal
            await self.je_service.add_line(
                journal_entry_id=entry.id,
                gl_account_id=bank_account,
                debit_fc=Decimal("0.00"),
                credit_fc=abs(transaction.amount),
                currency=transaction.currency
            )
        
        await self.je_service.post_entry(entry.id, posted_by, require_dimensions=False, source_key=source_key)
        return entry.id
    
    async def _get_bank_account_mapping(
        self,
        entity_id: UUID,
        book_id: UUID,
        map_key: str
    ) -> UUID:
        """Get GL account from mapping"""
        mapping = await self.mapping_repo.get_mapping(entity_id, book_id, map_key)
        if not mapping:
            raise NotFoundError(f"Account mapping not found: {map_key} for entity {entity_id}, book {book_id}")
        return mapping.gl_account_id
    
    async def post_settlement(
        self,
        entity_id: UUID,
        settlement: Settlement,
        posted_by: UUID,
        source_key: Optional[str] = None
    ) -> UUID:
        """Post settlement to CASH book"""
        # Get CASH book
        cash_book = await self.book_repo.get_by_entity_and_type(entity_id, BookType.CASH)
        if not cash_book:
            raise NotFoundError(f"CASH book not found for entity {entity_id}")
        
        # Get period
        from app.modules.general_ledger.repositories.accounting_period_repository import AccountingPeriodRepository
        period_repo = AccountingPeriodRepository(self.session)
        period = await period_repo.get_by_book_and_date(cash_book.id, settlement.settlement_date)
        if not period:
            raise NotFoundError(f"No period found for date {settlement.settlement_date}")
        
        # Get account mappings
        bank_account = await self._get_bank_account_mapping(entity_id, cash_book.id, "CASH_BANK")
        revenue_account = await self._get_bank_account_mapping(entity_id, cash_book.id, "REV_CASH")
        fee_account = await self._get_bank_account_mapping(entity_id, cash_book.id, "EXP_PROCESSING_FEES")
        
        # Create entry for net settlement
        entry = await self.je_service.create_draft_entry(
            book_id=cash_book.id,
            entry_date=settlement.settlement_date,
            description=f"Settlement {settlement.source.value}: {settlement.description or settlement.external_settlement_id}",
            reference_number=settlement.external_settlement_id,
            source_service="treasury",
            source_type="settlement",
            source_id=settlement.id,
            idempotency_key=f"treasury_settlement_{settlement.id}"
        )
        
        # Dr Bank Cash (net amount)
        await self.je_service.add_line(
            journal_entry_id=entry.id,
            gl_account_id=bank_account,
            debit_fc=settlement.net_amount,
            credit_fc=Decimal("0.00"),
            currency=settlement.currency
        )
        
        # Cr Revenue (gross amount)
        await self.je_service.add_line(
            journal_entry_id=entry.id,
            gl_account_id=revenue_account,
            debit_fc=Decimal("0.00"),
            credit_fc=settlement.gross_amount,
            currency=settlement.currency
        )
        
        # Dr Processing Fee Expense (fees)
        if settlement.fees > 0:
            await self.je_service.add_line(
                journal_entry_id=entry.id,
                gl_account_id=fee_account,
                debit_fc=settlement.fees,
                credit_fc=Decimal("0.00"),
                currency=settlement.currency
            )
        
        # Generate source_key if not provided: SETTLEMENT:CREATE:{provider}:{external_settlement_id}
        # CRITICAL: external_settlement_id must be present for idempotency
        # If missing, this is a manual settlement and we use the settlement.id as fallback
        if not source_key:
            provider = settlement.source.value  # STRIPE, TELR, MANUAL
            # Prefer external_settlement_id, fallback to external_payout_id, then settlement.id
            # Note: For idempotency, external_settlement_id should always be present for provider settlements
            external_id = settlement.external_settlement_id or settlement.external_payout_id
            if not external_id:
                # Manual settlement without external ID - use internal ID
                # This is acceptable for manual entries but not for provider syncs
                external_id = str(settlement.id)
            source_key = f"SETTLEMENT:CREATE:{provider}:{external_id}"
        
        await self.je_service.post_entry(entry.id, posted_by, require_dimensions=False, source_key=source_key)
        return entry.id
