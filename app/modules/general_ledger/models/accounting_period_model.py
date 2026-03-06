"""Accounting Period Model"""
from sqlalchemy import Column, Date, DateTime, Integer, String, ForeignKey, Enum as SQLEnum, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.shared.models.base_model import BaseModel


class PeriodStatus(str, enum.Enum):
    """Accounting period status"""
    OPEN = "OPEN"
    SOFT_CLOSED = "SOFT_CLOSED"
    PENDING_CLOSE_APPROVAL = "PENDING_CLOSE_APPROVAL"
    CLOSED = "CLOSED"
    LOCKED = "LOCKED"


class AccountingPeriod(BaseModel):
    """Accounting period model (monthly)"""
    __tablename__ = "accounting_period"
    
    book_id = Column(UUID(as_uuid=True), ForeignKey("book.id"), nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    period_name = Column(String(50), nullable=False)  # e.g., "2025-01", "Jan 2025"
    status = Column(SQLEnum(PeriodStatus), default=PeriodStatus.OPEN, nullable=False, index=True)
    # Approval fields for period close
    submitted_by = Column(UUID(as_uuid=True), nullable=True)  # User who submitted close request
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)  # User who approved close
    approved_at = Column(DateTime(timezone=True), nullable=True)
    decision_reason = Column(Text, nullable=True)  # Reason for approval/rejection
    # Legacy fields (kept for backward compatibility)
    closed_by = Column(UUID(as_uuid=True), nullable=True)  # User who closed it (maps to approved_by)
    closed_at = Column(DateTime(timezone=True), nullable=True)  # When closed (maps to approved_at)
    lock_reason = Column(String(500), nullable=True)  # Reason for locking
    
    # Relationships
    book = relationship("Book", back_populates="periods")
    journal_entries = relationship("JournalEntry", back_populates="period")
    
    __table_args__ = (
        UniqueConstraint("book_id", "period_start", name="uq_accounting_period_book_start"),
        {"comment": "Monthly accounting periods per book"},
    )
    
    def __repr__(self):
        return f"<AccountingPeriod(book_id={self.book_id}, period={self.period_name}, status={self.status.value})>"
