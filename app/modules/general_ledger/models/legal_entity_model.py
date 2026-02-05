"""Legal Entity Model"""
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from app.shared.models.base_model import BaseModel


class LegalEntity(BaseModel):
    """Legal entity (company) model"""
    __tablename__ = "legal_entity"
    
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    country = Column(String(10), nullable=False)
    functional_currency = Column(String(3), nullable=False)  # USD, AED, PKR
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    books = relationship("Book", back_populates="entity", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<LegalEntity(code={self.code}, name={self.name})>"
