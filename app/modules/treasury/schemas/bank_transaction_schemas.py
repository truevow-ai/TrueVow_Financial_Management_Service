"""Bank Transaction Schemas"""
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from app.modules.treasury.models.bank_transaction_model import TransactionType


class BankTransactionCreate(BaseModel):
    """Schema for creating a bank transaction"""
    bank_account_id: UUID
    transaction_date: date
    amount: Decimal
    currency: str = Field(..., min_length=3, max_length=3)
    transaction_type: TransactionType
    description: str | None = None
    value_date: date | None = None
    reference_number: str | None = None
    counterparty_name: str | None = None
    counterparty_account: str | None = None
    balance_after: Decimal | None = None
    external_id: str | None = None


class BankTransactionCSVImport(BaseModel):
    """Schema for CSV import request"""
    bank_account_id: UUID
    transactions: list[dict] = Field(..., min_items=1)
    import_batch_id: str = Field(..., min_length=1)


class BankTransactionResponse(BaseModel):
    """Schema for bank transaction response"""
    id: UUID
    bank_account_id: UUID
    transaction_date: date
    value_date: date | None
    amount: Decimal
    currency: str
    transaction_type: TransactionType
    description: str | None
    reference_number: str | None
    counterparty_name: str | None
    counterparty_account: str | None
    balance_after: Decimal | None
    is_reconciled: bool
    external_id: str | None
    import_batch_id: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BankTransactionListResponse(BaseModel):
    """Schema for paginated transaction list"""
    transactions: list[BankTransactionResponse]
    next_cursor: str | None = None
    limit: int
    has_more: bool
