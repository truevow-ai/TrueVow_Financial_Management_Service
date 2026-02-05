"""Journal Entry Models"""
from sqlalchemy import Column, String, Date, DateTime, Integer, ForeignKey, Enum as SQLEnum, Numeric, Text, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class JournalEntryStatus(str, enum.Enum):
    """Journal entry status"""
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    REVERSED = "REVERSED"


class JournalEntry(BaseModel):
    """Journal entry model"""
    __tablename__ = "journal_entry"
    
    # Entity/Book context (entity_id for source_key uniqueness constraint)
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("book.id"), nullable=False, index=True)
    period_id = Column(UUID(as_uuid=True), ForeignKey("accounting_period.id"), nullable=False, index=True)
    entry_number = Column(String(100), unique=True, nullable=False, index=True)
    entry_date = Column(Date, nullable=False, index=True)
    description = Column(Text)
    reference_number = Column(String(255))
    status = Column(SQLEnum(JournalEntryStatus), default=JournalEntryStatus.DRAFT, nullable=False, index=True)
    
    # Source tracking
    source_service = Column(String(50))  # billing, treasury, fm, payroll, ap, manual
    source_type = Column(String(100))  # invoice_issued, payout_received, payroll_run_posted, etc.
    source_id = Column(UUID(as_uuid=True))  # External or internal ID
    idempotency_key = Column(String(255), unique=True, nullable=True, index=True)
    source_key = Column(String(255), nullable=True, index=True)  # Deterministic posting key (e.g., "JE:POST:{entry_id}")
    
    # Reversal tracking
    reversed_by_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entry.id"), nullable=True)
    reversal_reason = Column(Text, nullable=True)
    
    # Posting metadata
    posted_by = Column(UUID(as_uuid=True), nullable=True)
    posted_at = Column(Date, nullable=True)
    
    # Relationships
    book = relationship("Book", back_populates="journal_entries")
    period = relationship("AccountingPeriod", back_populates="journal_entries")
    lines = relationship("JournalLine", back_populates="journal_entry", cascade="all, delete-orphan")
    # Dimensions live on JournalLine.dimensions; no direct JournalEntry->JournalLineDimension FK
    __table_args__ = (
        UniqueConstraint("legal_entity_id", "book_id", "source_key", name="uq_journal_entry_entity_book_source"),
        {"comment": "Journal entries - immutable after posting"},
    )
    
    def __repr__(self):
        return f"<JournalEntry(number={self.entry_number}, status={self.status.value}, date={self.entry_date})>"


JournalEntry.reversed_entry = relationship(
    "JournalEntry",
    foreign_keys=[JournalEntry.reversed_by_entry_id],
    remote_side=[JournalEntry.id],
    backref="reverses",
)


class JournalLine(BaseModel):
    """Journal entry line model"""
    __tablename__ = "journal_line"
    
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entry.id"), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("book.id"), nullable=False, index=True)
    gl_account_id = Column(UUID(as_uuid=True), ForeignKey("gl_account.id"), nullable=False, index=True)
    line_number = Column(Integer, nullable=False)
    
    # Transaction currency amounts
    debit_tc = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    credit_tc = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    currency = Column(String(3), nullable=False)  # Transaction currency
    
    # Functional currency amounts
    debit_fc = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    credit_fc = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    
    # FX information
    fx_rate = Column(Numeric(15, 6), nullable=True)
    fx_source = Column(String(100), nullable=True)  # api, manual, etc.
    fx_timestamp = Column(DateTime(timezone=True), nullable=True)
    
    description = Column(Text)
    
    # Relationships
    journal_entry = relationship("JournalEntry", back_populates="lines")
    book = relationship("Book")
    account = relationship("GLAccount", back_populates="journal_lines")
    dimensions = relationship("JournalLineDimension", back_populates="journal_line", cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("journal_entry_id", "line_number", name="uq_journal_line_entry_line"),
        CheckConstraint("debit_tc >= 0 AND credit_tc >= 0", name="ck_journal_line_non_neg"),
        CheckConstraint("(debit_tc > 0 AND credit_tc = 0) OR (debit_tc = 0 AND credit_tc > 0)", name="ck_journal_line_dr_or_cr"),
        {"comment": "Journal entry lines - must balance (debits == credits)"},
    )
    
    def __repr__(self):
        return f"<JournalLine(entry_id={self.journal_entry_id}, account={self.gl_account_id}, dr={self.debit_fc}, cr={self.credit_fc})>"


class JournalLineDimension(BaseModel):
    """Journal line dimension (tag) association"""
    __tablename__ = "journal_line_dimension"
    
    journal_line_id = Column(UUID(as_uuid=True), ForeignKey("journal_line.id"), nullable=False, index=True)
    dimension_value_id = Column(UUID(as_uuid=True), ForeignKey("dimension_value.id"), nullable=False, index=True)
    
    # Relationships
    journal_line = relationship("JournalLine", back_populates="dimensions")
    dimension_value = relationship("DimensionValue")
    
    __table_args__ = (
        UniqueConstraint("journal_line_id", "dimension_value_id", name="uq_journal_line_dim_line_dim"),
        {"comment": "Dimensions (tags) attached to journal lines"},
    )
    
    def __repr__(self):
        return f"<JournalLineDimension(line_id={self.journal_line_id}, dimension_value_id={self.dimension_value_id})>"
