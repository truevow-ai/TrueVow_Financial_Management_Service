"""AP Vendor Model"""
from sqlalchemy import Column, String, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.shared.models.base_model import BaseModel


class APVendor(BaseModel):
    """AP Vendor model"""
    __tablename__ = "ap_vendor"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    vendor_code = Column(String(100), unique=True, nullable=False, index=True)
    vendor_name = Column(String(255), nullable=False)
    vendor_type = Column(String(50))  # vendor, consultant, affiliate
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    tax_id = Column(String(100))  # VAT, tax registration number
    payment_terms = Column(String(100))  # Net 30, Net 15, etc.
    default_currency = Column(String(3), nullable=False)
    bank_name = Column(String(255))
    bank_account_number = Column(String(100))
    iban = Column(String(50))
    swift_code = Column(String(50))
    address = Column(Text)
    country = Column(String(10))
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    entity = relationship("LegalEntity")
    bills = relationship("APBill", back_populates="vendor", cascade="all, delete-orphan")
    payments = relationship("APPayment", back_populates="vendor", cascade="all, delete-orphan")
    
    __table_args__ = (
        {"comment": "AP vendors (vendors, consultants, affiliates)"}
    )
    
    def __repr__(self):
        return f"<APVendor(code={self.vendor_code}, name={self.vendor_name}, type={self.vendor_type})>"
