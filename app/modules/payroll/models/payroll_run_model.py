"""Payroll Run Models"""
from sqlalchemy import Column, String, Date, DateTime, Integer, ForeignKey, Numeric, Enum as SQLEnum, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class PayrollRunStatus(str, enum.Enum):
    """Payroll run status"""
    DRAFT = "DRAFT"
    CALCULATED = "CALCULATED"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    POSTED = "POSTED"
    PAID = "PAID"
    CLOSED = "CLOSED"
    REJECTED = "REJECTED"
    REVERSED = "REVERSED"


class PayrollRun(BaseModel):
    """Payroll run model"""
    __tablename__ = "payroll_run"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("book.id"), nullable=False, index=True)
    pay_group_id = Column(UUID(as_uuid=True), ForeignKey("pay_group.id"), nullable=False, index=True)
    run_number = Column(String(100), unique=True, nullable=False, index=True)
    pay_period_start = Column(Date, nullable=False, index=True)
    pay_period_end = Column(Date, nullable=False, index=True)
    pay_date = Column(Date, nullable=False, index=True)
    status = Column(SQLEnum(PayrollRunStatus), default=PayrollRunStatus.DRAFT, nullable=False, index=True)
    total_gross = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_deductions = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_net = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_employer_contrib = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    currency = Column(String(3), nullable=False)
    # Approval fields
    submitted_by = Column(UUID(as_uuid=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(UUID(as_uuid=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    decision_reason = Column(Text, nullable=True)  # Required on reject, optional on approve
    # Posting fields
    posted_by = Column(UUID(as_uuid=True), nullable=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entry.id"), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    entity = relationship("LegalEntity")
    book = relationship("Book")
    pay_group = relationship("PayGroup", back_populates="payroll_runs")
    items = relationship("PayrollRunItem", back_populates="payroll_run", cascade="all, delete-orphan")
    payment_batches = relationship("PayrollPaymentBatch", back_populates="payroll_run", cascade="all, delete-orphan")
    journal_entry = relationship("JournalEntry")
    
    __table_args__ = (
        {"comment": "Payroll runs - immutable after posting"}
    )
    
    def __repr__(self):
        return f"<PayrollRun(number={self.run_number}, period={self.pay_period_start} to {self.pay_period_end}, status={self.status.value})>"


class PayrollRunItem(BaseModel):
    """Payroll run item (per employee)"""
    __tablename__ = "payroll_run_item"
    
    payroll_run_id = Column(UUID(as_uuid=True), ForeignKey("payroll_run.id"), nullable=False, index=True)
    hr_employee_id = Column(UUID(as_uuid=True), ForeignKey("hr_employee.id"), nullable=False, index=True)
    gross_pay = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_deductions = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    net_pay = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    employer_contributions = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    currency = Column(String(3), nullable=False)
    
    # Relationships
    payroll_run = relationship("PayrollRun", back_populates="items")
    employee = relationship("HREmployee", back_populates="payroll_runs")
    component_lines = relationship("PayrollRunComponentLine", back_populates="run_item", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("payroll_run_id", "hr_employee_id", name="uq_payroll_run_item_run_emp"),
        {"comment": "Payroll run items per employee"},
    )
    
    def __repr__(self):
        return f"<PayrollRunItem(run={self.payroll_run_id}, employee={self.hr_employee_id}, net={self.net_pay})>"


class PayrollRunComponentLine(BaseModel):
    """Payroll run component line (detailed breakdown)"""
    __tablename__ = "payroll_run_component_line"
    
    payroll_run_item_id = Column(UUID(as_uuid=True), ForeignKey("payroll_run_item.id"), nullable=False, index=True)
    pay_component_id = Column(UUID(as_uuid=True), ForeignKey("pay_component_definition.id"), nullable=False, index=True)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    calculation_note = Column(Text, nullable=True)  # How this was calculated
    
    # Relationships
    run_item = relationship("PayrollRunItem", back_populates="component_lines")
    component = relationship("PayComponentDefinition", back_populates="run_lines")
    
    __table_args__ = (
        {"comment": "Detailed component lines for payroll run items"}
    )
    
    def __repr__(self):
        return f"<PayrollRunComponentLine(item={self.payroll_run_item_id}, component={self.pay_component_id}, amount={self.amount})>"
