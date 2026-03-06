"""Pricing Service - Fetches pricing and tier information from Billing service"""
from typing import Dict, Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from app.modules.ar.integrations.billing_adapter import BillingAdapter
from app.core.exceptions import NotFoundError, ValidationError


class PricingService:
    """Service for fetching pricing and tier information from Billing service"""
    
    def __init__(self, billing_adapter: BillingAdapter):
        self.billing_adapter = billing_adapter
    
    async def get_feature_access(
        self,
        tenant_id: UUID
    ) -> Dict:
        """Get feature access and pricing information for a tenant
        
        Args:
            tenant_id: The tenant/tenant ID
            
        Returns:
            Dict containing tier, features, and founding intelligence info
            
        Example Response:
            {
                "tier": "growth",
                "features": {
                    "intake": {
                        "per_use_price_cents": 8900,
                        "included_uses": 50,
                        "used_this_month": 23
                    },
                    "settle": {
                        "per_use_price_cents": 9900,
                        "included_uses": 10,
                        "used_this_month": 5
                    }
                },
                "founding_intelligence": {
                    "pricing_locked_until": "2029-01-01T00:00:00Z",
                    "locked_unlock_price_cents": 9900
                }
            }
        """
        try:
            # Call billing service to get feature access
            response = await self.billing_adapter.get_tenant_pricing(tenant_id)
            
            if not response:
                raise NotFoundError(f"Pricing information not found for tenant {tenant_id}")
            
            return response
            
        except Exception as e:
            # Handle billing service errors
            if hasattr(e, 'status_code') and e.status_code == 404:
                raise NotFoundError(f"Pricing information not found for tenant {tenant_id}")
            raise
    
    async def calculate_feature_cost(
        self,
        tenant_id: UUID,
        feature_name: str,
        usage_count: int
    ) -> Dict:
        """Calculate cost for a specific feature based on usage
        
        Args:
            tenant_id: The tenant ID
            feature_name: Name of the feature (e.g., 'intake', 'settle')
            usage_count: Number of times the feature was used
            
        Returns:
            Dict with cost breakdown
        """
        pricing_info = await self.get_feature_access(tenant_id)
        
        feature_pricing = pricing_info["features"].get(feature_name)
        if not feature_pricing:
            raise ValidationError(f"Feature '{feature_name}' not found in pricing plan")
        
        included_uses = feature_pricing.get("included_uses", 0)
        per_use_price_cents = feature_pricing.get("per_use_price_cents", 0)
        
        # Calculate overage
        billable_uses = max(0, usage_count - included_uses)
        total_cost_cents = billable_uses * per_use_price_cents
        
        return {
            "feature_name": feature_name,
            "tier": pricing_info["tier"],
            "included_uses": included_uses,
            "usage_count": usage_count,
            "billable_uses": billable_uses,
            "per_use_price_cents": per_use_price_cents,
            "total_cost_cents": total_cost_cents,
            "currency": "USD"
        }
    
    async def get_addon_purchases(
        self,
        tenant_id: UUID
    ) -> List[Dict]:
        """Get active add-on purchases for a tenant
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            List of add-on purchases
        """
        try:
            addons = await self.billing_adapter.get_tenant_addons(tenant_id)
            return addons or []
        except Exception as e:
            # Return empty list if no addons found
            return []
    
    async def check_founding_intelligence_benefits(
        self,
        tenant_id: UUID
    ) -> Dict:
        """Check if tenant has Founding Intelligence pricing locks
        
        Args:
            tenant_id: The tenant ID
            
        Returns:
            Dict with founding intelligence benefits
        """
        pricing_info = await self.get_feature_access(tenant_id)
        
        founding_benefits = pricing_info.get("founding_intelligence")
        
        if not founding_benefits:
            return {
                "has_founding_benefits": False,
                "message": "No Founding Intelligence pricing lock found"
            }
        
        # Check if lock is still valid
        locked_until = datetime.fromisoformat(
            founding_benefits["pricing_locked_until"].replace("Z", "+00:00")
        )
        is_still_locked = datetime.now(locked_until.tzinfo) < locked_until
        
        return {
            "has_founding_benefits": True,
            "pricing_locked_until": founding_benefits["pricing_locked_until"],
            "locked_unlock_price_cents": founding_benefits.get("locked_unlock_price_cents", 9900),
            "is_still_locked": is_still_locked,
            "savings_message": f"Save ${founding_benefits.get('locked_unlock_price_cents', 9900) / 100:.2f} per unlock until {locked_until.strftime('%Y-%m-%d')}" if is_still_locked else "Pricing lock has expired"
        }
