"""AP Withholding Profile Model"""
from sqlalchemy import Column, String, ForeignKey, Numeric, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class APWithholdingProfile(BaseModel):
    """AP Withholding tax profile"""
    __tablename__ = "ap_withholding_profile"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    profile_name = Column(String(255), nullable=False)
    withholding_type = Column(String(50))  # tax, vat, etc.
    withholding_rate = Column(Numeric(5, 2), nullable=False)  # Percentage
    gl_account_id = Column(UUID(as_uuid=True), ForeignKey("gl_account.id"), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(String(500))
    
    # Relationships
    entity = relationship("LegalEntity")
    gl_account = relationship("GLAccount")
    bills = relationship("APBill", back_populates="withholding_profile")
    
    __table_args__ = (
        {"comment": "AP withholding tax profiles (optional)"}
    )
    
    def __repr__(self):
        return f"<APWithholdingProfile(name={self.profile_name}, rate={self.withholding_rate}%)>"
