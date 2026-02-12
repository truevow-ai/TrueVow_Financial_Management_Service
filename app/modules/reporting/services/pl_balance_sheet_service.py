"""Profit & Loss and Balance Sheet Report Services"""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from uuid import UUID
from datetime import date, timedelta
from decimal import Decimal
from app.modules.general_ledger.repositories.gl_account_repository import GLAccountRepository
from app.modules.general_ledger.repositories.accounting_period_repository import AccountingPeriodRepository
from app.modules.general_ledger.repositories.book_repository import BookRepository
from app.modules.general_ledger.models.gl_account_model import AccountType
from app.modules.general_ledger.models.journal_entry_model import JournalEntryStatus


class PLBalanceSheetService:
    """Service for generating P&L and Balance Sheet reports"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.gl_account_repo = GLAccountRepository(session)
        self.period_repo = AccountingPeriodRepository(session)
        self.book_repo = BookRepository(session)
    
    async def generate_profit_loss(
        self,
        book_id: UUID,
        period_start: date,
        period_end: date,
        compare_previous: bool = False
    ) -> Dict:
        """Generate Profit & Loss (Income Statement) report
        
        Args:
            book_id: Book ID
            period_start: Report period start date
            period_end: Report period end date
            compare_previous: Include previous period comparison
        """
        book = await self.book_repo.get_by_id(book_id)
        if not book:
            raise ValueError(f"Book {book_id} not found")
        
        # Get periods
        start_period = await self.period_repo.get_by_book_and_date(book_id, period_start)
        end_period = await self.period_repo.get_by_book_and_date(book_id, period_end)
        
        if not start_period or not end_period:
            raise ValueError("Periods not found for date range")
        
        # Get revenue and expense accounts
        revenue_accounts = await self.gl_account_repo.list_by_type(book_id, AccountType.REVENUE)
        expense_accounts = await self.gl_account_repo.list_by_type(book_id, AccountType.EXPENSE)
        cogs_accounts = await self.gl_account_repo.list_by_type(book_id, AccountType.COST_OF_GOODS_SOLD)
        
        # Calculate balances
        revenue_total = await self._calculate_account_group_balance(
            book_id, revenue_accounts, start_period.id, end_period.id
        )
        cogs_total = await self._calculate_account_group_balance(
            book_id, cogs_accounts, start_period.id, end_period.id
        )
        expense_total = await self._calculate_account_group_balance(
            book_id, expense_accounts, start_period.id, end_period.id
        )
        
        gross_profit = revenue_total - cogs_total
        operating_profit = gross_profit - expense_total
        net_profit = operating_profit  # Simplified (no other income/expense)
        
        report = {
            "book_id": str(book_id),
            "book_name": book.book_name,
            "period_start": period_start.isoformat(),
            "period_end": period_end.isoformat(),
            "currency": book.functional_currency,
            "revenue": {
                "total": float(revenue_total),
                "accounts": await self._get_account_details(
                    book_id, revenue_accounts, start_period.id, end_period.id
                )
            },
            "cost_of_goods_sold": {
                "total": float(cogs_total),
                "accounts": await self._get_account_details(
                    book_id, cogs_accounts, start_period.id, end_period.id
                )
            },
            "gross_profit": float(gross_profit),
            "expenses": {
                "total": float(expense_total),
                "accounts": await self._get_account_details(
                    book_id, expense_accounts, start_period.id, end_period.id
                )
            },
            "operating_profit": float(operating_profit),
            "net_profit": float(net_profit)
        }
        
        if compare_previous:
            # Calculate previous period (same duration, shifted back)
            prev_start = self._shift_date(period_start, period_end, -1)
            prev_end = period_start  # One day before current start
            
            prev_revenue = await self._calculate_account_group_balance(
                book_id, revenue_accounts,
                await self._get_period_id(book_id, prev_start),
                await self._get_period_id(book_id, prev_end)
            )
            prev_expense = await self._calculate_account_group_balance(
                book_id, expense_accounts,
                await self._get_period_id(book_id, prev_start),
                await self._get_period_id(book_id, prev_end)
            )
            
            report["comparison"] = {
                "previous_period_start": prev_start.isoformat(),
                "previous_period_end": prev_end.isoformat(),
                "revenue_change": float(revenue_total - prev_revenue),
                "expense_change": float(expense_total - prev_expense),
                "profit_change": float(net_profit - (prev_revenue - prev_expense))
            }
        
        return report
    
    async def generate_balance_sheet(
        self,
        book_id: UUID,
        as_of_date: date
    ) -> Dict:
        """Generate Balance Sheet report
        
        Args:
            book_id: Book ID
            as_of_date: Report as-of date
        """
        book = await self.book_repo.get_by_id(book_id)
        if not book:
            raise ValueError(f"Book {book_id} not found")
        
        period = await self.period_repo.get_by_book_and_date(book_id, as_of_date)
        if not period:
            raise ValueError(f"Period not found for date {as_of_date}")
        
        # Get account types
        asset_accounts = await self.gl_account_repo.list_by_type(book_id, AccountType.ASSET)
        liability_accounts = await self.gl_account_repo.list_by_type(book_id, AccountType.LIABILITY)
        equity_accounts = await self.gl_account_repo.list_by_type(book_id, AccountType.EQUITY)
        
        # Calculate balances (from period start to as_of_date)
        assets_total = await self._calculate_account_group_balance(
            book_id, asset_accounts, period.id, period.id
        )
        liabilities_total = await self._calculate_account_group_balance(
            book_id, liability_accounts, period.id, period.id
        )
        equity_total = await self._calculate_account_group_balance(
            book_id, equity_accounts, period.id, period.id
        )
        
        # Get retained earnings (from P&L)
        revenue_accounts = await self.gl_account_repo.list_by_type(book_id, AccountType.REVENUE)
        expense_accounts = await self.gl_account_repo.list_by_type(book_id, AccountType.EXPENSE)
        
        revenue = await self._calculate_account_group_balance(
            book_id, revenue_accounts, period.id, period.id
        )
        expenses = await self._calculate_account_group_balance(
            book_id, expense_accounts, period.id, period.id
        )
        net_income = revenue - expenses
        
        total_equity = equity_total + net_income
        total_liabilities_equity = liabilities_total + total_equity
        
        return {
            "book_id": str(book_id),
            "book_name": book.book_name,
            "as_of_date": as_of_date.isoformat(),
            "currency": book.functional_currency,
            "assets": {
                "total": float(assets_total),
                "accounts": await self._get_account_details(
                    book_id, asset_accounts, period.id, period.id
                )
            },
            "liabilities": {
                "total": float(liabilities_total),
                "accounts": await self._get_account_details(
                    book_id, liability_accounts, period.id, period.id
                )
            },
            "equity": {
                "total": float(total_equity),
                "retained_earnings": float(net_income),
                "accounts": await self._get_account_details(
                    book_id, equity_accounts, period.id, period.id
                )
            },
            "total_assets": float(assets_total),
            "total_liabilities_equity": float(total_liabilities_equity),
            "is_balanced": abs(assets_total - total_liabilities_equity) < Decimal("0.01")
        }
    
    async def _calculate_account_group_balance(
        self,
        book_id: UUID,
        accounts: List,
        start_period_id: UUID,
        end_period_id: UUID
    ) -> Decimal:
        """Calculate total balance for a group of accounts"""
        from app.modules.general_ledger.models.journal_entry_model import JournalEntry
        from app.modules.general_ledger.models.journal_line_model import JournalLine
        
        if not accounts:
            return Decimal("0.00")
        
        account_ids = [acc.id for acc in accounts]
        
        query = select(
            func.sum(JournalLine.debit_fc).label("total_debit"),
            func.sum(JournalLine.credit_fc).label("total_credit")
        ).join(JournalEntry).where(
            JournalEntry.book_id == book_id,
            JournalEntry.period_id >= start_period_id,
            JournalEntry.period_id <= end_period_id,
            JournalEntry.status == JournalEntryStatus.POSTED,
            JournalLine.gl_account_id.in_(account_ids)
        )
        
        result = await self.session.execute(query)
        row = result.first()
        
        total_debit = row.total_debit or Decimal("0.00")
        total_credit = row.total_credit or Decimal("0.00")
        
        # For revenue/equity: credit - debit (normal credit balance)
        # For expenses/assets/liabilities: debit - credit (normal debit balance)
        return total_debit - total_credit
    
    async def _get_account_details(
        self,
        book_id: UUID,
        accounts: List,
        start_period_id: UUID,
        end_period_id: UUID
    ) -> List[Dict]:
        """Get account details with balances"""
        from app.modules.general_ledger.models.journal_entry_model import JournalEntry
        from app.modules.general_ledger.models.journal_line_model import JournalLine
        
        details = []
        
        for account in accounts:
            query = select(
                func.sum(JournalLine.debit_fc).label("total_debit"),
                func.sum(JournalLine.credit_fc).label("total_credit")
            ).join(JournalEntry).where(
                JournalEntry.book_id == book_id,
                JournalEntry.period_id >= start_period_id,
                JournalEntry.period_id <= end_period_id,
                JournalEntry.status == JournalEntryStatus.POSTED,
                JournalLine.gl_account_id == account.id
            )
            
            result = await self.session.execute(query)
            row = result.first()
            
            debit = row.total_debit or Decimal("0.00")
            credit = row.total_credit or Decimal("0.00")
            balance = debit - credit
            
            details.append({
                "account_code": account.account_code,
                "account_name": account.account_name,
                "balance": float(balance)
            })
        
        return details
    
    async def _get_period_id(self, book_id: UUID, date: date) -> UUID:
        """Get period ID for a date"""
        period = await self.period_repo.get_by_book_and_date(book_id, date)
        return period.id if period else None
    
    def _shift_date(self, start: date, end: date, periods: int) -> date:
        """Shift date by number of periods"""
        days = (end - start).days * abs(periods)
        if periods < 0:
            return start - timedelta(days=days)
        else:
            return start + timedelta(days=days)
