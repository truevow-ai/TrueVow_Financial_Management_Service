"""
Reconciliation Matching Suggestion Service
Provides intelligent matching suggestions for bank transactions to journal entries
"""
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal
from difflib import SequenceMatcher

from app.modules.treasury.repositories.bank_transaction_repository import BankTransactionRepository
from app.modules.general_ledger.repositories.journal_entry_repository import JournalEntryRepository
from app.modules.general_ledger.repositories.reconciliation_repository import ReconciliationMatchRepository
from app.modules.treasury.models.bank_transaction_model import BankTransaction
from app.modules.general_ledger.models.journal_entry_model import JournalEntry
from app.core.logging import logger


class MatchSuggestion:
    """Represents a matching suggestion with confidence score"""
    
    def __init__(
        self,
        journal_entry_id: UUID,
        journal_entry_number: str,
        entry_date: date,
        total_amount: Decimal,
        memo: Optional[str],
        reference: Optional[str],
        confidence: float,
        match_reasons: List[str]
    ):
        self.journal_entry_id = journal_entry_id
        self.journal_entry_number = journal_entry_number
        self.entry_date = entry_date
        self.total_amount = total_amount
        self.memo = memo
        self.reference = reference
        self.confidence = confidence
        self.match_reasons = match_reasons


class ReconciliationMatchingService:
    """Service for suggesting matches between bank transactions and journal entries"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction_repo = BankTransactionRepository(session)
        self.je_repo = JournalEntryRepository(session)
        self.match_repo = ReconciliationMatchRepository(session)
    
    async def suggest_matches(
        self,
        bank_transaction_id: UUID,
        reconciliation_session_id: UUID,
        max_suggestions: int = 5,
        date_tolerance_days: int = 7,
        amount_tolerance_percent: float = 0.01  # 1% tolerance
    ) -> List[MatchSuggestion]:
        """
        Suggest journal entry matches for a bank transaction.
        
        Matching criteria (weighted):
        1. Exact amount match (40% weight)
        2. Date proximity (25% weight)
        3. Description/text similarity (20% weight)
        4. Reference number match (15% weight)
        """
        # Get bank transaction
        transaction = await self.transaction_repo.get_by_id(bank_transaction_id)
        if not transaction:
            raise ValueError(f"Bank transaction {bank_transaction_id} not found")
        
        # Get reconciliation session to determine period and account
        from app.modules.general_ledger.repositories.reconciliation_repository import ReconciliationSessionRepository
        session_repo = ReconciliationSessionRepository(self.session)
        session = await session_repo.get_by_id(reconciliation_session_id)
        if not session:
            raise ValueError(f"Reconciliation session {reconciliation_session_id} not found")
        
        # Get already matched journal entries to exclude
        existing_matches = await self.match_repo.list_by_session(reconciliation_session_id)
        excluded_je_ids = {match.journal_entry_id for match in existing_matches if match.journal_entry_id}
        
        # Get book_id from bank account
        from app.modules.treasury.repositories.bank_account_repository import BankAccountRepository
        account_repo = BankAccountRepository(self.session)
        account = await account_repo.get_by_id(session.bank_account_id)
        if not account:
            raise ValueError(f"Bank account {session.bank_account_id} not found")
        
        # Find potential journal entries
        # Search in date range: transaction date ± tolerance
        search_start = transaction.transaction_date - timedelta(days=date_tolerance_days)
        search_end = transaction.transaction_date + timedelta(days=date_tolerance_days)
        
        # Query journal entries in date range, same book, not already matched
        from app.modules.general_ledger.models.journal_entry_model import JournalEntryStatus
        stmt = select(JournalEntry).where(
            and_(
                JournalEntry.book_id == account.book_id,
                JournalEntry.entry_date >= search_start,
                JournalEntry.entry_date <= search_end,
                JournalEntry.status == JournalEntryStatus.POSTED,  # Only match posted entries
                ~JournalEntry.id.in_(excluded_je_ids) if excluded_je_ids else True
            )
        )
        
        result = await self.session.execute(stmt)
        candidate_jes = result.scalars().all()
        
        # Score each candidate
        suggestions = []
        for je in candidate_jes:
            # Calculate total amount of journal entry (sum of all line amounts)
            from app.modules.general_ledger.repositories.journal_line_repository import JournalLineRepository
            line_repo = JournalLineRepository(self.session)
            lines = await line_repo.list_by_entry(je.id)
            
            # Calculate net amount (debits - credits) using functional currency
            total_debits = sum(line.debit_fc for line in lines if line.debit_fc)
            total_credits = sum(line.credit_fc for line in lines if line.credit_fc)
            je_total_amount = total_debits - total_credits  # Net amount
            
            # Score the match
            confidence, reasons = self._score_match(
                transaction=transaction,
                journal_entry=je,
                je_total_amount=je_total_amount,
                date_tolerance_days=date_tolerance_days,
                amount_tolerance_percent=amount_tolerance_percent
            )
            
            if confidence > 0.3:  # Only include suggestions with >30% confidence
                suggestions.append(MatchSuggestion(
                    journal_entry_id=je.id,
                    journal_entry_number=je.entry_number or str(je.id),
                    entry_date=je.entry_date,
                    total_amount=je_total_amount,
                    memo=je.description,  # Use description field instead of memo
                    reference=je.reference_number,
                    confidence=confidence,
                    match_reasons=reasons
                ))
        
        # Sort by confidence descending and return top N
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        return suggestions[:max_suggestions]
    
    def _score_match(
        self,
        transaction: BankTransaction,
        journal_entry: JournalEntry,
        je_total_amount: Decimal,
        date_tolerance_days: int,
        amount_tolerance_percent: float
    ) -> Tuple[float, List[str]]:
        """
        Score a potential match between transaction and journal entry.
        Returns (confidence_score, list_of_reasons)
        """
        confidence = 0.0
        reasons = []
        
        # 1. Amount match (40% weight)
        tx_amount = abs(transaction.amount)  # Use absolute value
        je_amount = abs(je_total_amount)
        
        if tx_amount == je_amount:
            confidence += 0.40
            reasons.append("Exact amount match")
        else:
            # Check if within tolerance
            tolerance = tx_amount * Decimal(str(amount_tolerance_percent))
            if abs(tx_amount - je_amount) <= tolerance:
                confidence += 0.30
                reasons.append(f"Amount within {amount_tolerance_percent*100}% tolerance")
            elif abs(tx_amount - je_amount) <= tx_amount * Decimal("0.05"):  # Within 5%
                confidence += 0.15
                reasons.append("Amount within 5% tolerance")
        
        # 2. Date proximity (25% weight)
        date_diff = abs((transaction.transaction_date - journal_entry.entry_date).days)
        if date_diff == 0:
            confidence += 0.25
            reasons.append("Same date")
        elif date_diff <= 1:
            confidence += 0.20
            reasons.append("Date within 1 day")
        elif date_diff <= date_tolerance_days:
            # Linear decay: 0.15 at tolerance boundary, 0.05 at 0 days
            date_score = 0.15 * (1 - (date_diff / date_tolerance_days))
            confidence += date_score
            reasons.append(f"Date within {date_diff} days")
        
        # 3. Description/text similarity (20% weight)
        tx_desc = (transaction.description or "").lower().strip()
        je_memo = (journal_entry.description or "").lower().strip()  # JournalEntry uses 'description' not 'memo'
        je_ref = (journal_entry.reference_number or "").lower().strip()
        
        if tx_desc and (je_memo or je_ref):
            # Check exact match
            if tx_desc in je_memo or tx_desc in je_ref:
                confidence += 0.20
                reasons.append("Description text match")
            else:
                # Use sequence matcher for similarity
                if je_memo:
                    similarity = SequenceMatcher(None, tx_desc, je_memo).ratio()
                    if similarity > 0.8:
                        confidence += 0.15
                        reasons.append(f"Description {similarity*100:.0f}% similar")
                    elif similarity > 0.5:
                        confidence += 0.08
                        reasons.append(f"Description {similarity*100:.0f}% similar")
        
        # 4. Reference number match (15% weight)
        tx_ref = (transaction.reference_number or "").strip()
        if tx_ref and je_ref and tx_ref.lower() == je_ref.lower():
            confidence += 0.15
            reasons.append("Reference number match")
        
        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)
        
        return confidence, reasons
    
    async def get_suggestions_for_session(
        self,
        reconciliation_session_id: UUID,
        max_per_transaction: int = 3
    ) -> dict[UUID, List[MatchSuggestion]]:
        """
        Get suggestions for all unmatched transactions in a reconciliation session.
        Returns dict mapping transaction_id -> list of suggestions
        """
        # Get session
        from app.modules.general_ledger.repositories.reconciliation_repository import ReconciliationSessionRepository
        session_repo = ReconciliationSessionRepository(self.session)
        session = await session_repo.get_by_id(reconciliation_session_id)
        if not session:
            raise ValueError(f"Reconciliation session {reconciliation_session_id} not found")
        
        # Get all transactions in period
        transactions = await self.transaction_repo.list_by_account(
            bank_account_id=session.bank_account_id,
            start_date=session.period_start,
            end_date=session.period_end
        )
        
        # Get already matched transactions
        existing_matches = await self.match_repo.list_by_session(reconciliation_session_id)
        matched_tx_ids = {match.bank_transaction_id for match in existing_matches if match.bank_transaction_id}
        
        # Get suggestions for each unmatched transaction
        all_suggestions = {}
        for tx in transactions:
            if tx.id not in matched_tx_ids:
                suggestions = await self.suggest_matches(
                    bank_transaction_id=tx.id,
                    reconciliation_session_id=reconciliation_session_id,
                    max_suggestions=max_per_transaction
                )
                if suggestions:
                    all_suggestions[tx.id] = suggestions
        
        return all_suggestions
