"""Pay Group Model"""
from sqlalchemy import Column, String, ForeignKey, Enum as SQLEnum, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.shared.models.base_model import BaseModel


class PayFrequency(str, enum.Enum):
    """Pay frequency"""
    MONTHLY = "MONTHLY"
    BIWEEKLY = "BIWEEKLY"
    WEEKLY = "WEEKLY"


class PayDayRule(str, enum.Enum):
    """Pay day rule"""
    LAST_BUSINESS_DAY = "LAST_BUSINESS_DAY"
    FIRST_BUSINESS_DAY = "FIRST_BUSINESS_DAY"
    FIXED_DAY = "FIXED_DAY"  # e.g., 25th of month
    MONTHLY_DAY_5 = "MONTHLY_DAY_5"


class PayGroup(BaseModel):
    """Pay group model"""
    __tablename__ = "pay_group"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    group_code = Column(String(50), unique=True, nullable=False, index=True)
    group_name = Column(String(255), nullable=False)
    frequency = Column(SQLEnum(PayFrequency), default=PayFrequency.MONTHLY, nullable=False)
    payroll_currency = Column(String(3), nullable=False)
    pay_day_rule = Column(SQLEnum(PayDayRule), default=PayDayRule.LAST_BUSINESS_DAY, nullable=False)
    wps_enabled = Column(Boolean, default=False, nullable=False)  # UAE WPS support
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    entity = relationship("LegalEntity")
    employees = relationship("HREmployee", back_populates="pay_group")
    payroll_runs = relationship("PayrollRun", back_populates="pay_group")
    
    __table_args__ = (
        {"comment": "Pay groups for payroll processing"}
    )
    
    def __repr__(self):
        return f"<PayGroup(code={self.group_code}, frequency={self.frequency.value}, currency={self.payroll_currency})>"
