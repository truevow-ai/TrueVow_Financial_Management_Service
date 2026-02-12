"""Bonus Models"""
from sqlalchemy import Column, String, Date, ForeignKey, Numeric, Enum as SQLEnum, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class BonusType(str, enum.Enum):
    """Bonus type"""
    ONE_TIME = "ONE_TIME"
    PERIODIC = "PERIODIC"


class BonusPlan(BaseModel):
    """Bonus plan model"""
    __tablename__ = "bonus_plan"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    plan_code = Column(String(50), unique=True, nullable=False, index=True)
    plan_name = Column(String(255), nullable=False)
    bonus_type = Column(SQLEnum(BonusType), default=BonusType.ONE_TIME, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    entity = relationship("LegalEntity")
    results = relationship("BonusResult", back_populates="plan", cascade="all, delete-orphan")
    
    __table_args__ = (
        {"comment": "Bonus plans"}
    )
    
    def __repr__(self):
        return f"<BonusPlan(code={self.plan_code}, type={self.bonus_type.value})>"


class BonusResult(BaseModel):
    """Bonus result (awarded bonus)"""
    __tablename__ = "bonus_result"
    
    bonus_plan_id = Column(UUID(as_uuid=True), ForeignKey("bonus_plan.id"), nullable=False, index=True)
    hr_employee_id = Column(UUID(as_uuid=True), ForeignKey("hr_employee.id"), nullable=False, index=True)
    bonus_date = Column(Date, nullable=False, index=True)
    bonus_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    description = Column(Text, nullable=True)
    is_paid = Column(Boolean, default=False, nullable=False, index=True)
    paid_at = Column(Date, nullable=True)
    payroll_run_id = Column(UUID(as_uuid=True), ForeignKey("payroll_run.id"), nullable=True)
    
    # Relationships
    plan = relationship("BonusPlan", back_populates="results")
    employee = relationship("HREmployee")
    payroll_run = relationship("PayrollRun")
    
    __table_args__ = (
        {"comment": "Bonus results - awarded bonuses"}
    )
    
    def __repr__(self):
        return f"<BonusResult(employee={self.hr_employee_id}, amount={self.bonus_amount}, paid={self.is_paid})>"
