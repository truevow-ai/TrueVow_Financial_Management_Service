"""Affiliate Partner Model"""
from sqlalchemy import Column, String, Boolean, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from app.shared.models.base_model import BaseModel


class AffiliatePartner(BaseModel):
    """Affiliate partner (external partner in affiliate program)."""
    __tablename__ = "affiliate_partner"

    partner_code = Column(String(100), unique=True, nullable=False, index=True)
    partner_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)

    agreements = relationship("AffiliateAgreement", back_populates="partner", cascade="all, delete-orphan")
    earning_events = relationship("AffiliateEarningEvent", back_populates="partner", cascade="all, delete-orphan")
    payouts = relationship("AffiliatePayout", back_populates="partner", cascade="all, delete-orphan")

    __table_args__ = ({"comment": "Affiliate partners"},)

    def __repr__(self):
        return f"<AffiliatePartner(code={self.partner_code}, name={self.partner_name})>"
