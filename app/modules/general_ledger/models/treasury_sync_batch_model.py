"""Treasury Sync Batch Model"""
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func
import enum
from app.shared.models.base_model import BaseModel


class SyncBatchStatus(str, enum.Enum):
    """Sync batch status"""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TreasurySyncBatch(BaseModel):
    """Treasury sync batch for tracking idempotent sync/post operations"""
    __tablename__ = "treasury_sync_batch"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("book.id"), nullable=False, index=True)
    batch_number = Column(String(100), unique=True, nullable=False, index=True)
    status = Column(SQLEnum(SyncBatchStatus), default=SyncBatchStatus.PENDING, nullable=False, index=True)
    
    # Sync metadata
    cursor_start = Column(String(255), nullable=True)  # Starting cursor for this batch
    cursor_end = Column(String(255), nullable=True)  # Ending cursor after sync
    transactions_count = Column(Integer, default=0, nullable=False)
    posted_count = Column(Integer, default=0, nullable=False)
    failed_count = Column(Integer, default=0, nullable=False)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Error tracking
    error_message = Column(String(1000), nullable=True)
    
    __table_args__ = (
        {"comment": "Treasury sync batches for idempotent sync/post operations"}
    )
    
    def __repr__(self):
        return f"<TreasurySyncBatch(batch_number={self.batch_number}, status={self.status.value})>"
