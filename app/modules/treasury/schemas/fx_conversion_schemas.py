"""FX Conversion Schemas"""
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal


class FXConversionCreate(BaseModel):
    """Schema for creating an FX conversion"""
    legal_entity_id: UUID
    conversion_date: date
    from_currency: str = Field(..., min_length=3, max_length=3)
    to_currency: str = Field(..., min_length=3, max_length=3)
    from_amount: Decimal = Field(..., gt=0)
    to_amount: Decimal = Field(..., gt=0)
    exchange_rate: Decimal = Field(..., gt=0)
    rate_source: str = Field(..., min_length=1)
    from_bank_account_id: UUID | None = None
    to_bank_account_id: UUID | None = None
    description: str | None = None
    external_id: str | None = None


class FXConversionResponse(BaseModel):
    """Schema for FX conversion response"""
    id: UUID
    legal_entity_id: UUID
    conversion_date: date
    from_currency: str
    to_currency: str
    from_amount: Decimal
    to_amount: Decimal
    exchange_rate: Decimal
    rate_source: str
    from_bank_account_id: UUID | None
    to_bank_account_id: UUID | None
    description: str | None
    external_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
