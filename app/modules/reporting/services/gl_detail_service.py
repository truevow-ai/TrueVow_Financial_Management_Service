"""GL Detail Report Service"""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.modules.general_ledger.repositories.gl_account_repository import GLAccountRepository
from app.modules.general_ledger.repositories.journal_entry_repository import JournalEntryRepository
from app.modules.general_ledger.repositories.accounting_period_repository import AccountingPeriodRepository
from app.modules.general_ledger.models.journal_entry_model import JournalEntryStatus


class GLDetailService:
    """Service for generating GL Detail reports"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.gl_account_repo = GLAccountRepository(session)
        self.je_repo = JournalEntryRepository(session)
        self.period_repo = AccountingPeriodRepository(session)
    
    async def generate_gl_detail(
        self,
        book_id: UUID,
        account_id: Optional[UUID] = None,
        account_code: Optional[str] = None,
        period_start: Optional[date] = None,
        period_end: Optional[date] = None,
        period_id: Optional[UUID] = None,
        include_dimensions: bool = True
    ) -> Dict:
        """Generate GL Detail report
        
        Args:
            book_id: Book ID
            account_id: Optional account ID filter
            account_code: Optional account code filter
            period_start: Optional period start date
            period_end: Optional period end date
            period_id: Optional period ID (overrides dates)
            include_dimensions: Include dimension details on lines
        """
        # Get account
        if account_id:
            account = await self.gl_account_repo.get_by_id(account_id)
        elif account_code:
            account = await self.gl_account_repo.get_by_code(book_id, account_code)
        else:
            raise ValueError("Either account_id or account_code must be provided")
        
        if not account:
            raise ValueError("Account not found")
        
        # Get period(s)
        if period_id:
            period = await self.period_repo.get_by_id(period_id)
            periods = [period] if period else []
        elif period_start and period_end:
            # Get all periods in range
            all_periods = await self.period_repo.list_by_book(book_id)
            periods = [
                p for p in all_periods
                if p.period_start >= period_start and p.period_end <= period_end
            ]
        else:
            raise ValueError("Either period_id or period_start/period_end must be provided")
        
        if not periods:
            raise ValueError("No periods found for date range")
        
        period_ids = [p.id for p in periods]
        
        # Get journal lines for account
        from app.modules.general_ledger.models.journal_entry_model import JournalEntry
        from app.modules.general_ledger.models.journal_line_model import JournalLine
        
        query = select(JournalLine).join(JournalEntry).where(
            JournalEntry.book_id == book_id,
            JournalEntry.period_id.in_(period_ids),
            JournalEntry.status == JournalEntryStatus.POSTED,
            JournalLine.gl_account_id == account.id
        ).order_by(JournalEntry.entry_date, JournalLine.line_number)
        
        result = await self.session.execute(query)
        lines = list(result.scalars().all())
        
        # Build detail rows
        detail_rows = []
        running_balance = Decimal("0.00")
        
        for line in lines:
            # Calculate running balance
            running_balance += (line.debit_fc or Decimal("0.00")) - (line.credit_fc or Decimal("0.00"))
            
            row = {
                "entry_date": line.journal_entry.entry_date.isoformat(),
                "entry_number": line.journal_entry.entry_number,
                "line_number": line.line_number,
                "description": line.description or line.journal_entry.description,
                "reference_number": line.journal_entry.reference_number,
                "debit": float(line.debit_fc or Decimal("0.00")),
                "credit": float(line.credit_fc or Decimal("0.00")),
                "running_balance": float(running_balance)
            }
            
            if include_dimensions:
                # Get dimensions for line
                from app.modules.general_ledger.repositories.dimension_repository import DimensionValueRepository
                dim_repo = DimensionValueRepository(self.session)
                dimensions = await dim_repo.list_by_journal_line(line.id)
                
                row["dimensions"] = {
                    dv.dimension.code: dv.value_code
                    for dv in dimensions
                    if dv.dimension
                }
            
            detail_rows.append(row)
        
        # Calculate period totals
        period_totals = {}
        for period in periods:
            period_lines = [
                line for line in lines
                if line.journal_entry.period_id == period.id
            ]
            
            period_debit = sum(line.debit_fc or Decimal("0.00") for line in period_lines)
            period_credit = sum(line.credit_fc or Decimal("0.00") for line in period_lines)
            
            period_totals[period.id] = {
                "period_start": period.period_start.isoformat(),
                "period_end": period.period_end.isoformat(),
                "debit": float(period_debit),
                "credit": float(period_credit),
                "net": float(period_debit - period_credit)
            }
        
        # Calculate overall totals
        total_debit = sum(line.debit_fc or Decimal("0.00") for line in lines)
        total_credit = sum(line.credit_fc or Decimal("0.00") for line in lines)
        
        return {
            "book_id": str(book_id),
            "account_id": str(account.id),
            "account_code": account.account_code,
            "account_name": account.account_name,
            "period_start": periods[0].period_start.isoformat() if periods else None,
            "period_end": periods[-1].period_end.isoformat() if periods else None,
            "total_debit": float(total_debit),
            "total_credit": float(total_credit),
            "ending_balance": float(running_balance),
            "period_totals": list(period_totals.values()),
            "transactions": detail_rows
        }
