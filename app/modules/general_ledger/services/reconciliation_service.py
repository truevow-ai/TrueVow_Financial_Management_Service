"""Reconciliation Service"""
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.modules.general_ledger.repositories.reconciliation_repository import (
    ReconciliationSessionRepository,
    ReconciliationMatchRepository
)
from app.modules.treasury.repositories.bank_account_repository import BankAccountRepository
from app.modules.treasury.repositories.bank_transaction_repository import BankTransactionRepository
from app.modules.general_ledger.repositories.journal_entry_repository import JournalEntryRepository
from app.modules.general_ledger.models.reconciliation_model import (
    ReconciliationSession,
    ReconciliationMatch,
    ReconciliationStatus
)
from app.core.exceptions import NotFoundError, ValidationError


class ReconciliationService:
    """Service for bank reconciliation"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.session_repo = ReconciliationSessionRepository(session)
        self.match_repo = ReconciliationMatchRepository(session)
        self.account_repo = BankAccountRepository(session)
        self.transaction_repo = BankTransactionRepository(session)
        self.je_repo = JournalEntryRepository(session)
    
    async def create_session(
        self,
        bank_account_id: UUID,
        period_start: date,
        period_end: date,
        statement_ending_balance: Decimal,
        statement_currency: str
    ) -> ReconciliationSession:
        """Create a reconciliation session"""
        # Verify bank account exists
        account = await self.account_repo.get_by_id(bank_account_id)
        if not account:
            raise NotFoundError(f"Bank account {bank_account_id} not found")
        
        if account.currency != statement_currency:
            raise ValidationError(f"Statement currency {statement_currency} does not match account currency {account.currency}")
        
        session = await self.session_repo.create(
            bank_account_id=bank_account_id,
            period_start=period_start,
            period_end=period_end,
            statement_ending_balance=statement_ending_balance,
            statement_currency=statement_currency,
            status=ReconciliationStatus.DRAFT,
            difference=Decimal("0.00")
        )
        
        await self.session.commit()
        return session
    
    async def get_session(self, session_id: UUID) -> Optional[ReconciliationSession]:
        """Get reconciliation session by ID"""
        return await self.session_repo.get_by_id(session_id)
    
    async def list_sessions(
        self,
        bank_account_id: UUID,
        status: Optional[ReconciliationStatus] = None
    ) -> List[ReconciliationSession]:
        """List reconciliation sessions for an account"""
        return await self.session_repo.list_by_account(bank_account_id, status=status)
    
    async def match_transaction(
        self,
        session_id: UUID,
        bank_transaction_id: UUID,
        journal_entry_id: Optional[UUID] = None,
        match_type: str = "manual",
        notes: Optional[str] = None
    ) -> ReconciliationMatch:
        """Match a bank transaction to a journal entry"""
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise NotFoundError(f"Reconciliation session {session_id} not found")
        
        # Verify transaction exists and is in period
        transaction = await self.transaction_repo.get_by_id(bank_transaction_id)
        if not transaction:
            raise NotFoundError(f"Bank transaction {bank_transaction_id} not found")
        
        if transaction.bank_account_id != session.bank_account_id:
            raise ValidationError("Transaction must belong to the session's bank account")
        
        if not (session.period_start <= transaction.transaction_date <= session.period_end):
            raise ValidationError("Transaction date must be within reconciliation period")
        
        # Verify journal entry if provided
        if journal_entry_id:
            je = await self.je_repo.get_by_id(journal_entry_id)
            if not je:
                raise NotFoundError(f"Journal entry {journal_entry_id} not found")
        
        # Check if already matched
        existing = await self.match_repo.get_by_transaction(session_id, bank_transaction_id)
        if existing:
            raise ValidationError("Transaction already matched")
        
        # Create match
        match = await self.match_repo.create(
            reconciliation_session_id=session_id,
            bank_transaction_id=bank_transaction_id,
            journal_entry_id=journal_entry_id,
            match_type=match_type,
            match_confidence=100.0 if match_type == "manual" else None,
            notes=notes
        )
        
        # Mark transaction as reconciled
        await self.transaction_repo.update(
            bank_transaction_id,
            is_reconciled=True,
            reconciliation_id=session_id
        )
        
        await self.session.commit()
        return match
    
    async def calculate_difference(self, session_id: UUID) -> Decimal:
        """Calculate reconciliation difference"""
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise NotFoundError(f"Reconciliation session {session_id} not found")
        
        # Get all transactions in period
        transactions = await self.transaction_repo.list_by_account(
            bank_account_id=session.bank_account_id,
            start_date=session.period_start,
            end_date=session.period_end
        )
        
        # Calculate book balance (sum of all transactions)
        book_balance = sum(tx.amount for tx in transactions)
        
        # Difference = statement balance - book balance
        difference = session.statement_ending_balance - book_balance
        
        # Update session
        await self.session_repo.update(session_id, difference=difference)
        await self.session.commit()
        
        return difference
    
    async def close_session(
        self,
        session_id: UUID,
        reconciled_by: UUID,
        notes: Optional[str] = None,
        allow_non_zero: bool = False
    ) -> ReconciliationSession:
        """Close a reconciliation session"""
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise NotFoundError(f"Reconciliation session {session_id} not found")
        
        # Calculate difference
        difference = await self.calculate_difference(session_id)
        
        # Check if difference is zero (or allow override)
        if abs(difference) > Decimal("0.01") and not allow_non_zero:
            raise ValidationError(
                f"Cannot close reconciliation with non-zero difference: {difference}. "
                "Set allow_non_zero=True to override."
            )
        
        # Update session
        await self.session_repo.update(
            session_id,
            status=ReconciliationStatus.CLOSED,
            reconciled_by=reconciled_by,
            reconciled_at=date.today(),
            notes=notes
        )
        
        await self.session.commit()
        return await self.session_repo.get_by_id(session_id)
