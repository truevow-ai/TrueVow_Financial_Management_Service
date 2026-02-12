"""Chart of Accounts Schemas"""
from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from app.modules.general_ledger.models.gl_account_model import AccountType


class GLAccountCreate(BaseModel):
    """Schema for creating a GL account"""
    book_id: UUID
    account_code: str = Field(..., min_length=1, max_length=50)
    account_name: str = Field(..., min_length=1, max_length=255)
    account_type: AccountType
    parent_account_id: UUID | None = None
    description: str | None = None


class GLAccountUpdate(BaseModel):
    """Schema for updating a GL account"""
    account_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    is_active: bool | None = None


class GLAccountResponse(BaseModel):
    """Schema for GL account response"""
    id: UUID
    book_id: UUID
    account_code: str
    account_name: str
    account_type: AccountType
    parent_account_id: UUID | None
    is_active: bool
    description: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GLAccountMappingCreate(BaseModel):
    """Schema for creating account mapping"""
    legal_entity_id: UUID
    book_id: UUID
    map_key: str = Field(..., min_length=1, max_length=100)
    gl_account_id: UUID


class GLAccountMappingResponse(BaseModel):
    """Schema for account mapping response"""
    id: UUID
    legal_entity_id: UUID
    book_id: UUID
    map_key: str
    gl_account_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
