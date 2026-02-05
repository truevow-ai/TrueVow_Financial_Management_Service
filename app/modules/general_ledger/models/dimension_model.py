"""Dimension Models"""
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.shared.models.base_model import BaseModel


class Dimension(BaseModel):
    """Dimension (tag category) model"""
    __tablename__ = "dimension"
    
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    
    # Relationships
    values = relationship("DimensionValue", back_populates="dimension", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Dimension(code={self.code}, name={self.name})>"


class DimensionValue(BaseModel):
    """Dimension value model"""
    __tablename__ = "dimension_value"
    
    dimension_code = Column(String(50), ForeignKey("dimension.code"), nullable=False, index=True)
    value_code = Column(String(50), nullable=False)
    value_name = Column(String(255), nullable=False)
    
    # Relationships
    dimension = relationship("Dimension", back_populates="values")
    
    __table_args__ = (
        {"comment": "Values for each dimension (e.g., COST_CENTER: DEV, SALES, GNA)"}
    )
    
    def __repr__(self):
        return f"<DimensionValue(dimension={self.dimension_code}, value={self.value_code})>"
