"""Transfer Model"""
from sqlalchemy import Column, String, Date, ForeignKey, Numeric, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class TransferType(str, enum.Enum):
    """Transfer type"""
    INTERCOMPANY = "INTERCOMPANY"  # Between entities
    INTRA_ENTITY = "INTRA_ENTITY"  # Within same entity
    EXTERNAL = "EXTERNAL"  # To external party


class Transfer(BaseModel):
    """Transfer model (intercompany or intra-entity)"""
    __tablename__ = "treasury_transfer"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    transfer_date = Column(Date, nullable=False, index=True)
    transfer_type = Column(SQLEnum(TransferType), nullable=False, index=True)
    from_bank_account_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_account.id"), nullable=False)
    to_bank_account_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_account.id"), nullable=True)  # Null for external
    to_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=True)  # For intercompany
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    from_bank_transaction_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_transaction.id"), nullable=True)
    to_bank_transaction_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_transaction.id"), nullable=True)
    description = Column(Text)
    reference_number = Column(String(255))
    external_id = Column(String(255), unique=True, nullable=True, index=True)  # External system ID
    
    # Relationships
    entity = relationship("LegalEntity", foreign_keys=[legal_entity_id])
    to_entity = relationship("LegalEntity", foreign_keys=[to_entity_id])
    from_account = relationship("BankAccount", foreign_keys=[from_bank_account_id])
    to_account = relationship("BankAccount", foreign_keys=[to_bank_account_id])
    from_transaction = relationship("BankTransaction", foreign_keys=[from_bank_transaction_id])
    to_transaction = relationship("BankTransaction", foreign_keys=[to_bank_transaction_id])
    
    __table_args__ = (
        {"comment": "Cash transfers (intercompany, intra-entity, external)"}
    )
    
    def __repr__(self):
        return f"<Transfer(type={self.transfer_type.value}, from={self.from_bank_account_id}, amount={self.amount} {self.currency})>"
