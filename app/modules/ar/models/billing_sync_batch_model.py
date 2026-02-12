"""Billing Sync Batch Model"""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func
import enum
from app.shared.models.base_model import BaseModel
from app.modules.general_ledger.models.treasury_sync_batch_model import SyncBatchStatus


class BillingSyncBatch(BaseModel):
    """Billing sync batch for tracking idempotent sync operations"""
    __tablename__ = "billing_sync_batch"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("book.id"), nullable=False, index=True)
    batch_number = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(SQLEnum(SyncBatchStatus), default=SyncBatchStatus.PENDING, nullable=False, index=True)
    
    # Sync metadata
    cursor_start = Column(String(255), nullable=True)  # Starting cursor for this batch
    cursor_end = Column(String(255), nullable=True)  # Ending cursor after sync
    customers_count = Column(Integer, default=0, nullable=False)
    invoices_count = Column(Integer, default=0, nullable=False)
    payments_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error tracking
    error_message = Column(String(1000), nullable=True)
    
    __table_args__ = (
        {"comment": "Billing sync batches for idempotent sync operations"}
    )
    
    def __repr__(self):
        return f"<BillingSyncBatch(batch_number={self.batch_number}, status={self.status.value})>"
