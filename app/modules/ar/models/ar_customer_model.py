"""AR Customer Model"""
from sqlalchemy import Column, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.shared.models.base_model import BaseModel


class ARCustomer(BaseModel):
    """AR Customer model (mapped from Billing customer)"""
    __tablename__ = "ar_customer"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    external_customer_id = Column(String(255), unique=True, nullable=False, index=True)  # Billing customer ID
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255))
    customer_code = Column(String(100))
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    entity = relationship("LegalEntity")
    invoices = relationship("ARInvoice", back_populates="customer", cascade="all, delete-orphan")
    payments = relationship("ARPayment", back_populates="customer", cascade="all, delete-orphan")
    
    __table_args__ = (
        {"comment": "AR customers mapped from Billing service"}
    )
    
    def __repr__(self):
        return f"<ARCustomer(name={self.customer_name}, external_id={self.external_customer_id})>"
