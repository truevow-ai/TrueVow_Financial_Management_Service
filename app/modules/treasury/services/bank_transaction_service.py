"""Bank Transaction Service"""
from typing import List, Optional, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from app.modules.treasury.repositories.bank_transaction_repository import BankTransactionRepository
from app.modules.treasury.repositories.bank_account_repository import BankAccountRepository
from app.modules.treasury.models.bank_transaction_model import BankTransaction, TransactionType
from app.core.exceptions import NotFoundError, ValidationError, DuplicateEntryError


class BankTransactionService:
    """Service for bank transaction management"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.transaction_repo = BankTransactionRepository(session)
        self.account_repo = BankAccountRepository(session)
    
    async def create_transaction(
        self,
        bank_account_id: UUID,
        transaction_date: date,
        amount: Decimal,
        currency: str,
        transaction_type: TransactionType,
        description: Optional[str] = None,
        value_date: Optional[date] = None,
        reference_number: Optional[str] = None,
        counterparty_name: Optional[str] = None,
        counterparty_account: Optional[str] = None,
        balance_after: Optional[Decimal] = None,
        external_id: Optional[str] = None,
        import_batch_id: Optional[str] = None,
        commit: bool = True
    ) -> BankTransaction:
        """
        Create a bank transaction
        
        Args:
            commit: If False, don't commit (for batch operations). Default True for backward compatibility.
        """
        # Verify account exists
        account = await self.account_repo.get_by_id(bank_account_id)
        if not account:
            raise NotFoundError(f"Bank account {bank_account_id} not found")
        
        # Check for duplicate by external_id
        if external_id:
            existing = await self.transaction_repo.get_by_external_id(external_id)
            if existing:
                raise DuplicateEntryError(f"Transaction with external_id {external_id} already exists")
        
        # Validate currency matches account
        if currency != account.currency:
            raise ValidationError(f"Transaction currency {currency} does not match account currency {account.currency}")
        
        transaction = await self.transaction_repo.create(
            bank_account_id=bank_account_id,
            transaction_date=transaction_date,
            value_date=value_date or transaction_date,
            amount=amount,
            currency=currency,
            transaction_type=transaction_type,
            description=description,
            reference_number=reference_number,
            counterparty_name=counterparty_name,
            counterparty_account=counterparty_account,
            balance_after=balance_after,
            external_id=external_id,
            import_batch_id=import_batch_id,
            is_reconciled=False
        )
        
        if commit:
            await self.session.commit()
        return transaction
    
    async def import_csv_transactions(
        self,
        bank_account_id: UUID,
        transactions_data: List[Dict],
        import_batch_id: str
    ) -> tuple[int, int]:
        """
        Import transactions from CSV data (atomic batch operation)
        
        Uses external_id uniqueness to prevent duplicates on retry.
        If handler fails mid-import, retry will skip already-imported transactions.
        
        Returns: (created_count, skipped_count)
        """
        created = 0
        skipped = 0
        
        # Import all transactions in single transaction (atomic)
        for row in transactions_data:
            try:
                # Check for duplicate by external_id if provided
                external_id = row.get("external_id")
                if external_id:
                    existing = await self.transaction_repo.get_by_external_id(external_id)
                    if existing:
                        skipped += 1
                        continue
                
                # Parse transaction (don't commit individually - batch commit at end)
                await self.create_transaction(
                    bank_account_id=bank_account_id,
                    transaction_date=row["transaction_date"],
                    amount=Decimal(str(row["amount"])),
                    currency=row["currency"],
                    transaction_type=TransactionType(row.get("transaction_type", "OTHER")),
                    description=row.get("description"),
                    value_date=row.get("value_date"),
                    reference_number=row.get("reference_number"),
                    counterparty_name=row.get("counterparty_name"),
                    counterparty_account=row.get("counterparty_account"),
                    balance_after=Decimal(str(row["balance_after"])) if row.get("balance_after") else None,
                    external_id=external_id,
                    import_batch_id=import_batch_id,
                    commit=False  # Batch commit at end
                )
                created += 1
            except (ValidationError, DuplicateEntryError) as e:
                skipped += 1
                continue
        
        # Single commit for entire batch (atomic)
        await self.session.commit()
        return created, skipped
    
    async def get_transaction(self, transaction_id: UUID) -> Optional[BankTransaction]:
        """Get transaction by ID"""
        return await self.transaction_repo.get_by_id(transaction_id)
    
    async def list_transactions(
        self,
        bank_account_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        is_reconciled: Optional[bool] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[BankTransaction]:
        """List transactions for an account"""
        return await self.transaction_repo.list_by_account(
            bank_account_id=bank_account_id,
            start_date=start_date,
            end_date=end_date,
            is_reconciled=is_reconciled,
            limit=limit,
            offset=offset
        )
    
    async def list_with_cursor(
        self,
        bank_account_id: Optional[UUID] = None,
        updated_after: Optional[datetime] = None,
        limit: int = 100,
        cursor: Optional[str] = None
    ) -> tuple[List[BankTransaction], Optional[str]]:
        """List transactions with cursor pagination"""
        return await self.transaction_repo.list_with_cursor(
            bank_account_id=bank_account_id,
            updated_after=updated_after,
            limit=limit,
            cursor=cursor
        )
