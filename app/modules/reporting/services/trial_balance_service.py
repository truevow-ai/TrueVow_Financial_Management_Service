"""Trial Balance Report Service"""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.modules.general_ledger.repositories.gl_account_repository import GLAccountRepository
from app.modules.general_ledger.repositories.journal_entry_repository import JournalEntryRepository
from app.modules.general_ledger.repositories.accounting_period_repository import AccountingPeriodRepository
from app.modules.general_ledger.repositories.book_repository import BookRepository
from app.modules.general_ledger.models.journal_entry_model import JournalEntryStatus


class TrialBalanceService:
    """Service for generating Trial Balance reports"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.gl_account_repo = GLAccountRepository(session)
        self.je_repo = JournalEntryRepository(session)
        self.period_repo = AccountingPeriodRepository(session)
        self.book_repo = BookRepository(session)
    
    async def generate_trial_balance(
        self,
        book_id: UUID,
        period_id: Optional[UUID] = None,
        as_of_date: Optional[date] = None,
        include_zero_balance: bool = False
    ) -> Dict:
        """Generate Trial Balance report
        
        Args:
            book_id: Book ID
            period_id: Optional period ID (if not provided, uses as_of_date)
            as_of_date: Optional date (if period_id not provided)
            include_zero_balance: Include accounts with zero balance
        """
        # Get book
        book = await self.book_repo.get_by_id(book_id)
        if not book:
            raise ValueError(f"Book {book_id} not found")
        
        # Get period
        if period_id:
            period = await self.period_repo.get_by_id(period_id)
        elif as_of_date:
            period = await self.period_repo.get_by_book_and_date(book_id, as_of_date)
        else:
            raise ValueError("Either period_id or as_of_date must be provided")
        
        if not period:
            raise ValueError(f"Period not found for book {book_id}")
        
        # Get all accounts for the book
        accounts = await self.gl_account_repo.list_by_book(book_id)
        
        # Get all posted journal entries for the period
        from app.modules.general_ledger.models.journal_entry_model import JournalEntry
        from app.modules.general_ledger.models.journal_line_model import JournalLine
        
        query = select(JournalLine).join(JournalEntry).where(
            JournalEntry.book_id == book_id,
            JournalEntry.period_id == period.id,
            JournalEntry.status == JournalEntryStatus.POSTED
        )
        
        result = await self.session.execute(query)
        lines = list(result.scalars().all())
        
        # Calculate balances per account
        account_balances: Dict[UUID, Dict[str, Decimal]] = {}
        
        for line in lines:
            account_id = line.gl_account_id
            if account_id not in account_balances:
                account_balances[account_id] = {
                    "debit": Decimal("0.00"),
                    "credit": Decimal("0.00")
                }
            
            account_balances[account_id]["debit"] += line.debit_fc or Decimal("0.00")
            account_balances[account_id]["credit"] += line.credit_fc or Decimal("0.00")
        
        # Build report rows
        report_rows = []
        total_debit = Decimal("0.00")
        total_credit = Decimal("0.00")
        
        for account in accounts:
            balance = account_balances.get(account.id, {"debit": Decimal("0.00"), "credit": Decimal("0.00")})
            debit = balance["debit"]
            credit = balance["credit"]
            net_balance = debit - credit
            
            # Skip zero balance if requested
            if not include_zero_balance and debit == Decimal("0.00") and credit == Decimal("0.00"):
                continue
            
            report_rows.append({
                "account_code": account.account_code,
                "account_name": account.account_name,
                "account_type": account.account_type.value if account.account_type else None,
                "debit": float(debit),
                "credit": float(credit),
                "net_balance": float(net_balance)
            })
            
            total_debit += debit
            total_credit += credit
        
        # Sort by account code
        report_rows.sort(key=lambda x: x["account_code"])
        
        return {
            "book_id": str(book_id),
            "book_name": book.book_name,
            "period_id": str(period.id),
            "period_start": period.period_start.isoformat(),
            "period_end": period.period_end.isoformat(),
            "as_of_date": period.period_end.isoformat(),
            "currency": book.functional_currency,
            "total_debit": float(total_debit),
            "total_credit": float(total_credit),
            "is_balanced": abs(total_debit - total_credit) < Decimal("0.01"),
            "accounts": report_rows
        }
