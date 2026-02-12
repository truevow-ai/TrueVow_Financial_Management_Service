"""Affiliate Agreement Model"""
from sqlalchemy import Column, String, Date, ForeignKey, Numeric, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class AffiliateAgreement(BaseModel):
    """Agreement terms for an affiliate partner."""
    __tablename__ = "affiliate_agreement"

    partner_id = Column(UUID(as_uuid=True), ForeignKey("affiliate_partner.id"), nullable=False, index=True)
    agreement_code = Column(String(100), unique=True, nullable=False, index=True)
    commission_rate = Column(Numeric(10, 4), default=Decimal("0.00"), nullable=False)
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    terms = Column(Text, nullable=True)

    partner = relationship("AffiliatePartner", back_populates="agreements")

    __table_args__ = ({"comment": "Affiliate agreements"},)

    def __repr__(self):
        return f"<AffiliateAgreement(code={self.agreement_code}, partner_id={self.partner_id})>"
