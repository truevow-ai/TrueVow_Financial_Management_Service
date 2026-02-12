"""Intercompany Transfer Model"""
from sqlalchemy import Column, String, Date, Boolean, ForeignKey, Numeric, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class TransferDirection(str, enum.Enum):
    """Transfer direction"""
    FROM_ENTITY = "FROM_ENTITY"
    TO_ENTITY = "TO_ENTITY"


class IntercompanyTransfer(BaseModel):
    """Intercompany transfer model"""
    __tablename__ = "intercompany_transfer"
    
    from_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    to_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    transfer_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    transfer_type = Column(String(50))  # CASH, ROYALTY, LOAN, etc.
    description = Column(Text)
    reference_number = Column(String(255))
    
    # Treasury links
    from_bank_account_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_account.id"), nullable=True)
    to_bank_account_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_account.id"), nullable=True)
    from_bank_transaction_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_transaction.id"), nullable=True)
    to_bank_transaction_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_transaction.id"), nullable=True)
    
    # Journal entry links (both entities)
    from_entity_je_id = Column(UUID(as_uuid=True), ForeignKey("journal_entry.id"), nullable=True)
    to_entity_je_id = Column(UUID(as_uuid=True), ForeignKey("journal_entry.id"), nullable=True)
    
    # Reconciliation
    is_reconciled = Column(Boolean, default=False, nullable=False, index=True)
    reconciled_at = Column(Date, nullable=True)
    
    # Relationships
    from_entity = relationship("LegalEntity", foreign_keys=[from_entity_id])
    to_entity = relationship("LegalEntity", foreign_keys=[to_entity_id])
    from_account = relationship("BankAccount", foreign_keys=[from_bank_account_id])
    to_account = relationship("BankAccount", foreign_keys=[to_bank_account_id])
    from_transaction = relationship("BankTransaction", foreign_keys=[from_bank_transaction_id])
    to_transaction = relationship("BankTransaction", foreign_keys=[to_bank_transaction_id])
    from_je = relationship("JournalEntry", foreign_keys=[from_entity_je_id])
    to_je = relationship("JournalEntry", foreign_keys=[to_entity_je_id])
    
    __table_args__ = (
        {"comment": "Intercompany transfers between entities"}
    )
    
    def __repr__(self):
        return f"<IntercompanyTransfer(from={self.from_entity_id}, to={self.to_entity_id}, amount={self.amount} {self.currency})>"
