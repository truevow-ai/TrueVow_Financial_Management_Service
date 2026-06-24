"""Enhanced Reconciliation Service with Auto-Matching"""
from typing import List, Optional, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal
from app.modules.general_ledger.services.reconciliation_service import ReconciliationService
from app.modules.general_ledger.repositories.journal_entry_repository import (
    JournalEntryRepository,
    JournalLineRepository,
)
from app.modules.treasury.repositories.bank_transaction_repository import BankTransactionRepository
from app.modules.general_ledger.models.reconciliation_model import ReconciliationMatch
from app.modules.general_ledger.models.journal_entry_model import JournalEntryStatus
from app.core.exceptions import NotFoundError, ValidationError


class EnhancedReconciliationService(ReconciliationService):
    """Enhanced reconciliation service with auto-matching and adjustments"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session)
        self.je_repo = JournalEntryRepository(session)
        self.je_line_repo = JournalLineRepository(session)
    
    async def auto_match_transactions(
        self,
        session_id: UUID,
        match_tolerance_days: int = 3,
        match_tolerance_amount: Decimal = Decimal("0.01"),
        min_confidence: float = 80.0
    ) -> Dict:
        """Auto-match bank transactions to journal entries
        
        Args:
            session_id: Reconciliation session ID
            match_tolerance_days: Days tolerance for date matching
            match_tolerance_amount: Amount tolerance for matching
            min_confidence: Minimum confidence score to auto-match
        
        Returns:
            Dict with match results
        """
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise NotFoundError(f"Reconciliation session {session_id} not found")
        
        # Get unmatched transactions
        transactions = await self.transaction_repo.list_by_account(
            bank_account_id=session.bank_account_id,
            start_date=session.period_start,
            end_date=session.period_end
        )
        
        unmatched = [tx for tx in transactions if not tx.is_reconciled]
        
        # Get potential journal entries (CASH book, same period)
        from app.modules.general_ledger.repositories.book_repository import BookRepository
        from app.modules.general_ledger.models.book_model import BookType
        from app.modules.general_ledger.repositories.accounting_period_repository import AccountingPeriodRepository
        
        book_repo = BookRepository(self.session)
        period_repo = AccountingPeriodRepository(self.session)
        
        # Get CASH book for entity
        account = await self.account_repo.get_by_id(session.bank_account_id)
        cash_book = await book_repo.get_by_entity_and_type(account.legal_entity_id, BookType.CASH)
        
        if not cash_book:
            return {
                "matched": 0,
                "suggestions": [],
                "errors": ["CASH book not found"]
            }
        
        # Get period
        period = await period_repo.get_by_book_and_date(cash_book.id, session.period_end)
        if not period:
            return {
                "matched": 0,
                "suggestions": [],
                "errors": ["Period not found"]
            }
        
        # Get journal entries for period
        journal_entries = await self.je_repo.list_by_book_and_period(
            book_id=cash_book.id,
            period_id=period.id,
            status=JournalEntryStatus.POSTED
        )
        
        # Get journal lines for cash account
        from app.modules.general_ledger.repositories.gl_account_repository import GLAccountMappingRepository
        mapping_repo = GLAccountMappingRepository(self.session)
        
        cash_account_mapping = await mapping_repo.get_mapping(
            account.legal_entity_id,
            cash_book.id,
            "CASH_BANK"
        )
        
        if not cash_account_mapping:
            return {
                "matched": 0,
                "suggestions": [],
                "errors": ["CASH_BANK account mapping not found"]
            }
        
        # Get all journal lines for cash account
        je_lines = []
        for je in journal_entries:
            lines = await self.je_line_repo.list_by_journal_entry(je.id)
            cash_lines = [
                line for line in lines
                if line.gl_account_id == cash_account_mapping.gl_account_id
            ]
            je_lines.extend(cash_lines)
        
        # Match transactions
        matched_count = 0
        suggestions = []
        
        for transaction in unmatched:
            best_match = await self._find_best_match(
                transaction,
                je_lines,
                match_tolerance_days,
                match_tolerance_amount
            )
            
            if best_match and best_match["confidence"] >= min_confidence:
                # Auto-match
                try:
                    await self.match_transaction(
                        session_id=session_id,
                        bank_transaction_id=transaction.id,
                        journal_entry_id=best_match["journal_entry_id"],
                        match_type="auto",
                        notes=f"Auto-matched with confidence {best_match['confidence']:.1f}%"
                    )
                    matched_count += 1
                except Exception as e:
                    suggestions.append({
                        "transaction_id": str(transaction.id),
                        "suggestion": best_match,
                        "error": str(e)
                    })
            elif best_match:
                # Suggest match
                suggestions.append({
                    "transaction_id": str(transaction.id),
                    "suggestion": best_match,
                    "action": "review"
                })
        
        return {
            "matched": matched_count,
            "suggestions": suggestions,
            "unmatched": len(unmatched) - matched_count
        }
    
    async def _find_best_match(
        self,
        transaction,
        je_lines: List,
        tolerance_days: int,
        tolerance_amount: Decimal
    ) -> Optional[Dict]:
        """Find best matching journal line for transaction"""
        best_match = None
        best_confidence = 0.0
        
        for line in je_lines:
            je = line.journal_entry
            
            # Calculate confidence score
            confidence = 0.0
            
            # Amount match (40% weight)
            line_amount = (line.debit_fc or Decimal("0.00")) - (line.credit_fc or Decimal("0.00"))
            if transaction.transaction_type in ["WITHDRAWAL", "DEBIT", "FEE"]:
                line_amount = -line_amount  # Reverse for debits
            
            amount_diff = abs(transaction.amount - line_amount)
            if amount_diff <= tolerance_amount:
                confidence += 40.0
            elif amount_diff <= tolerance_amount * 10:
                confidence += 20.0 * (1 - amount_diff / (tolerance_amount * 10))
            
            # Date match (30% weight)
            date_diff = abs((transaction.transaction_date - je.entry_date).days)
            if date_diff == 0:
                confidence += 30.0
            elif date_diff <= tolerance_days:
                confidence += 30.0 * (1 - date_diff / tolerance_days)
            
            # Reference match (30% weight)
            if transaction.reference_number and je.reference_number:
                if transaction.reference_number.lower() == je.reference_number.lower():
                    confidence += 30.0
                elif transaction.reference_number.lower() in je.reference_number.lower():
                    confidence += 15.0
            
            if confidence > best_confidence:
                best_confidence = confidence
                best_match = {
                    "journal_entry_id": je.id,
                    "journal_line_id": line.id,
                    "confidence": confidence,
                    "amount_match": float(amount_diff),
                    "date_match_days": date_diff,
                    "reference_match": bool(
                        transaction.reference_number and
                        je.reference_number and
                        transaction.reference_number.lower() == je.reference_number.lower()
                    )
                }
        
        return best_match
    
    async def create_adjustment_entry(
        self,
        session_id: UUID,
        adjustment_amount: Decimal,
        adjustment_type: str,  # "BANK_ERROR", "BOOK_ERROR", "TIMING_DIFF"
        description: str,
        gl_account_id: UUID,
        posted_by: UUID
    ) -> UUID:
        """Create adjustment journal entry for reconciliation difference
        
        Args:
            session_id: Reconciliation session ID
            adjustment_amount: Adjustment amount (positive = increase book, negative = decrease)
            adjustment_type: Type of adjustment
            description: Description of adjustment
            gl_account_id: GL account to post adjustment to
            posted_by: User ID posting the adjustment
        """
        session = await self.session_repo.get_by_id(session_id)
        if not session:
            raise NotFoundError(f"Reconciliation session {session_id} not found")
        
        # Get CASH book
        account = await self.account_repo.get_by_id(session.bank_account_id)
        from app.modules.general_ledger.repositories.book_repository import BookRepository
        from app.modules.general_ledger.models.book_model import BookType
        from app.modules.general_ledger.repositories.accounting_period_repository import AccountingPeriodRepository
        
        book_repo = BookRepository(self.session)
        period_repo = AccountingPeriodRepository(self.session)
        
        cash_book = await book_repo.get_by_entity_and_type(account.legal_entity_id, BookType.CASH)
        if not cash_book:
            raise NotFoundError("CASH book not found")
        
        period = await period_repo.get_by_book_and_date(cash_book.id, session.period_end)
        if not period:
            raise NotFoundError("Period not found")
        
        # Get cash account
        from app.modules.general_ledger.repositories.gl_account_repository import GLAccountMappingRepository
        mapping_repo = GLAccountMappingRepository(self.session)
        cash_account_mapping = await mapping_repo.get_mapping(
            account.legal_entity_id,
            cash_book.id,
            "CASH_BANK"
        )
        if not cash_account_mapping:
            raise NotFoundError("CASH_BANK account mapping not found")
        
        # Create adjustment journal entry
        from app.modules.general_ledger.services.ledger_poster import get_ledger_poster
        je_service = get_ledger_poster(self.session)
        
        entry = await je_service.create_draft_entry(
            book_id=cash_book.id,
            entry_date=session.period_end,
            description=f"Reconciliation adjustment: {description}",
            reference_number=f"RECON-ADJ-{session.id}",
            source_service="reconciliation",
            source_type="reconciliation_adjustment",
            source_id=session.id,
            idempotency_key=f"recon_adj_{session.id}"
        )
        
        # Post adjustment: Dr/Cr cash, Cr/Dr adjustment account
        if adjustment_amount > 0:
            # Increase book balance (Dr cash, Cr adjustment)
            await je_service.add_line(
                journal_entry_id=entry.id,
                gl_account_id=cash_account_mapping.gl_account_id,
                debit_fc=adjustment_amount,
                credit_fc=Decimal("0.00"),
                currency=session.statement_currency
            )
            await je_service.add_line(
                journal_entry_id=entry.id,
                gl_account_id=gl_account_id,
                debit_fc=Decimal("0.00"),
                credit_fc=adjustment_amount,
                currency=session.statement_currency
            )
        else:
            # Decrease book balance (Cr cash, Dr adjustment)
            await je_service.add_line(
                journal_entry_id=entry.id,
                gl_account_id=cash_account_mapping.gl_account_id,
                debit_fc=Decimal("0.00"),
                credit_fc=abs(adjustment_amount),
                currency=session.statement_currency
            )
            await je_service.add_line(
                journal_entry_id=entry.id,
                gl_account_id=gl_account_id,
                debit_fc=abs(adjustment_amount),
                credit_fc=Decimal("0.00"),
                currency=session.statement_currency
            )
        
        # Post entry
        await je_service.post_entry(entry.id, posted_by, require_dimensions=False)
        
        # Update session notes
        notes = f"{session.notes or ''}\nAdjustment: {description} ({adjustment_amount})".strip()
        await self.session_repo.update(session_id, notes=notes)
        
        await self.session.commit()
        return entry.id
