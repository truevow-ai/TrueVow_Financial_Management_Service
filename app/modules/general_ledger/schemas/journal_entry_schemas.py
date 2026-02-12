"""Journal Entry Schemas"""
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from app.modules.general_ledger.models.journal_entry_model import JournalEntryStatus


class JournalLineCreate(BaseModel):
    """Schema for creating a journal line"""
    gl_account_id: UUID
    debit_fc: Decimal = Field(Decimal("0.00"), ge=0)
    credit_fc: Decimal = Field(Decimal("0.00"), ge=0)
    currency: str = Field(..., min_length=3, max_length=3)
    description: str | None = None
    debit_tc: Decimal | None = None
    credit_tc: Decimal | None = None
    fx_rate: Decimal | None = None
    fx_source: str | None = None
    fx_timestamp: datetime | None = None
    dimension_value_ids: list[UUID] | None = None


class JournalEntryCreate(BaseModel):
    """Schema for creating a journal entry"""
    book_id: UUID
    entry_date: date
    description: str = Field(..., min_length=1)
    reference_number: str | None = None
    source_service: str | None = None
    source_type: str | None = None
    source_id: UUID | None = None
    idempotency_key: str | None = None
    lines: list[JournalLineCreate] = Field(..., min_length=2)


class JournalEntryPostRequest(BaseModel):
    """Schema for posting a journal entry"""
    posted_by: UUID
    require_dimensions: bool = True


class JournalEntryReverseRequest(BaseModel):
    """Schema for reversing a journal entry"""
    reversed_by: UUID
    reason: str = Field(..., min_length=1)
    reversal_date: date | None = None


class JournalLineResponse(BaseModel):
    """Schema for journal line response"""
    id: UUID
    journal_entry_id: UUID
    book_id: UUID
    gl_account_id: UUID
    line_number: int
    debit_tc: Decimal
    credit_tc: Decimal
    currency: str
    debit_fc: Decimal
    credit_fc: Decimal
    fx_rate: Decimal | None
    fx_source: str | None
    fx_timestamp: datetime | None
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JournalEntryResponse(BaseModel):
    """Schema for journal entry response"""
    id: UUID
    book_id: UUID
    period_id: UUID
    entry_number: str
    entry_date: date
    description: str | None
    reference_number: str | None
    status: JournalEntryStatus
    source_service: str | None
    source_type: str | None
    source_id: UUID | None
    idempotency_key: str | None
    reversed_by_entry_id: UUID | None
    reversal_reason: str | None
    posted_by: UUID | None
    posted_at: date | None
    created_at: datetime
    updated_at: datetime
    lines: list[JournalLineResponse] | None = None

    model_config = ConfigDict(from_attributes=True)


class JournalLineBulkUpsertItem(BaseModel):
    """Schema for a single line in bulk upsert"""
    client_row_id: str | None = None  # Temporary ID for new rows
    line_id: UUID | None = None  # Database ID for existing rows
    gl_account_id: UUID | None = None  # Direct account ID
    account_code: str | None = None  # Account code (alternative to gl_account_id)
    description: str | None = None
    debit_amount: Decimal = Field(Decimal("0.00"), ge=0)
    credit_amount: Decimal = Field(Decimal("0.00"), ge=0)
    cost_center: str | None = None  # Dimension value code
    department: str | None = None  # Dimension value code
    location: str | None = None  # Dimension value code
    project: str | None = None  # Dimension value code
    currency: str | None = None
    fx_rate: Decimal | None = None
    deleted: bool = False  # Mark for deletion


class JournalLineBulkUpsertRequest(BaseModel):
    """Schema for bulk upsert request"""
    lines: list[JournalLineBulkUpsertItem] = Field(..., min_length=0)


class JournalLineBulkUpsertError(BaseModel):
    """Schema for per-row error in bulk upsert response"""
    client_row_id: str | None = None
    line_id: UUID | None = None
    field: str | None = None
    code: str
    message: str


class JournalLineBulkUpsertResponse(BaseModel):
    """Schema for bulk upsert response"""
    lines: list[JournalLineResponse]
    row_version: int | None = None
    errors: list[JournalLineBulkUpsertError] = Field(default_factory=list)
