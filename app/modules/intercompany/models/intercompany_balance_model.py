"""Intercompany Balance Model"""
from sqlalchemy import Column, String, Date, ForeignKey, Numeric, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class BalanceType(str, enum.Enum):
    """Balance type"""
    NET = "NET"  # Net balance (sum of all transfers)
    RECEIVABLE = "RECEIVABLE"  # Amount receivable
    PAYABLE = "PAYABLE"  # Amount payable


class IntercompanyBalance(BaseModel):
    """Intercompany balance snapshot"""
    __tablename__ = "intercompany_balance"
    
    from_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    to_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    as_of_date = Column(Date, nullable=False, index=True)
    balance_type = Column(SQLEnum(BalanceType), default=BalanceType.NET, nullable=False)
    balance_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    
    # Relationships
    from_entity = relationship("LegalEntity", foreign_keys=[from_entity_id])
    to_entity = relationship("LegalEntity", foreign_keys=[to_entity_id])
    
    __table_args__ = (
        UniqueConstraint("from_entity_id", "to_entity_id", "as_of_date", "balance_type", name="uq_intercompany_balance_from_to_date_type"),
        {"comment": "Intercompany balance snapshots"},
    )
    
    def __repr__(self):
        return f"<IntercompanyBalance(from={self.from_entity_id}, to={self.to_entity_id}, date={self.as_of_date}, balance={self.balance_amount})>"
