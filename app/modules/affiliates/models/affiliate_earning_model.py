"""Affiliate Earning and Payout Models"""
from sqlalchemy import Column, String, Date, DateTime, ForeignKey, Numeric, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class EarningEventType(str, enum.Enum):
    """Type of affiliate earning event."""
    SIGNUP = "SIGNUP"
    REVENUE = "REVENUE"
    SUBSCRIPTION = "SUBSCRIPTION"


class PayoutStatus(str, enum.Enum):
    """Affiliate payout status."""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    PAID = "PAID"
    CANCELLED = "CANCELLED"


class AffiliateEarningEvent(BaseModel):
    """Individual earning event credited to an affiliate."""
    __tablename__ = "affiliate_earning_event"

    partner_id = Column(UUID(as_uuid=True), ForeignKey("affiliate_partner.id"), nullable=False, index=True)
    event_type = Column(SQLEnum(EarningEventType), nullable=False, index=True)
    event_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    reference_type = Column(String(100), nullable=True)  # e.g. invoice_id, subscription_id
    reference_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    description = Column(Text, nullable=True)

    partner = relationship("AffiliatePartner", back_populates="earning_events")

    __table_args__ = ({"comment": "Affiliate earning events"},)

    def __repr__(self):
        return f"<AffiliateEarningEvent(partner_id={self.partner_id}, type={self.event_type}, amount={self.amount})>"


class AffiliatePayout(BaseModel):
    """Payout batch or record to an affiliate."""
    __tablename__ = "affiliate_payout"

    partner_id = Column(UUID(as_uuid=True), ForeignKey("affiliate_partner.id"), nullable=False, index=True)
    payout_date = Column(Date, nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(SQLEnum(PayoutStatus), default=PayoutStatus.PENDING, nullable=False, index=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    external_ref = Column(String(255), nullable=True)  # e.g. transfer_id
    notes = Column(Text, nullable=True)

    partner = relationship("AffiliatePartner", back_populates="payouts")

    __table_args__ = ({"comment": "Affiliate payouts"},)

    def __repr__(self):
        return f"<AffiliatePayout(partner_id={self.partner_id}, amount={self.amount}, status={self.status})>"
