"""Settlement Schemas"""
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import date, datetime
from decimal import Decimal
from app.modules.treasury.models.settlement_model import SettlementSource


class SettlementCreate(BaseModel):
    """Schema for creating a settlement"""
    legal_entity_id: UUID
    bank_account_id: UUID
    settlement_date: date
    source: SettlementSource
    gross_amount: Decimal = Field(..., ge=0)
    fees: Decimal = Field(0, ge=0)
    net_amount: Decimal = Field(..., ge=0)
    currency: str = Field(..., min_length=3, max_length=3)
    external_settlement_id: str | None = None
    external_payout_id: str | None = None
    description: str | None = None


class SettlementImport(BaseModel):
    """Schema for importing settlement (manual JSON)"""
    legal_entity_id: UUID
    bank_account_id: UUID
    settlement_date: date
    source: SettlementSource
    gross_amount: Decimal
    fees: Decimal = Field(0, ge=0)
    net_amount: Decimal
    currency: str
    external_settlement_id: str | None = None
    external_payout_id: str | None = None
    description: str | None = None


class SettlementResponse(BaseModel):
    """Schema for settlement response"""
    id: UUID
    legal_entity_id: UUID
    bank_account_id: UUID
    settlement_date: date
    source: SettlementSource
    gross_amount: Decimal
    fees: Decimal
    net_amount: Decimal
    currency: str
    external_settlement_id: str | None
    external_payout_id: str | None
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
