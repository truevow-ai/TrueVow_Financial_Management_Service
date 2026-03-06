"""Settlement Model"""
from sqlalchemy import Column, String, Date, ForeignKey, Numeric, Enum as SQLEnum, Index, text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class SettlementSource(str, enum.Enum):
    """Settlement source"""
    STRIPE = "STRIPE"
    TELR = "TELR"
    MANUAL = "MANUAL"


class Settlement(BaseModel):
    """Payment gateway settlement model"""
    __tablename__ = "treasury_settlement"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_account.id"), nullable=False, index=True)
    settlement_date = Column(Date, nullable=False, index=True)
    source = Column(SQLEnum(SettlementSource), nullable=False, index=True)
    gross_amount = Column(Numeric(15, 2), nullable=False)  # Total settlement amount
    fees = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)  # Gateway fees
    net_amount = Column(Numeric(15, 2), nullable=False)  # Net after fees
    currency = Column(String(3), nullable=False)
    external_settlement_id = Column(String(255), nullable=True, index=True)  # Gateway settlement ID
    external_payout_id = Column(String(255), nullable=True)  # Gateway payout ID
    bank_transaction_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_transaction.id"), nullable=True)  # Linked bank tx
    description = Column(String(500))
    
    # Relationships
    entity = relationship("LegalEntity")
    bank_account = relationship("BankAccount")
    bank_transaction = relationship("BankTransaction")
    
    __table_args__ = (
        # Partial unique index: (source, external_settlement_id) where external_settlement_id IS NOT NULL
        # This prevents duplicate settlements from the same provider with the same external ID
        Index(
            "uq_settlement_source_external_id",
            "source",
            "external_settlement_id",
            unique=True,
            postgresql_where=text("external_settlement_id IS NOT NULL")
        ),
        {"comment": "Payment gateway settlements (Stripe/TELR payouts)"}
    )
    
    def __repr__(self):
        return f"<Settlement(source={self.source.value}, date={self.settlement_date}, net={self.net_amount}, currency={self.currency})>"
