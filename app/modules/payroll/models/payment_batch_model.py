"""Payroll Payment Batch Model"""
from sqlalchemy import Column, String, Integer, ForeignKey, Enum as SQLEnum, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.shared.models.base_model import BaseModel


class BatchStatus(str, enum.Enum):
    """Payment batch status"""
    GENERATED = "GENERATED"
    EXPORTED = "EXPORTED"
    SUBMITTED = "SUBMITTED"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class PayrollPaymentBatch(BaseModel):
    """Payroll payment batch for export"""
    __tablename__ = "payroll_payment_batch"
    
    payroll_run_id = Column(UUID(as_uuid=True), ForeignKey("payroll_run.id"), nullable=False, index=True)
    batch_number = Column(String(100), unique=True, nullable=False, index=True)
    export_type = Column(String(50), nullable=False)  # WPS_SIF, BANK_CSV, etc.
    status = Column(SQLEnum(BatchStatus), default=BatchStatus.GENERATED, nullable=False, index=True)
    file_path = Column(String(500))  # Generated file path
    file_hash = Column(String(64))  # SHA-256 hash of file content
    file_size = Column(Integer, nullable=True)
    exported_at = Column(DateTime(timezone=True), nullable=True)
    exported_by = Column(UUID(as_uuid=True), nullable=True)
    batch_metadata = Column("metadata", Text)  # JSON blob for export metadata (Python name avoids declarative reserved "metadata")
    
    # Relationships
    payroll_run = relationship("PayrollRun", back_populates="payment_batches")
    
    __table_args__ = (
        {"comment": "Payroll payment batch exports (WPS, bank CSV, etc.)"}
    )
    
    def __repr__(self):
        return f"<PayrollPaymentBatch(number={self.batch_number}, type={self.export_type}, status={self.status.value})>"
