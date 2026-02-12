"""AR Sync Schemas"""
from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime


class BillingSyncRequest(BaseModel):
    """Schema for billing sync request"""
    entity_id: UUID
    since_cursor: Optional[str] = None
    full_resync: bool = False


class BillingSyncResponse(BaseModel):
    """Schema for billing sync response"""
    entity_id: UUID
    customers_synced: int
    invoices_synced: int
    payments_synced: int
    next_cursor: Optional[str] = None
    sync_timestamp: datetime
