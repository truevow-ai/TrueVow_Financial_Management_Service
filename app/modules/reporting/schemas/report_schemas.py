"""Report Request/Response Schemas"""
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import date
from typing import List, Optional, Dict, Any


class TrialBalanceRequest(BaseModel):
    """Trial Balance report request"""
    book_id: UUID
    period_id: Optional[UUID] = None
    as_of_date: Optional[date] = None
    include_zero_balance: bool = False


class ProfitLossRequest(BaseModel):
    """Profit & Loss report request"""
    book_id: UUID
    period_start: date
    period_end: date
    compare_previous: bool = False


class BalanceSheetRequest(BaseModel):
    """Balance Sheet report request"""
    book_id: UUID
    as_of_date: date


class CashPositionRequest(BaseModel):
    """Cash Position report request"""
    entity_id: UUID
    as_of_date: date
    currency: Optional[str] = None


class ARAgingRequest(BaseModel):
    """AR Aging report request"""
    entity_id: UUID
    as_of_date: date
    aging_buckets: Optional[List[int]] = None


class GLDetailRequest(BaseModel):
    """GL Detail report request"""
    book_id: UUID
    account_id: Optional[UUID] = None
    account_code: Optional[str] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    period_id: Optional[UUID] = None
    include_dimensions: bool = True


# Response schemas are Dict[str, Any] as they have dynamic structures
# The services return the actual report data
