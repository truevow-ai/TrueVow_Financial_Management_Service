"""AP Payment Models"""
from sqlalchemy import Column, String, Date, ForeignKey, Numeric, Text, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class APPaymentStatus(str, enum.Enum):
    """AP Payment status"""
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    PROCESSED = "PROCESSED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class APPayment(BaseModel):
    """AP Payment model"""
    __tablename__ = "ap_payment"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("book.id"), nullable=False, index=True)
    ap_vendor_id = Column(UUID(as_uuid=True), ForeignKey("ap_vendor.id"), nullable=False, index=True)
    payment_number = Column(String(100), unique=True, nullable=False, index=True)
    payment_date = Column(Date, nullable=False, index=True)
    payment_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    payment_method = Column(String(50))  # check, wire, ach, bank_transfer
    payment_reference = Column(String(255))  # Check number, wire reference, etc.
    bank_account_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_account.id"), nullable=True)
    bank_transaction_id = Column(UUID(as_uuid=True), ForeignKey("treasury_bank_transaction.id"), nullable=True)
    status = Column(SQLEnum(APPaymentStatus), default=APPaymentStatus.PENDING, nullable=False, index=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(Date, nullable=True)
    processed_at = Column(Date, nullable=True)
    description = Column(Text)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entry.id"), nullable=True)
    
    # Relationships
    entity = relationship("LegalEntity")
    book = relationship("Book")
    vendor = relationship("APVendor", back_populates="payments")
    bank_account = relationship("BankAccount")
    bank_transaction = relationship("BankTransaction")
    allocations = relationship("APAllocation", back_populates="payment", cascade="all, delete-orphan")
    # Bills linked via allocations; use payment.allocations then a.bill
    journal_entry = relationship("JournalEntry")
    
    __table_args__ = (
        {"comment": "AP payments to vendors"}
    )
    
    def __repr__(self):
        return f"<APPayment(number={self.payment_number}, amount={self.payment_amount}, status={self.status.value})>"


class APAllocation(BaseModel):
    """AP Payment allocation to bill"""
    __tablename__ = "ap_allocation"
    
    ap_payment_id = Column(UUID(as_uuid=True), ForeignKey("ap_payment.id"), nullable=False, index=True)
    ap_bill_id = Column(UUID(as_uuid=True), ForeignKey("ap_bill.id"), nullable=False, index=True)
    allocated_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    allocation_date = Column(Date, nullable=False)
    
    # Relationships
    payment = relationship("APPayment", back_populates="allocations")
    bill = relationship("APBill", back_populates="allocations")
    
    __table_args__ = (
        UniqueConstraint("ap_payment_id", "ap_bill_id", name="uq_ap_allocation_payment_bill"),
        {"comment": "Payment allocations to bills"},
    )
    
    def __repr__(self):
        return f"<APAllocation(payment={self.ap_payment_id}, bill={self.ap_bill_id}, amount={self.allocated_amount})>"
