"""Deferred Revenue Models"""
from sqlalchemy import Column, String, Date, ForeignKey, Numeric, Enum as SQLEnum, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import enum
from decimal import Decimal
from app.shared.models.base_model import BaseModel


class ScheduleStatus(str, enum.Enum):
    """Revenue schedule status"""
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class RevenueSchedule(BaseModel):
    """Revenue recognition schedule"""
    __tablename__ = "revenue_schedule"
    
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("book.id"), nullable=False, index=True)
    ar_invoice_id = Column(UUID(as_uuid=True), ForeignKey("ar_invoice.id"), nullable=False, index=True)
    ar_invoice_line_id = Column(UUID(as_uuid=True), ForeignKey("ar_invoice_line.id"), nullable=False, index=True)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    service_start = Column(Date, nullable=False)
    service_end = Column(Date, nullable=False)
    recognition_cadence = Column(String(20), default="MONTHLY", nullable=False)  # MONTHLY, QUARTERLY, etc.
    status = Column(SQLEnum(ScheduleStatus), default=ScheduleStatus.ACTIVE, nullable=False, index=True)
    
    # Relationships
    entity = relationship("LegalEntity")
    book = relationship("Book")
    invoice = relationship("ARInvoice")
    invoice_line = relationship("ARInvoiceLine")
    periods = relationship("RevenueSchedulePeriod", back_populates="schedule", cascade="all, delete-orphan")
    
    __table_args__ = (
        {"comment": "Revenue recognition schedules from invoice lines"}
    )
    
    def __repr__(self):
        return f"<RevenueSchedule(invoice_line={self.ar_invoice_line_id}, amount={self.total_amount}, period={self.service_start} to {self.service_end})>"


class RevenueSchedulePeriod(BaseModel):
    """Revenue recognition schedule period"""
    __tablename__ = "revenue_schedule_period"
    
    revenue_schedule_id = Column(UUID(as_uuid=True), ForeignKey("revenue_schedule.id"), nullable=False, index=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    recognition_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), nullable=False)
    is_recognized = Column(Boolean, default=False, nullable=False, index=True)
    recognized_at = Column(Date, nullable=True)
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("journal_entry.id"), nullable=True)  # Link to recognition JE
    
    # Relationships
    schedule = relationship("RevenueSchedule", back_populates="periods")
    journal_entry = relationship("JournalEntry")
    
    __table_args__ = (
        UniqueConstraint("revenue_schedule_id", "period_start", name="uq_revenue_schedule_period_sched_start"),
        {"comment": "Monthly recognition periods within a schedule"},
    )
    
    def __repr__(self):
        return f"<RevenueSchedulePeriod(schedule={self.revenue_schedule_id}, period={self.period_start}, amount={self.recognition_amount}, recognized={self.is_recognized})>"
