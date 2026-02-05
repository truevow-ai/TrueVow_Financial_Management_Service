"""Bank Account Model"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class BankAccount(BaseModel):
    """Bank account model"""
    __tablename__ = "treasury_bank_account"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("book.id"), nullable=True, index=True)  # CASH book for this entity
    account_name = Column(String(255), nullable=False)
    account_number = Column(String(100))
    bank_name = Column(String(255), nullable=False)
    bank_code = Column(String(50))
    currency = Column(String(3), nullable=False)  # USD, AED, PKR
    account_type = Column(String(50))  # checking, savings, etc.
    is_active = Column(Boolean, default=True, nullable=False)
    wps_enabled = Column(Boolean, default=False, nullable=False)  # UAE WPS support
    wps_agent_id = Column(String(100))  # WPS agent/bank code for UAE
    
    # Relationships
    entity = relationship("LegalEntity")
    transactions = relationship("BankTransaction", back_populates="bank_account", cascade="all, delete-orphan")
    reconciliations = relationship("ReconciliationSession", back_populates="bank_account")
    
    __table_args__ = (
        {"comment": "Bank accounts per legal entity"}
    )
    
    def __repr__(self):
        return f"<BankAccount(name={self.account_name}, currency={self.currency}, entity={self.legal_entity_id})>"
