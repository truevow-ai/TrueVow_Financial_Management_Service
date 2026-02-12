"""AR Payment Models"""
from sqlalchemy import Column, String, Date, ForeignKey, Numeric, Text, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class PaymentStatus(str, enum.Enum):
    """Payment status"""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"


class ARPayment(BaseModel):
    """AR Payment model (mapped from Billing payment)"""
    __tablename__ = "ar_payment"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    ar_customer_id = Column(UUID(as_uuid=True), ForeignKey("ar_customer.id"), nullable=False, index=True)
    external_payment_id = Column(String(255), unique=True, nullable=False, index=True)  # Billing payment ID
    payment_date = Column(Date, nullable=False, index=True)
    payment_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    payment_method = Column(String(50))  # stripe, telr, bank_transfer, etc.
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.COMPLETED, nullable=False, index=True)
    reference_number = Column(String(255))
    description = Column(Text)
    external_data = Column(Text)  # JSON blob for additional Billing data
    
    # Relationships
    entity = relationship("LegalEntity")
    customer = relationship("ARCustomer", back_populates="payments")
    allocations = relationship("ARAllocation", back_populates="payment", cascade="all, delete-orphan")
    # Invoices linked via allocations (no direct FK); use payment.allocations then a.invoice
    
    __table_args__ = (
        {"comment": "AR payments synced from Billing service"}
    )
    
    def __repr__(self):
        return f"<ARPayment(external_id={self.external_payment_id}, amount={self.payment_amount}, status={self.status.value})>"


class ARAllocation(BaseModel):
    """AR Payment allocation to invoice"""
    __tablename__ = "ar_allocation"
    
    ar_payment_id = Column(UUID(as_uuid=True), ForeignKey("ar_payment.id"), nullable=False, index=True)
    ar_invoice_id = Column(UUID(as_uuid=True), ForeignKey("ar_invoice.id"), nullable=False, index=True)
    allocated_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    allocation_date = Column(Date, nullable=False)
    
    # Relationships
    payment = relationship("ARPayment", back_populates="allocations")
    invoice = relationship("ARInvoice", back_populates="allocations")
    
    __table_args__ = (
        UniqueConstraint("ar_payment_id", "ar_invoice_id", name="uq_ar_allocation_payment_invoice"),
        {"comment": "Payment allocations to invoices"},
    )
    
    def __repr__(self):
        return f"<ARAllocation(payment={self.ar_payment_id}, invoice={self.ar_invoice_id}, amount={self.allocated_amount})>"
