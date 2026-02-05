"""Treasury Sync Schemas"""
from pydantic import BaseModel
from uuid import UUID
from typing import List, Optional
from datetime import datetime
from app.modules.treasury.schemas.bank_transaction_schemas import BankTransactionResponse
from app.modules.treasury.schemas.settlement_schemas import SettlementResponse
from app.modules.treasury.schemas.fx_conversion_schemas import FXConversionResponse
from app.modules.treasury.schemas.transfer_schemas import TransferResponse


class TreasurySyncRequest(BaseModel):
    """Schema for treasury sync request"""
    entity_id: UUID
    since_cursor: Optional[str] = None
    full_resync: bool = False


class TreasurySyncResponse(BaseModel):
    """Schema for treasury sync response"""
    entity_id: UUID
    transactions_count: int
    settlements_count: int
    fx_conversions_count: int
    transfers_count: int
    next_cursor: Optional[str] = None
    sync_timestamp: datetime
