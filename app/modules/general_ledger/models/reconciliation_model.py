"""Reconciliation Model"""
from sqlalchemy import Column, String, Date, ForeignKey, Numeric, Enum as SQLEnum, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class ReconciliationStatus(str, enum.Enum):
    """Reconciliation status"""
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"


class ReconciliationSession(BaseModel):
    """Bank reconciliation session model"""
    __tablename__ = "reconciliation_session"
    
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_account.id"), nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    statement_ending_balance = Column(Numeric(15, 2), nullable=False)
    statement_currency = Column(String(3), nullable=False)
    status = Column(SQLEnum(ReconciliationStatus), default=ReconciliationStatus.DRAFT, nullable=False, index=True)
    reconciled_by = Column(UUID(as_uuid=True), nullable=True)
    reconciled_at = Column(Date, nullable=True)
    difference = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)  # Calculated difference
    notes = Column(Text, nullable=True)
    
    # Relationships
    bank_account = relationship("BankAccount")
    matches = relationship("ReconciliationMatch", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        {"comment": "Bank reconciliation sessions"}
    )
    
    def __repr__(self):
        return f"<ReconciliationSession(account={self.bank_account_id}, period={self.period_start} to {self.period_end}, status={self.status.value})>"


class ReconciliationMatch(BaseModel):
    """Reconciliation match model"""
    __tablename__ = "reconciliation_match"
    
    reconciliation_session_id = Column(UUID(as_uuid=True), ForeignKey("reconciliation_session.id"), nullable=False, index=True)
    bank_transaction_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_transaction.id"), nullable=True)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entry.id"), nullable=True)
    match_type = Column(String(50), nullable=False)  # auto, manual
    match_confidence = Column(Numeric(5, 2), nullable=True)  # 0-100 for auto matches
    notes = Column(Text, nullable=True)
    
    # Relationships
    session = relationship("ReconciliationSession", back_populates="matches")
    bank_transaction = relationship("BankTransaction")
    journal_entry = relationship("JournalEntry")
    
    __table_args__ = (
        UniqueConstraint("reconciliation_session_id", "bank_transaction_id", name="uq_reconciliation_match_session_tx"),
        {"comment": "Matches between bank transactions and journal entries"},
    )
    
    def __repr__(self):
        return f"<ReconciliationMatch(session={self.reconciliation_session_id}, tx={self.bank_transaction_id}, je={self.journal_entry_id})>"
