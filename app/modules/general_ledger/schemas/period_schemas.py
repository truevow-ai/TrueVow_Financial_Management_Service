"""Accounting Period Schemas"""
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime
from app.modules.general_ledger.models.accounting_period_model import PeriodStatus


class PeriodGenerateRequest(BaseModel):
    """Schema for generating periods"""
    book_id: UUID
    start_year: int = Field(..., ge=2000, le=2100)
    start_month: int = Field(..., ge=1, le=12)
    num_months: int = Field(12, ge=1, le=24)


class PeriodCloseRequest(BaseModel):
    """Schema for closing a period"""
    closed_by: UUID
    reason: str | None = None


class PeriodCloseSubmitRequest(BaseModel):
    """Schema for submitting period for close approval"""
    reason: str | None = None
    row_version: int  # Required for optimistic locking
    row_version: int  # Required for optimistic locking


class PeriodCloseApproveRequest(BaseModel):
    """Schema for approving period close"""
    reason: str | None = None
    override_reason: str | None = None  # For FINANCE_ADMIN SoD override
    row_version: int  # Required for optimistic locking
    row_version: int  # Required for optimistic locking


class PeriodLockRequest(BaseModel):
    """Schema for locking a period"""
    locked_by: UUID
    reason: str = Field(..., min_length=1)


class AccountingPeriodResponse(BaseModel):
    """Schema for accounting period response"""
    id: UUID
    book_id: UUID
    period_start: date
    period_end: date
    period_name: str
    status: PeriodStatus
    submitted_by: UUID | None
    submitted_at: datetime | None
    approved_by: UUID | None
    approved_at: datetime | None
    decision_reason: str | None
    row_version: int
    closed_by: UUID | None  # Legacy field
    closed_at: datetime | None  # Legacy field
    lock_reason: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Period Close Checklist Schemas
from app.modules.general_ledger.models.period_close_checklist_model import (
    ChecklistItemCode,
    ChecklistItemStatus
)


class PeriodCloseChecklistItemResponse(BaseModel):
    """Schema for period close checklist item response"""
    id: UUID
    period_id: UUID
    item_code: ChecklistItemCode
    status: ChecklistItemStatus
    computed_at: datetime | None
    computed_by: UUID | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PeriodCloseChecklistMarkCompleteRequest(BaseModel):
    """Schema for marking checklist item as complete"""
    notes: str | None = None
