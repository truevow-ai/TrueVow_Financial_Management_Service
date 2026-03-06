"""Pricing Schema Definitions"""
from pydantic import BaseModel, Field
from typing import Dict, Optional
from datetime import datetime
from uuid import UUID


class FeatureAccessSchema(BaseModel):
    """Feature access schema for pricing calculations"""
    
    tier: str = Field(..., description="Current tier level")
    features: Dict[str, Dict] = Field(
        ..., 
        description="Feature-specific pricing information"
    )
    founding_intelligence: Optional[Dict] = Field(
        None,
        description="Founding Intelligence pricing lock information"
    )


class PricingResponse(BaseModel):
    """Response schema for pricing information"""
    
    tenant_id: UUID
    tier: str = Field(..., description="Tier level (e.g., 'solo', 'growth')")
    features: Dict[str, Dict] = Field(
        ...,
        description="Feature pricing details",
        example={
            "intake": {
                "per_use_price_cents": 9900,
                "included_uses": 0
            },
            "settle": {
                "per_use_price_cents": 0,
                "included_uses": 10
            }
        }
    )
    founding_intelligence: Optional[Dict] = Field(
        None,
        description="Founding Intelligence pricing lock details",
        example={
            "pricing_locked_until": "2029-01-01T00:00:00Z",
            "locked_unlock_price_cents": 9900  # $99 locked rate
        }
    )
    currency: str = Field(default="USD", description="Currency code")
    last_updated: datetime = Field(default_factory=datetime.now)


class TierInfo(BaseModel):
    """Tier information schema"""
    
    name: str
    monthly_base_price_cents: int
    included_features: list[str]
    overage_pricing: Dict[str, Dict]


class AddOnPurchase(BaseModel):
    """Add-on purchase schema"""
    
    id: UUID
    name: str
    price_cents: int
    billing_cycle: str  # one_time, monthly, annual
    quantity: int = 1
    active: bool = True
