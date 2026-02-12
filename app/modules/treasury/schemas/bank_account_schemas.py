"""Bank Account Schemas"""
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime


class BankAccountCreate(BaseModel):
    """Schema for creating a bank account"""
    legal_entity_id: UUID
    account_name: str = Field(..., min_length=1, max_length=255)
    bank_name: str = Field(..., min_length=1, max_length=255)
    currency: str = Field(..., min_length=3, max_length=3)
    account_number: str | None = None
    bank_code: str | None = None
    account_type: str | None = None
    wps_enabled: bool = False
    wps_agent_id: str | None = None


class BankAccountUpdate(BaseModel):
    """Schema for updating a bank account"""
    account_name: str | None = Field(None, min_length=1, max_length=255)
    is_active: bool | None = None
    wps_enabled: bool | None = None
    wps_agent_id: str | None = None


class BankAccountResponse(BaseModel):
    """Schema for bank account response"""
    id: UUID
    legal_entity_id: UUID
    account_name: str
    account_number: str | None
    bank_name: str
    bank_code: str | None
    currency: str
    account_type: str | None
    is_active: bool
    wps_enabled: bool
    wps_agent_id: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
