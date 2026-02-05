"""Chart of Accounts Models"""
from sqlalchemy import Column, String, ForeignKey, Boolean, Enum as SQLEnum, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.shared.models.base_model import BaseModel


class AccountType(str, enum.Enum):
    """Account type enumeration"""
    ASSET = "ASSET"
    LIABILITY = "LIABILITY"
    EQUITY = "EQUITY"
    REVENUE = "REVENUE"
    EXPENSE = "EXPENSE"
    # Special types
    AR = "AR"  # Accounts Receivable
    AP = "AP"  # Accounts Payable
    CASH = "CASH"
    DEFERRED_REVENUE = "DEFERRED_REVENUE"
    OTHER_ASSET = "OTHER_ASSET"
    OTHER_LIABILITY = "OTHER_LIABILITY"
    OTHER_INCOME = "OTHER_INCOME"
    OTHER_INCOME_EXPENSE = "OTHER_INCOME_EXPENSE"
    CONTRA_REVENUE = "CONTRA_REVENUE"


class GLAccount(BaseModel):
    """Chart of Accounts - GL Account model"""
    __tablename__ = "gl_account"
    
    book_id = Column(UUID(as_uuid=True), ForeignKey("book.id"), nullable=False, index=True)
    account_code = Column(String(50), nullable=False)
    account_name = Column(String(255), nullable=False)
    account_type = Column(SQLEnum(AccountType), nullable=False)
    parent_account_id = Column(UUID(as_uuid=True), ForeignKey("gl_account.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    description = Column(String(500))
    
    # Relationships
    book = relationship("Book", back_populates="accounts")
    journal_lines = relationship("JournalLine", back_populates="account")
    mappings = relationship("GLAccountMapping", back_populates="account")
    
    __table_args__ = (
        {"comment": "Chart of Accounts - GL accounts per book"}
    )
    
    def __repr__(self):
        return f"<GLAccount(code={self.account_code}, name={self.account_name}, type={self.account_type.value})>"


GLAccount.parent_account = relationship(
    "GLAccount",
    foreign_keys=[GLAccount.parent_account_id],
    remote_side=[GLAccount.id],
    backref="child_accounts",
)


class GLAccountMapping(BaseModel):
    """GL Account mapping for system postings"""
    __tablename__ = "gl_account_mapping"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("book.id"), nullable=False, index=True)
    map_key = Column(String(100), nullable=False)  # e.g., "AR", "AP", "PAYROLL_PAYABLE"
    gl_account_id = Column(UUID(as_uuid=True), ForeignKey("gl_account.id"), nullable=False)
    
    # Relationships
    account = relationship("GLAccount", back_populates="mappings")
    
    __table_args__ = (
        UniqueConstraint("legal_entity_id", "book_id", "map_key", name="uq_gl_account_mapping_entity_book_key"),
        {"comment": "Mapping keys to GL accounts for system-generated postings"},
    )
    
    def __repr__(self):
        return f"<GLAccountMapping(map_key={self.map_key}, account_id={self.gl_account_id})>"
