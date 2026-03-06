"""Dashboard Statistics Schema Definitions"""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime


class DashboardStatsResponse(BaseModel):
    """Response schema for dashboard statistics"""
    
    # Financial metrics
    total_revenue: Decimal = Field(..., description="Total revenue in cents")
    total_expenses: Decimal = Field(..., description="Total expenses in cents")
    net_income: Decimal = Field(..., description="Net income in cents")
    cash_position: Decimal = Field(..., description="Current cash position in cents")
    accounts_receivable: Decimal = Field(..., description="AR balance in cents")
    accounts_payable: Decimal = Field(..., description="AP balance in cents")
    total_assets: Optional[Decimal] = Field(None, description="Total assets in cents")
    total_liabilities: Optional[Decimal] = Field(None, description="Total liabilities in cents")
    equity: Optional[Decimal] = Field(None, description="Equity in cents")
    
    # Operational metrics
    pending_approvals: int = Field(..., description="Number of pending approvals")
    overdue_invoices: int = Field(..., description="Number of overdue invoices")
    upcoming_payments: int = Field(..., description="Number of upcoming payments")
    
    # Metadata
    currency: str = Field(default="USD", description="Base currency")
    as_of_date: datetime = Field(default_factory=datetime.now, description="Statistics as of date")


class TrendData(BaseModel):
    """Trend data for metrics"""
    current_value: Decimal
    previous_value: Decimal
    change_percentage: float
    trend_direction: str  # 'up', 'down', 'flat'
