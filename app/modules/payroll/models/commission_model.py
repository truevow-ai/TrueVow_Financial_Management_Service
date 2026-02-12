"""Commission Models"""
from sqlalchemy import Column, String, Date, ForeignKey, Numeric, Enum as SQLEnum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class CommissionBasis(str, enum.Enum):
    """Commission basis"""
    RECOGNIZED = "RECOGNIZED"  # Based on recognized revenue
    COLLECTED = "COLLECTED"  # Based on collected cash
    HYBRID = "HYBRID"  # Both recognized and collected


class CommissionPlan(BaseModel):
    """Commission plan model"""
    __tablename__ = "commission_plan"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    plan_code = Column(String(50), unique=True, nullable=False, index=True)
    plan_name = Column(String(255), nullable=False)
    basis = Column(SQLEnum(CommissionBasis), default=CommissionBasis.HYBRID, nullable=False)
    payout_mode = Column(String(50), default="PAYROLL", nullable=False)  # PAYROLL or AP
    default_recognized_rate = Column(Numeric(10, 4), default=Decimal("0.00"), nullable=False)
    default_collected_rate = Column(Numeric(10, 4), default=Decimal("0.00"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    entity = relationship("LegalEntity")
    rules = relationship("CommissionRule", back_populates="plan", cascade="all, delete-orphan")
    ledger_entries = relationship("CommissionLedger", back_populates="plan")
    
    __table_args__ = (
        {"comment": "Commission plans with HYBRID basis support"}
    )
    
    def __repr__(self):
        return f"<CommissionPlan(code={self.plan_code}, basis={self.basis.value})>"


class CommissionRule(BaseModel):
    """Commission rule (tier-based)"""
    __tablename__ = "commission_rule"
    
    commission_plan_id = Column(UUID(as_uuid=True), ForeignKey("commission_plan.id"), nullable=False, index=True)
    applies_to = Column(String(50))  # ROLE, EMPLOYEE, TEAM
    role = Column(String(100))  # If applies_to is ROLE
    employee_id = Column(UUID(as_uuid=True), ForeignKey("hr_employee.id"), nullable=True)
    sku_filter = Column(Text)  # JSON filter for products/SKUs
    tier_from = Column(Numeric(15, 2), nullable=True)  # Revenue threshold from
    tier_to = Column(Numeric(15, 2), nullable=True)  # Revenue threshold to
    recognized_rate = Column(Numeric(10, 4), default=Decimal("0.00"), nullable=False)
    collected_rate = Column(Numeric(10, 4), default=Decimal("0.00"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    plan = relationship("CommissionPlan", back_populates="rules")
    employee = relationship("HREmployee")
    
    __table_args__ = (
        {"comment": "Commission rules with tiers and filters"}
    )
    
    def __repr__(self):
        return f"<CommissionRule(plan={self.commission_plan_id}, tier={self.tier_from}-{self.tier_to})>"


class CommissionLedger(BaseModel):
    """Commission ledger (accrued commissions)"""
    __tablename__ = "commission_ledger"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    commission_plan_id = Column(UUID(as_uuid=True), ForeignKey("commission_plan.id"), nullable=False, index=True)
    hr_employee_id = Column(UUID(as_uuid=True), ForeignKey("hr_employee.id"), nullable=False, index=True)
    period_start = Column(Date, nullable=False, index=True)
    period_end = Column(Date, nullable=False, index=True)
    recognized_revenue_base = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    collected_revenue_base = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    recognized_commission = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    collected_commission = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_commission = Column(Numeric(15, 2), nullable=False)  # Sum of recognized + collected
    currency = Column(String(3), nullable=False)
    is_paid = Column(Boolean, default=False, nullable=False, index=True)
    paid_at = Column(Date, nullable=True)
    payroll_run_id = Column(UUID(as_uuid=True), ForeignKey("payroll_run.id"), nullable=True)  # If paid via payroll
    
    # Relationships
    entity = relationship("LegalEntity")
    plan = relationship("CommissionPlan", back_populates="ledger_entries")
    employee = relationship("HREmployee", back_populates="commission_ledger")
    payroll_run = relationship("PayrollRun")
    
    __table_args__ = (
        {"comment": "Commission ledger - accrued commissions per period"}
    )
    
    def __repr__(self):
        return f"<CommissionLedger(employee={self.hr_employee_id}, period={self.period_start}, total={self.total_commission}, paid={self.is_paid})>"
