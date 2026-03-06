"""Pricing API Routes"""
from fastapi import APIRouter, Depends, HTTPException, status
from uuid import UUID
from app.modules.ar.services.pricing_service import PricingService
from app.modules.ar.integrations.billing_adapter import BillingAdapter, HTTPBillingAdapter
from app.modules.ar.schemas.pricing_schemas import PricingResponse
from app.core.config import settings
from app.auth.authorization import get_user_context

router = APIRouter(prefix="/pricing", tags=["Pricing"], dependencies=[Depends(get_user_context)])


def get_billing_adapter() -> BillingAdapter:
    """Get billing adapter instance - always uses HTTP adapter for production"""
    return HTTPBillingAdapter()


def get_pricing_service(adapter: BillingAdapter = Depends(get_billing_adapter)) -> PricingService:
    """Get pricing service instance"""
    return PricingService(adapter)


@router.get("/tenants/{tenant_id}/feature-access")
async def get_feature_access(
    tenant_id: UUID,
    pricing_service: PricingService = Depends(get_pricing_service)
):
    """Get feature access and pricing information for a tenant
    
    This endpoint provides:
    - Current tier level (solo, growth, etc.)
    - Feature-specific pricing (per-use costs, included quantities)
    - Founding Intelligence pricing lock information ($99/unlock for 36 months)
    
    Example Response:
    ```json
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
    ```
    """
    try:
        result = await pricing_service.get_feature_access(tenant_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing information not found: {str(e)}"
        )


@router.get("/tenants/{tenant_id}/feature-cost")
async def calculate_feature_cost(
    tenant_id: UUID,
    feature_name: str,
    usage_count: int,
    pricing_service: PricingService = Depends(get_pricing_service)
):
    """Calculate cost for a specific feature based on usage
    
    Args:
        tenant_id: The tenant ID
        feature_name: Name of the feature (e.g., 'intake', 'settle')
        usage_count: Number of times the feature was used
        
    Returns:
        Cost breakdown including billable uses and total cost
    """
    try:
        result = await pricing_service.calculate_feature_cost(
            tenant_id=tenant_id,
            feature_name=feature_name,
            usage_count=usage_count
        )
        return result
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing information not found: {str(e)}"
        )


@router.get("/tenants/{tenant_id}/addons")
async def get_addon_purchases(
    tenant_id: UUID,
    pricing_service: PricingService = Depends(get_pricing_service)
):
    """Get active add-on purchases for a tenant
    
    Returns list of add-ons with pricing and billing cycle information
    """
    try:
        result = await pricing_service.get_addon_purchases(tenant_id)
        return {"addons": result}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve add-ons: {str(e)}"
        )


@router.get("/tenants/{tenant_id}/founding-intelligence")
async def check_founding_intelligence_benefits(
    tenant_id: UUID,
    pricing_service: PricingService = Depends(get_pricing_service)
):
    """Check if tenant has Founding Intelligence pricing locks
    
    Returns information about pricing locks including:
    - Whether the tenant has founding benefits
    - Lock expiration date
    - Locked unlock price ($99 for founding members)
    - Whether the lock is still active
    - Savings message
    """
    try:
        result = await pricing_service.check_founding_intelligence_benefits(tenant_id)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Failed to check founding benefits: {str(e)}"
        )
