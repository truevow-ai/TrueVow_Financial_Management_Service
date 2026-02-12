"""Deferred Revenue Schemas"""
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from app.modules.ar.models.deferred_revenue_model import ScheduleStatus


class RevenueRecognitionRequest(BaseModel):
    """Schema for revenue recognition run"""
    book_id: UUID
    period_start: date
    period_end: date
    posted_by: UUID


class RevenueScheduleResponse(BaseModel):
    """Schema for revenue schedule response"""
    id: UUID
    legal_entity_id: UUID
    book_id: UUID
    ar_invoice_id: UUID
    ar_invoice_line_id: UUID
    total_amount: Decimal
    currency: str
    service_start: date
    service_end: date
    recognition_cadence: str
    status: ScheduleStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RevenueSchedulePeriodResponse(BaseModel):
    """Schema for revenue schedule period response"""
    id: UUID
    revenue_schedule_id: UUID
    period_start: date
    period_end: date
    recognition_amount: Decimal
    currency: str
    is_recognized: bool
    recognized_at: date | None
    journal_entry_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
