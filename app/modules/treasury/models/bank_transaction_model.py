"""Bank Transaction Model"""
from sqlalchemy import Column, String, Date, ForeignKey, Numeric, Text, Enum as SQLEnum, Boolean, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class TransactionType(str, enum.Enum):
    """Bank transaction type"""
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER_IN = "TRANSFER_IN"
    TRANSFER_OUT = "TRANSFER_OUT"
    FEE = "FEE"
    INTEREST = "INTEREST"
    OTHER = "OTHER"


class BankTransaction(BaseModel):
    """Bank transaction (statement line) model"""
    __tablename__ = "treasury_bank_transaction"
    
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_account.id"), nullable=False, index=True)
    transaction_date = Column(Date, nullable=False, index=True)
    value_date = Column(Date, nullable=True)  # Value date (when funds are available)
    amount = Column(Numeric(15, 2), nullable=False)  # Positive for deposits, negative for withdrawals
    currency = Column(String(3), nullable=False)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False, index=True)
    description = Column(Text)
    reference_number = Column(String(255))  # Bank reference
    counterparty_name = Column(String(255))
    counterparty_account = Column(String(100))
    balance_after = Column(Numeric(15, 2))  # Account balance after this transaction
    is_reconciled = Column(Boolean, default=False, nullable=False, index=True)
    reconciliation_id = Column(UUID(as_uuid=True), nullable=True)  # Link to reconciliation session
    external_id = Column(String(255), unique=True, nullable=True, index=True)  # External system ID (for dedupe)
    import_batch_id = Column(String(100), nullable=True, index=True)  # CSV import batch
    
    # Relationships
    bank_account = relationship("BankAccount", back_populates="transactions")
    
    __table_args__ = (
        Index("ix_treasury_bank_tx_account_date", "bank_account_id", "transaction_date"),
        Index("ix_treasury_bank_tx_account_reconciled", "bank_account_id", "is_reconciled"),
        {"comment": "Bank statement transactions"},
    )
    
    def __repr__(self):
        return f"<BankTransaction(account={self.bank_account_id}, date={self.transaction_date}, amount={self.amount}, type={self.transaction_type.value})>"
