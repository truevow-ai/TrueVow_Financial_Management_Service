"""Royalty Models"""
from sqlalchemy import Column, String, Date, DateTime, Integer, ForeignKey, Numeric, Enum as SQLEnum, Text, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class RoyaltyBasis(str, enum.Enum):
    """Royalty calculation basis"""
    REVENUE = "REVENUE"
    RECOGNIZED_REVENUE = "RECOGNIZED_REVENUE"
    COLLECTED_REVENUE = "COLLECTED_REVENUE"
    FIXED = "FIXED"


class RoyaltyRunStatus(str, enum.Enum):
    """Royalty run status (for approval workflow)"""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    POSTED = "POSTED"
    REJECTED = "REJECTED"


class RoyaltyAgreement(BaseModel):
    """Royalty agreement model"""
    __tablename__ = "royalty_agreement"
    
    from_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    to_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    agreement_code = Column(String(100), unique=True, nullable=False, index=True)
    agreement_name = Column(String(255), nullable=False)
    basis = Column(SQLEnum(RoyaltyBasis), default=RoyaltyBasis.REVENUE, nullable=False)
    rate = Column(Numeric(10, 4), nullable=False)  # Percentage rate
    fixed_amount = Column(Numeric(15, 2), nullable=True)  # If basis is FIXED
    effective_from = Column(Date, nullable=False)
    effective_to = Column(Date, nullable=True)
    currency = Column(String(3), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(Text, nullable=True)
    
    # Relationships
    from_entity = relationship("LegalEntity", foreign_keys=[from_entity_id])
    to_entity = relationship("LegalEntity", foreign_keys=[to_entity_id])
    calculations = relationship("RoyaltyCalculation", back_populates="agreement", cascade="all, delete-orphan")
    
    __table_args__ = (
        {"comment": "Royalty agreements between entities"}
    )
    
    def __repr__(self):
        return f"<RoyaltyAgreement(code={self.agreement_code}, from={self.from_entity_id}, to={self.to_entity_id}, rate={self.rate}%)>"


class RoyaltyCalculation(BaseModel):
    """Royalty calculation per period"""
    __tablename__ = "royalty_calculation"
    
    royalty_agreement_id = Column(UUID(as_uuid=True), ForeignKey("royalty_agreement.id"), nullable=False, index=True)
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)
    revenue_base = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    recognized_revenue_base = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    collected_revenue_base = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    calculated_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    # Approval workflow fields
    status = Column(SQLEnum(RoyaltyRunStatus), default=RoyaltyRunStatus.DRAFT, nullable=False, index=True)
    submitted_by = Column(UUID(as_uuid=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(UUID(as_uuid=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    decision_reason = Column(Text, nullable=True)
    row_version = Column(Integer, default=1, nullable=False)
    # Posting fields (legacy: kept for backward compatibility)
    is_posted = Column(Boolean, default=False, nullable=False, index=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    posted_by = Column(UUID(as_uuid=True), nullable=True)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entry.id"), nullable=True)
    intercompany_transfer_id = Column(UUID(as_uuid=True), ForeignKey("intercompany_transfer.id"), nullable=True)
    
    # Relationships
    agreement = relationship("RoyaltyAgreement", back_populates="calculations")
    journal_entry = relationship("JournalEntry")
    transfer = relationship("IntercompanyTransfer")
    
    __table_args__ = (
        UniqueConstraint("royalty_agreement_id", "period_start", name="uq_royalty_calc_agreement_period"),
        {"comment": "Royalty calculations per period"},
    )
    
    def __repr__(self):
        return f"<RoyaltyCalculation(agreement={self.royalty_agreement_id}, period={self.period_start}, amount={self.calculated_amount})>"
