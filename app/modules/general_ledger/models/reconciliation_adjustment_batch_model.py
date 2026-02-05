"""Reconciliation Adjustment Batch Model"""
from sqlalchemy import Column, String, ForeignKey, Numeric, Enum as SQLEnum, Text, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class AdjustmentBatchStatus(str, enum.Enum):
    """Reconciliation adjustment batch status"""
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    POSTED = "POSTED"
    REJECTED = "REJECTED"


class ReconciliationAdjustmentBatch(BaseModel):
    """Represents accounting adjustments created during reconciliation that will be posted as JEs"""
    __tablename__ = "reconciliation_adjustment_batch"
    
    reconciliation_session_id = Column(UUID(as_uuid=True), ForeignKey("reconciliation_session.id"), nullable=False, index=True)
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("book.id"), nullable=False, index=True)
    batch_number = Column(String(100), unique=True, nullable=False, index=True)
    total_amount = Column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    currency = Column(String(3), nullable=False)
    status = Column(SQLEnum(AdjustmentBatchStatus), default=AdjustmentBatchStatus.DRAFT, nullable=False, index=True)
    # Approval fields
    submitted_by = Column(UUID(as_uuid=True), nullable=True)
    submitted_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(UUID(as_uuid=True), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_by = Column(UUID(as_uuid=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    decision_reason = Column(Text, nullable=True)
    row_version = Column(Integer, default=1, nullable=False)
    # Posting fields
    posted_by = Column(UUID(as_uuid=True), nullable=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entry.id"), nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    reconciliation_session = relationship("ReconciliationSession", backref="adjustment_batches")
    entity = relationship("LegalEntity")
    book = relationship("Book")
    journal_entry = relationship("JournalEntry")
    
    __table_args__ = (
        {"comment": "Reconciliation adjustment batches requiring approval before posting"},
    )
    
    def __repr__(self):
        return f"<ReconciliationAdjustmentBatch(batch={self.batch_number}, status={self.status.value}, amount={self.total_amount})>"
