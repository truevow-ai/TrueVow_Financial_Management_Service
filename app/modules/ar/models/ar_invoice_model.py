"""AR Invoice Models"""
from sqlalchemy import Column, String, Date, Integer, ForeignKey, Numeric, Text, Enum as SQLEnum, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class InvoiceStatus(str, enum.Enum):
    """Invoice status"""
    DRAFT = "DRAFT"
    ISSUED = "ISSUED"
    PAID = "PAID"
    PARTIALLY_PAID = "PARTIALLY_PAID"
    OVERDUE = "OVERDUE"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class ARInvoice(BaseModel):
    """AR Invoice model (mapped from Billing invoice)"""
    __tablename__ = "ar_invoice"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    ar_customer_id = Column(UUID(as_uuid=True), ForeignKey("ar_customer.id"), nullable=False, index=True)
    external_invoice_id = Column(String(255), unique=True, nullable=False, index=True)  # Billing invoice ID
    invoice_number = Column(String(100), unique=True, nullable=False, index=True)
    invoice_date = Column(Date, nullable=False, index=True)
    due_date = Column(Date, nullable=True, index=True)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(SQLEnum(InvoiceStatus), default=InvoiceStatus.ISSUED, nullable=False, index=True)
    paid_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    outstanding_amount = Column(Numeric(15, 2), nullable=False)  # total_amount - paid_amount
    description = Column(Text)
    external_data = Column(Text)  # JSON blob for additional Billing data
    
    # Relationships
    entity = relationship("LegalEntity")
    customer = relationship("ARCustomer", back_populates="invoices")
    lines = relationship("ARInvoiceLine", back_populates="invoice", cascade="all, delete-orphan")
    allocations = relationship("ARAllocation", back_populates="invoice", cascade="all, delete-orphan")
    # Payments linked via allocations (no direct FK); use invoice.allocations then a.payment
    
    __table_args__ = (
        {"comment": "AR invoices synced from Billing service"}
    )
    
    def __repr__(self):
        return f"<ARInvoice(number={self.invoice_number}, amount={self.total_amount}, status={self.status.value})>"


class ARInvoiceLine(BaseModel):
    """AR Invoice line model"""
    __tablename__ = "ar_invoice_line"
    
    ar_invoice_id = Column(UUID(as_uuid=True), ForeignKey("ar_invoice.id"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    description = Column(Text)
    quantity = Column(Numeric(10, 2), default=Decimal("1.00"), nullable=False)
    unit_price = Column(Numeric(15, 2), nullable=False)
    line_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    
    # Service period metadata (for deferred revenue)
    service_start = Column(Date, nullable=True)
    service_end = Column(Date, nullable=True)
    is_deferrable = Column(Boolean, default=False, nullable=False)  # Subscription/service period line
    
    # Relationships
    invoice = relationship("ARInvoice", back_populates="lines")
    
    __table_args__ = (
        UniqueConstraint("ar_invoice_id", "line_number", name="uq_ar_invoice_line_invoice_line"),
        {"comment": "AR invoice line items"},
    )
    
    def __repr__(self):
        return f"<ARInvoiceLine(invoice_id={self.ar_invoice_id}, line={self.line_number}, amount={self.line_amount})>"
