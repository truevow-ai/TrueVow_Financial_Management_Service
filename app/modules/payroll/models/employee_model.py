"""Employee Model"""
from sqlalchemy import Column, String, ForeignKey, Boolean, Date, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.shared.models.base_model import BaseModel


class EmployeeType(str, enum.Enum):
    """Employee type"""
    EMPLOYEE = "EMPLOYEE"
    CONTRACTOR = "CONTRACTOR"
    AFFILIATE = "AFFILIATE"


class HREmployee(BaseModel):
    """HR Employee model"""
    __tablename__ = "hr_employee"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    employee_code = Column(String(100), unique=True, nullable=False, index=True)
    employee_name = Column(String(255), nullable=False)
    employee_type = Column(SQLEnum(EmployeeType), default=EmployeeType.EMPLOYEE, nullable=False)
    country = Column(String(10), nullable=False)
    location = Column(String(50))  # UAE, Pakistan, Nevis
    pay_group_id = Column(UUID(as_uuid=True), ForeignKey("pay_group.id"), nullable=True, index=True)
    currency = Column(String(3), nullable=False)  # Payroll currency
    hire_date = Column(Date, nullable=True)
    termination_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # WPS fields (UAE)
    wps_enabled = Column(Boolean, default=False, nullable=False)
    labour_id = Column(String(100))  # UAE Labour ID
    mol_id = Column(String(100))  # UAE MOL ID
    iban = Column(String(50))  # Bank IBAN
    
    # Relationships
    entity = relationship("LegalEntity")
    pay_group = relationship("PayGroup", back_populates="employees")
    bank_details = relationship("HREmployeeBank", back_populates="employee", cascade="all, delete-orphan")
    component_assignments = relationship("PayComponentAssignment", back_populates="employee", cascade="all, delete-orphan")
    payroll_runs = relationship("PayrollRunItem", back_populates="employee", cascade="all, delete-orphan")
    commission_ledger = relationship("CommissionLedger", back_populates="employee")
    
    __table_args__ = (
        {"comment": "HR Employee master data"}
    )
    
    def __repr__(self):
        return f"<HREmployee(code={self.employee_code}, name={self.employee_name}, type={self.employee_type.value})>"


class HREmployeeBank(BaseModel):
    """Employee bank details"""
    __tablename__ = "hr_employee_bank"
    
    hr_employee_id = Column(UUID(as_uuid=True), ForeignKey("hr_employee.id"), nullable=False, index=True)
    bank_name = Column(String(255), nullable=False)
    account_number = Column(String(100))
    iban = Column(String(50))
    swift_code = Column(String(20))
    is_primary = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    employee = relationship("HREmployee", back_populates="bank_details")
    
    __table_args__ = (
        UniqueConstraint("hr_employee_id", "is_primary", name="uq_hr_employee_bank_emp_primary"),
        {"comment": "Employee bank account details"},
    )
    
    def __repr__(self):
        return f"<HREmployeeBank(employee={self.hr_employee_id}, bank={self.bank_name})>"
