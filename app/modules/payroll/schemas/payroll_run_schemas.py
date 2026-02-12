"""Payroll Run Schemas"""
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from app.modules.payroll.models.payroll_run_model import PayrollRunStatus


class PayrollRunCreate(BaseModel):
    """Schema for creating a payroll run"""
    entity_id: UUID
    book_id: UUID
    pay_group_id: UUID
    pay_period_start: date
    pay_period_end: date
    pay_date: date


class PayrollRunSubmitApprovalRequest(BaseModel):
    """Schema for submitting payroll run for approval"""
    reason: str | None = None
    row_version: int  # Required for optimistic locking


class PayrollRunApproveRequest(BaseModel):
    """Schema for approving a payroll run"""
    reason: str | None = None
    override_reason: str | None = None  # For FINANCE_ADMIN SoD override
    row_version: int  # Required for optimistic locking


class PayrollRunRejectRequest(BaseModel):
    """Schema for rejecting a payroll run"""
    reason: str  # Required for rejection
    required_changes: list[str] | None = None  # Optional list of required changes
    row_version: int  # Required for optimistic locking


class PayrollRunPostRequest(BaseModel):
    """Schema for posting a payroll run"""
    reason: str | None = None
    idempotency_key: str | None = None
    row_version: int  # Required for optimistic locking


class PayrollRunReverseRequest(BaseModel):
    """Schema for reversing a payroll run"""
    reason: str
    reversal_date: date | None = None  # If None, uses next open period


class PayrollRunItemResponse(BaseModel):
    """Schema for payroll run item response"""
    id: UUID
    payroll_run_id: UUID
    hr_employee_id: UUID
    gross_pay: Decimal
    total_deductions: Decimal
    net_pay: Decimal
    employer_contributions: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class PayrollRunResponse(BaseModel):
    """Schema for payroll run response"""
    id: UUID
    legal_entity_id: UUID
    book_id: UUID
    pay_group_id: UUID
    run_number: str
    pay_period_start: date
    pay_period_end: date
    pay_date: date
    status: PayrollRunStatus
    total_gross: Decimal
    total_deductions: Decimal
    total_net: Decimal
    total_employer_contrib: Decimal
    currency: str
    submitted_by: UUID | None
    submitted_at: datetime | None
    approved_by: UUID | None
    approved_at: datetime | None
    rejected_by: UUID | None
    rejected_at: datetime | None
    decision_reason: str | None
    row_version: int
    posted_by: UUID | None
    posted_at: datetime | None
    journal_entry_id: UUID | None
    created_at: datetime
    updated_at: datetime
    items: list[PayrollRunItemResponse] | None = None

    model_config = ConfigDict(from_attributes=True)
