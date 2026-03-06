"""AP Bill Models"""
from sqlalchemy import Column, String, Date, Integer, ForeignKey, Numeric, Text, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class BillStatus(str, enum.Enum):
    """AP Bill status"""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    POSTED = "POSTED"
    CANCELLED = "CANCELLED"


class APBill(BaseModel):
    """AP Bill model (vendor invoice)"""
    __tablename__ = "ap_bill"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("book.id"), nullable=False, index=True)
    ap_vendor_id = Column(UUID(as_uuid=True), ForeignKey("ap_vendor.id"), nullable=False, index=True)
    bill_number = Column(String(100), unique=True, nullable=False, index=True)
    bill_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=True, index=True)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(SQLEnum(BillStatus), default=BillStatus.DRAFT, nullable=False, index=True)
    paid_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    outstanding_amount = Column(Numeric(15, 2), nullable=False)  # total_amount - paid_amount
    description = Column(Text)
    reference_number = Column(String(255))  # Vendor invoice number
    
    # Withholding
    withholding_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    withholding_profile_id = Column(UUID(as_uuid=True), ForeignKey("ap_withholding_profile.id"), nullable=True)
    
    # Approval workflow fields
    submitted_by = Column(UUID(as_uuid=True), nullable=True)
    submitted_at = Column(Date, nullable=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(Date, nullable=True)
    rejected_by = Column(UUID(as_uuid=True), nullable=True)
    rejected_at = Column(Date, nullable=True)
    decision_reason = Column(Text, nullable=True)
    posted_by = Column(UUID(as_uuid=True), nullable=True)
    posted_at = Column(Date, nullable=True)
    
    # Posting
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entry.id"), nullable=True)
    
    # Relationships
    entity = relationship("LegalEntity")
    book = relationship("Book")
    vendor = relationship("APVendor", back_populates="bills")
    withholding_profile = relationship("APWithholdingProfile", back_populates="bills")
    lines = relationship("APBillLine", back_populates="bill", cascade="all, delete-orphan")
    allocations = relationship("APAllocation", back_populates="bill", cascade="all, delete-orphan")
    # Payments linked via allocations; use bill.allocations then a.payment
    journal_entry = relationship("JournalEntry")
    
    __table_args__ = (
        {"comment": "AP bills (vendor invoices)"}
    )
    
    def __repr__(self):
        return f"<APBill(number={self.bill_number}, amount={self.total_amount}, status={self.status.value})>"


class APBillLine(BaseModel):
    """AP Bill line model"""
    __tablename__ = "ap_bill_line"
    
    ap_bill_id = Column(UUID(as_uuid=True), ForeignKey("ap_bill.id"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    gl_account_id = Column(UUID(as_uuid=True), ForeignKey("gl_account.id"), nullable=False, index=True)
    description = Column(Text)
    quantity = Column(Numeric(10, 2), default=Decimal("1.00"), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    line_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    
    # Tax (optional for future)
    tax_code = Column(String(50), nullable=True)
    
    # Relationships
    bill = relationship("APBill", back_populates="lines")
    gl_account = relationship("GLAccount")
    
    __table_args__ = (
        UniqueConstraint("ap_bill_id", "line_number", name="uq_ap_bill_line_bill_line"),
        {"comment": "AP bill line items"},
    )
    
    def __repr__(self):
        return f"<APBillLine(bill_id={self.ap_bill_id}, line={self.line_number}, amount={self.line_amount})>"
