"""Pay Component Models"""
from sqlalchemy import Column, String, ForeignKey, Boolean, Enum as SQLEnum, Numeric, UniqueConstraint, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class ComponentType(str, enum.Enum):
    """Pay component type"""
    EARNING = "EARNING"
    DEDUCTION = "DEDUCTION"
    EMPLOYER_CONTRIBUTION = "EMPLOYER_CONTRIBUTION"


class ComponentCode(str, enum.Enum):
    """Standard component codes"""
    # Earnings
    BASIC = "BASIC"
    HOUSING = "HOUSING"
    TRANSPORT = "TRANSPORT"
    OVERTIME = "OVERTIME"
    COMMISSION = "COMMISSION"
    BONUS = "BONUS"
    REIMBURSEMENT = "REIMBURSEMENT"
    # Deductions
    TAX_WITHHOLDING = "TAX_WITHHOLDING"
    BENEFIT_EMP = "BENEFIT_EMP"
    LOAN_DEDUCT = "LOAN_DEDUCT"
    ADVANCE_DEDUCT = "ADVANCE_DEDUCT"
    # Employer Contributions
    GPSSA_EMPR = "GPSSA_EMPR"
    EOBI_EMPR = "EOBI_EMPR"
    SOCIALSEC_EMPR = "SOCIALSEC_EMPR"


class PayComponentDefinition(BaseModel):
    """Pay component definition"""
    __tablename__ = "pay_component_definition"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    component_code = Column(String(50), nullable=False, index=True)
    component_name = Column(String(255), nullable=False)
    component_type = Column(SQLEnum(ComponentType), nullable=False)
    is_taxable = Column(Boolean, default=True, nullable=False)
    affects_wps_net = Column(Boolean, default=True, nullable=False)  # Affects WPS net pay calculation
    gl_map_key = Column(String(100))  # GL account mapping key
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    entity = relationship("LegalEntity")
    assignments = relationship("PayComponentAssignment", back_populates="component", cascade="all, delete-orphan")
    run_lines = relationship("PayrollRunComponentLine", back_populates="component")
    
    __table_args__ = (
        UniqueConstraint("legal_entity_id", "component_code", name="uq_pay_component_entity_code"),
        {"comment": "Pay component definitions (earnings, deductions, employer contributions)"},
    )
    
    def __repr__(self):
        return f"<PayComponentDefinition(code={self.component_code}, name={self.component_name}, type={self.component_type.value})>"


class PayComponentAssignment(BaseModel):
    """Pay component assignment to employee"""
    __tablename__ = "pay_component_assignment"
    
    hr_employee_id = Column(UUID(as_uuid=True), ForeignKey("hr_employee.id"), nullable=False, index=True)
    pay_component_id = Column(UUID(as_uuid=True), ForeignKey("pay_component_definition.id"), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=True)  # Fixed amount (if applicable)
    rate = Column(Numeric(10, 4), nullable=True)  # Percentage rate (if applicable)
    is_active = Column(Boolean, default=True, nullable=False)
    effective_from = Column(Date, nullable=True)
    effective_to = Column(Date, nullable=True)
    
    # Relationships
    employee = relationship("HREmployee", back_populates="component_assignments")
    component = relationship("PayComponentDefinition", back_populates="assignments")
    
    __table_args__ = (
        UniqueConstraint("hr_employee_id", "pay_component_id", name="uq_pay_component_assignment_emp_comp"),
        {"comment": "Pay component assignments to employees"},
    )
    
    def __repr__(self):
        return f"<PayComponentAssignment(employee={self.hr_employee_id}, component={self.pay_component_id})>"
