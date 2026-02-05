"""Period Close Checklist Model"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Enum as SQLEnum, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from app.shared.models.base_model import BaseModel


class ChecklistItemCode(str, enum.Enum):
    """Period close checklist item codes"""
    BANK_REC_DONE = "BANK_REC_DONE"
    REVREC_DONE = "REVREC_DONE"
    PAYROLL_POSTED = "PAYROLL_POSTED"
    ROYALTY_POSTED = "ROYALTY_POSTED"
    AR_AGING_READY = "AR_AGING_READY"
    AP_AGING_READY = "AP_AGING_READY"


class ChecklistItemStatus(str, enum.Enum):
    """Checklist item status"""
    PENDING = "PENDING"
    COMPLETE = "COMPLETE"
    SKIPPED = "SKIPPED"  # For optional items


class PeriodCloseChecklist(BaseModel):
    """Period close checklist items"""
    __tablename__ = "period_close_checklist"
    
    period_id = Column(UUID(as_uuid=True), ForeignKey("accounting_period.id"), nullable=False, index=True)
    item_code = Column(SQLEnum(ChecklistItemCode), nullable=False, index=True)
    status = Column(SQLEnum(ChecklistItemStatus), default=ChecklistItemStatus.PENDING, nullable=False)
    computed_at = Column(DateTime(timezone=True), nullable=True)
    computed_by = Column(UUID(as_uuid=True), nullable=True)  # System or user who computed status
    notes = Column(Text, nullable=True)  # Optional notes about why item is complete/pending
    
    # Relationships
    period = relationship("AccountingPeriod", backref="close_checklist")
    
    __table_args__ = (
        UniqueConstraint("period_id", "item_code", name="uq_period_close_checklist_period_item"),
        {"comment": "Period close checklist items"},
    )
    
    def __repr__(self):
        return f"<PeriodCloseChecklist(period={self.period_id}, item={self.item_code.value}, status={self.status.value})>"
