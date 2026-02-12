"""Reconciliation Schemas"""
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from app.modules.general_ledger.models.reconciliation_model import ReconciliationStatus


class ReconciliationSessionCreate(BaseModel):
    """Schema for creating a reconciliation session"""
    bank_account_id: UUID
    period_start: date
    period_end: date
    statement_ending_balance: Decimal
    statement_currency: str = Field(..., min_length=3, max_length=3)


class ReconciliationMatchCreate(BaseModel):
    """Schema for matching a transaction"""
    bank_transaction_id: UUID
    journal_entry_id: UUID | None = None
    match_type: str = Field("manual", pattern="^(auto|manual)$")
    notes: str | None = None


class ReconciliationCloseRequest(BaseModel):
    """Schema for closing a reconciliation"""
    reconciled_by: UUID
    notes: str | None = None
    allow_non_zero: bool = False


class ReconciliationMatchResponse(BaseModel):
    """Schema for reconciliation match response"""
    id: UUID
    reconciliation_session_id: UUID
    bank_transaction_id: UUID | None
    journal_entry_id: UUID | None
    match_type: str
    match_confidence: Decimal | None
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ReconciliationAdjustmentSubmitRequest(BaseModel):
    """Schema for submitting adjustment batch for approval"""
    batch_id: UUID
    reason: str | None = None
    row_version: int  # Required for optimistic locking


class ReconciliationAdjustmentApproveRequest(BaseModel):
    """Schema for approving adjustment batch"""
    batch_id: UUID
    reason: str | None = None
    override_reason: str | None = None  # For FINANCE_ADMIN SoD override
    row_version: int  # Required for optimistic locking


class ReconciliationAdjustmentRejectRequest(BaseModel):
    """Schema for rejecting adjustment batch"""
    batch_id: UUID
    reason: str  # Required for rejection
    required_changes: list[str] | None = None
    row_version: int  # Required for optimistic locking


class ReconciliationAdjustmentPostRequest(BaseModel):
    """Schema for posting adjustment batch"""
    batch_id: UUID
    posted_by: UUID
    row_version: int  # Required for optimistic locking


class ReconciliationSessionResponse(BaseModel):
    """Schema for reconciliation session response"""
    id: UUID
    bank_account_id: UUID
    period_start: date
    period_end: date
    statement_ending_balance: Decimal
    statement_currency: str
    status: ReconciliationStatus
    reconciled_by: UUID | None
    reconciled_at: date | None
    difference: Decimal
    notes: str | None
    created_at: datetime
    updated_at: datetime
    matches: list[ReconciliationMatchResponse] | None = None

    model_config = ConfigDict(from_attributes=True)


# Reconciliation Matching Schemas
from typing import List


class MatchSuggestionResponse(BaseModel):
    """Schema for match suggestion response"""
    journal_entry_id: UUID
    journal_entry_number: str
    entry_date: date
    total_amount: Decimal
    memo: str | None
    reference: str | None
    confidence: float
    match_reasons: List[str]

    model_config = ConfigDict(from_attributes=True)
