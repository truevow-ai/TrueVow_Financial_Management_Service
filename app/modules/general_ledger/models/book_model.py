"""Book Model"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from sqlalchemy.dialects.postgresql import UUID
from app.shared.models.base_model import BaseModel


class BookType(str, enum.Enum):
    """Book type enumeration"""
    ACCRUAL = "ACCRUAL"
    CASH = "CASH"


class Book(BaseModel):
    """Accounting book model (ACCRUAL or CASH per entity)"""
    __tablename__ = "book"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    book_type = Column(SQLEnum(BookType), nullable=False)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    entity = relationship("LegalEntity", back_populates="books")
    accounts = relationship("GLAccount", back_populates="book", cascade="all, delete-orphan")
    periods = relationship("AccountingPeriod", back_populates="book", cascade="all, delete-orphan")
    journal_entries = relationship("JournalEntry", back_populates="book", cascade="all, delete-orphan")
    
    __table_args__ = (
        {"comment": "Accounting books (ACCRUAL or CASH) per legal entity"}
    )
    
    def __repr__(self):
        return f"<Book(entity={self.legal_entity_id}, type={self.book_type.value})>"
