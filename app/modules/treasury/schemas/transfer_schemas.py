"""Transfer Schemas"""
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from app.modules.treasury.models.transfer_model import TransferType


class TransferCreate(BaseModel):
    """Schema for creating a transfer"""
    legal_entity_id: UUID
    transfer_date: date
    transfer_type: TransferType
    from_bank_account_id: UUID
    amount: Decimal = Field(..., gt=0)
    currency: str = Field(..., min_length=3, max_length=3)
    to_bank_account_id: UUID | None = None
    to_entity_id: UUID | None = None
    description: str | None = None
    reference_number: str | None = None
    external_id: str | None = None


class TransferResponse(BaseModel):
    """Schema for transfer response"""
    id: UUID
    legal_entity_id: UUID
    transfer_date: date
    transfer_type: TransferType
    from_bank_account_id: UUID
    to_bank_account_id: UUID | None
    to_entity_id: UUID | None
    amount: Decimal
    currency: str
    description: str | None
    reference_number: str | None
    external_id: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
