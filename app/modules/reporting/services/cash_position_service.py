"""Cash Position Report Service"""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from uuid import UUID
from datetime import date
from decimal import Decimal
from app.modules.treasury.repositories.bank_account_repository import BankAccountRepository
from app.modules.treasury.repositories.bank_transaction_repository import BankTransactionRepository
from app.modules.general_ledger.repositories.book_repository import BookRepository
from app.modules.general_ledger.models.book_model import BookType


class CashPositionService:
    """Service for generating Cash Position reports"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.bank_account_repo = BankAccountRepository(session)
        self.bank_transaction_repo = BankTransactionRepository(session)
        self.book_repo = BookRepository(session)
    
    async def generate_cash_position(
        self,
        entity_id: UUID,
        as_of_date: date,
        currency: Optional[str] = None
    ) -> Dict:
        """Generate Cash Position report
        
        Args:
            entity_id: Legal entity ID
            as_of_date: Report as-of date
            currency: Optional currency filter
        """
        # Get all bank accounts for entity
        bank_accounts = await self.bank_account_repo.list_by_entity(entity_id)
        
        if currency:
            bank_accounts = [acc for acc in bank_accounts if acc.currency == currency]
        
        # Calculate balances per account
        account_positions = []
        total_balance = Decimal("0.00")
        
        for account in bank_accounts:
            # Get balance as of date
            balance = await self._calculate_account_balance(account.id, as_of_date)
            
            # Get pending transactions (after as_of_date)
            pending = await self._get_pending_transactions(account.id, as_of_date)
            
            account_positions.append({
                "bank_account_id": str(account.id),
                "bank_name": account.bank_name,
                "account_number": account.account_number,
                "account_name": account.account_name,
                "currency": account.currency,
                "balance_as_of": float(balance),
                "pending_debits": float(pending["debits"]),
                "pending_credits": float(pending["credits"]),
                "projected_balance": float(balance - pending["debits"] + pending["credits"])
            })
            
            total_balance += balance
        
        # Group by currency
        by_currency: Dict[str, Dict] = {}
        for pos in account_positions:
            curr = pos["currency"]
            if curr not in by_currency:
                by_currency[curr] = {
                    "currency": curr,
                    "total_balance": Decimal("0.00"),
                    "total_pending_debits": Decimal("0.00"),
                    "total_pending_credits": Decimal("0.00"),
                    "accounts": []
                }
            
            by_currency[curr]["total_balance"] += Decimal(str(pos["balance_as_of"]))
            by_currency[curr]["total_pending_debits"] += Decimal(str(pos["pending_debits"]))
            by_currency[curr]["total_pending_credits"] += Decimal(str(pos["pending_credits"]))
            by_currency[curr]["accounts"].append(pos)
        
        # Convert to float for JSON
        for curr in by_currency:
            by_currency[curr]["total_balance"] = float(by_currency[curr]["total_balance"])
            by_currency[curr]["total_pending_debits"] = float(by_currency[curr]["total_pending_debits"])
            by_currency[curr]["total_pending_credits"] = float(by_currency[curr]["total_pending_credits"])
            by_currency[curr]["projected_balance"] = (
                by_currency[curr]["total_balance"] -
                by_currency[curr]["total_pending_debits"] +
                by_currency[curr]["total_pending_credits"]
            )
        
        return {
            "entity_id": str(entity_id),
            "as_of_date": as_of_date.isoformat(),
            "by_currency": list(by_currency.values()),
            "total_accounts": len(account_positions)
        }
    
    async def _calculate_account_balance(
        self,
        bank_account_id: UUID,
        as_of_date: date
    ) -> Decimal:
        """Calculate account balance as of date"""
        # Get all transactions up to as_of_date
        transactions = await self.bank_transaction_repo.list_by_account(
            bank_account_id=bank_account_id,
            start_date=None,
            end_date=as_of_date,
            limit=10000
        )
        
        balance = Decimal("0.00")
        for txn in transactions:
            if txn.transaction_type in ["DEPOSIT", "CREDIT", "TRANSFER_IN"]:
                balance += txn.amount
            elif txn.transaction_type in ["WITHDRAWAL", "DEBIT", "TRANSFER_OUT", "FEE"]:
                balance -= txn.amount
        
        return balance
    
    async def _get_pending_transactions(
        self,
        bank_account_id: UUID,
        as_of_date: date
    ) -> Dict[str, Decimal]:
        """Get pending transactions after as_of_date"""
        transactions = await self.bank_transaction_repo.list_by_account(
            bank_account_id=bank_account_id,
            start_date=as_of_date,
            end_date=None,
            limit=10000
        )
        
        debits = Decimal("0.00")
        credits = Decimal("0.00")
        
        for txn in transactions:
            if txn.transaction_type in ["WITHDRAWAL", "DEBIT", "TRANSFER_OUT", "FEE"]:
                debits += txn.amount
            elif txn.transaction_type in ["DEPOSIT", "CREDIT", "TRANSFER_IN"]:
                credits += txn.amount
        
        return {"debits": debits, "credits": credits}
