"""FX Conversion Model"""
from sqlalchemy import Column, String, Date, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class FXConversion(BaseModel):
    """Foreign exchange conversion model"""
    __tablename__ = "treasury_fx_conversion"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    conversion_date = Column(Date, nullable=False, index=True)
    from_currency = Column(String(3), nullable=False)
    to_currency = Column(String(3), nullable=False)
    from_amount = Column(Numeric(15, 2), nullable=False)
    to_amount = Column(Numeric(15, 2), nullable=False)
    exchange_rate = Column(Numeric(15, 6), nullable=False)
    rate_source = Column(String(100))  # api, manual, bank
    from_bank_account_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_account.id"), nullable=True)
    to_bank_account_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_account.id"), nullable=True)
    from_bank_transaction_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_transaction.id"), nullable=True)
    to_bank_transaction_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_transaction.id"), nullable=True)
    description = Column(String(500))
    external_id = Column(String(255), unique=True, nullable=True, index=True)  # External system ID
    
    # Relationships
    entity = relationship("LegalEntity")
    from_account = relationship("BankAccount", foreign_keys=[from_bank_account_id])
    to_account = relationship("BankAccount", foreign_keys=[to_bank_account_id])
    from_transaction = relationship("BankTransaction", foreign_keys=[from_bank_transaction_id])
    to_transaction = relationship("BankTransaction", foreign_keys=[to_bank_transaction_id])
    
    __table_args__ = (
        {"comment": "FX conversions with realized rates"}
    )
    
    def __repr__(self):
        return f"<FXConversion({self.from_currency} {self.from_amount} -> {self.to_currency} {self.to_amount}, rate={self.exchange_rate})>"
