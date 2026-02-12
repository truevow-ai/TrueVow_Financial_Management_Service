"""Intercompany Schemas"""
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from app.modules.intercompany.models.royalty_model import RoyaltyBasis


class IntercompanyTransferCreate(BaseModel):
    """Schema for creating intercompany transfer"""
    from_entity_id: UUID
    to_entity_id: UUID
    transfer_date: date
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    transfer_type: str = Field("CASH", min_length=1)
    description: str | None = None
    reference_number: str | None = None
    from_bank_account_id: UUID | None = None
    to_bank_account_id: UUID | None = None


class IntercompanyTransferPostRequest(BaseModel):
    """Schema for posting intercompany transfer"""
    posted_by: UUID


class IntercompanyTransferResponse(BaseModel):
    """Schema for intercompany transfer response"""
    id: UUID
    from_entity_id: UUID
    to_entity_id: UUID
    transfer_date: date
    amount: Decimal
    currency: str
    transfer_type: str
    description: str | None
    reference_number: str | None
    is_reconciled: bool
    reconciled_at: date | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoyaltyAgreementCreate(BaseModel):
    """Schema for creating royalty agreement"""
    from_entity_id: UUID
    to_entity_id: UUID
    agreement_code: str = Field(..., min_length=1, max_length=100)
    agreement_name: str = Field(..., min_length=1, max_length=255)
    basis: RoyaltyBasis
    rate: Decimal = Field(..., ge=0, le=100)
    fixed_amount: Decimal | None = Field(None, ge=0)
    effective_from: date
    effective_to: date | None = None
    currency: str = Field(..., min_length=3, max_length=3)
    description: str | None = None


class RoyaltyCalculationRequest(BaseModel):
    """Schema for calculating royalty"""
    agreement_id: UUID
    period_start: date
    period_end: date


class RoyaltyRunSubmitApprovalRequest(BaseModel):
    """Schema for submitting royalty run for approval"""
    reason: str | None = None
    row_version: int  # Required for optimistic locking


class RoyaltyRunApproveRequest(BaseModel):
    """Schema for approving royalty run"""
    reason: str | None = None
    override_reason: str | None = None  # For FINANCE_ADMIN SoD override
    row_version: int  # Required for optimistic locking


class RoyaltyRunRejectRequest(BaseModel):
    """Schema for rejecting royalty run"""
    reason: str  # Required for rejection
    required_changes: list[str] | None = None
    row_version: int  # Required for optimistic locking


class RoyaltyCalculationPostRequest(BaseModel):
    """Schema for posting royalty calculation"""
    reason: str | None = None
    idempotency_key: str | None = None


class RoyaltyAgreementResponse(BaseModel):
    """Schema for royalty agreement response"""
    id: UUID
    from_entity_id: UUID
    to_entity_id: UUID
    agreement_code: str
    agreement_name: str
    basis: RoyaltyBasis
    rate: Decimal
    fixed_amount: Decimal | None
    effective_from: date
    effective_to: date | None
    currency: str
    is_active: bool
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RoyaltyCalculationResponse(BaseModel):
    """Schema for royalty calculation response"""
    id: UUID
    royalty_agreement_id: UUID
    period_start: date
    period_end: date
    revenue_base: Decimal
    recognized_revenue_base: Decimal
    collected_revenue_base: Decimal
    calculated_amount: Decimal
    currency: str
    status: str  # RoyaltyRunStatus
    submitted_by: UUID | None
    submitted_at: datetime | None
    approved_by: UUID | None
    approved_at: datetime | None
    rejected_by: UUID | None
    rejected_at: datetime | None
    decision_reason: str | None
    row_version: int
    is_posted: bool  # Legacy field
    posted_at: datetime | None  # Legacy field
    posted_by: UUID | None
    journal_entry_id: UUID | None
    intercompany_transfer_id: UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
