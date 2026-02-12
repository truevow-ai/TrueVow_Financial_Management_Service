"""AP Bill Schemas"""
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, List
from app.modules.ap.models.ap_bill_model import BillStatus


class APBillLineCreate(BaseModel):
    """Schema for creating an AP bill line"""
    gl_account_id: UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_number: int = 1
    currency: str = "USD"
    tax_code: Optional[str] = None


class APBillCreate(BaseModel):
    """Schema for creating an AP bill"""
    legal_entity_id: UUID
    ap_vendor_id: UUID
    bill_number: str
    bill_date: date
    due_date: Optional[date] = None
    currency: str = "USD"
    description: Optional[str] = None
    reference_number: Optional[str] = None
    lines: List[APBillLineCreate] = []


class APBillSubmitApprovalRequest(BaseModel):
    """Schema for submitting AP bill for approval"""
    reason: Optional[str] = None
    row_version: int  # Required for optimistic locking


class APBillApproveRequest(BaseModel):
    """Schema for approving an AP bill"""
    reason: Optional[str] = None
    override_reason: Optional[str] = None  # For FINANCE_ADMIN SoD override
    row_version: int  # Required for optimistic locking


class APBillRejectRequest(BaseModel):
    """Schema for rejecting an AP bill"""
    reason: str  # Required for rejection
    row_version: int  # Required for optimistic locking


class APBillPostRequest(BaseModel):
    """Schema for posting an AP bill"""
    reason: Optional[str] = None
    idempotency_key: Optional[str] = None
    row_version: int  # Required for optimistic locking


class APBillLineResponse(BaseModel):
    """Schema for AP bill line response"""
    id: UUID
    ap_bill_id: UUID
    gl_account_id: UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_amount: Decimal
    line_number: int
    currency: str
    tax_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class APBillResponse(BaseModel):
    """Schema for AP bill response"""
    id: UUID
    legal_entity_id: UUID
    book_id: UUID
    ap_vendor_id: UUID
    bill_number: str
    bill_date: date
    due_date: Optional[date] = None
    total_amount: Decimal
    currency: str
    status: BillStatus
    paid_amount: Decimal
    outstanding_amount: Decimal
    description: Optional[str] = None
    reference_number: Optional[str] = None
    withholding_amount: Decimal
    withholding_profile_id: Optional[UUID] = None
    submitted_by: Optional[UUID] = None
    submitted_at: Optional[date] = None
    approved_by: Optional[UUID] = None
    approved_at: Optional[date] = None
    rejected_by: Optional[UUID] = None
    rejected_at: Optional[date] = None
    decision_reason: Optional[str] = None
    posted_by: Optional[UUID] = None
    posted_at: Optional[date] = None
    row_version: int
    journal_entry_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    lines: List[APBillLineResponse] = []

    model_config = ConfigDict(from_attributes=True)
