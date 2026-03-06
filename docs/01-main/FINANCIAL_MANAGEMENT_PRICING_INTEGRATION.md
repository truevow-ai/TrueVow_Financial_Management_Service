# Financial Management Service - Pricing Integration Guide

**Last Updated:** February 16, 2026  
**Status:** ✅ IMPLEMENTED

## Overview

The Financial Management Service now includes complete integration with the Billing Service for pricing and tier information. This enables financial calculations, cost tracking, and Founding Intelligence pricing lock management.

## What Was Implemented

### 1. Backend Components ✅

#### Schema Definitions
- **File:** `app/modules/ar/schemas/pricing_schemas.py`
- **Purpose:** Pydantic schemas for pricing API requests/responses
- **Key Schemas:**
  - `PricingResponse` - Main response schema with tier, features, and founding intelligence
  - `FeatureAccessSchema` - Feature access details
  - `TierInfo` - Tier level information
  - `AddOnPurchase` - Add-on purchase details

#### Service Layer
- **File:** `app/modules/ar/services/pricing_service.py`
- **Purpose:** Business logic for pricing operations
- **Key Methods:**
  - `get_feature_access(tenant_id)` - Get complete pricing info for a tenant
  - `calculate_feature_cost(tenant_id, feature_name, usage_count)` - Calculate costs based on usage
  - `get_addon_purchases(tenant_id)` - Retrieve active add-on purchases
  - `check_founding_intelligence_benefits(tenant_id)` - Check pricing lock status

#### Adapter Layer
- **File:** `app/modules/ar/integrations/billing_adapter.py`
- **Updates:** Added pricing-specific methods to BillingAdapter interface
- **New Methods:**
  - `get_tenant_pricing(tenant_id)` - Fetch pricing from billing service
  - `get_tenant_addons(tenant_id)` - Fetch add-on purchases
- **Implementations:**
  - `HTTPBillingAdapter` - Production HTTP client
  - `MockBillingAdapter` - Development/testing mock with sample data

#### API Routes
- **File:** `app/modules/ar/api/routes/pricing_routes.py`
- **Endpoints:**
  ```
  GET /api/v1/fm/pricing/tenants/{tenant_id}/feature-access
  GET /api/v1/fm/pricing/tenants/{tenant_id}/feature-cost?feature_name={name}&usage_count={count}
  GET /api/v1/fm/pricing/tenants/{tenant_id}/addons
  GET /api/v1/fm/pricing/tenants/{tenant_id}/founding-intelligence
  ```

### 2. Frontend Enterprise Features ✅

#### Toast Notifications
- **File:** `frontend/hooks/useCompanyOperations.ts`
- **Features:**
  - Automatic toast notifications for all company operations
  - Success/error/warning/info notification types
  - Auto-dismiss with configurable duration
  - Pre-built hooks for common operations (create, update, delete, sync, approve, reject)

#### Dynamic Breadcrumb Navigation
- **File:** `frontend/components/layout/Breadcrumbs.tsx`
- **Features:**
  - Dynamic breadcrumb generation based on current route
  - Clickable intermediate breadcrumbs
  - Proper chevron separators
  - Responsive design with text truncation
  - Comprehensive mapping of all financial module routes

#### Contextual Sidebar with Statistics
- **Files:** 
  - `frontend/components/widgets/CompanyStatsWidget.tsx`
  - `frontend/components/layout/Sidebar.tsx`
- **Features:**
  - Financial metrics display (Revenue, Net Income, Cash Position, AR/AP Balances)
  - Operational alerts (Pending Approvals, Overdue Invoices, Upcoming Payments)
  - Status definitions/legend with color coding
  - Quick action buttons
  - Mock data ready for real API integration

## API Usage Examples

### Get Feature Access Information

```typescript
// Frontend example
const response = await fetch('/api/v1/fm/pricing/tenants/{tenant_id}/feature-access', {
  headers: { 'Authorization': `Bearer ${token}` }
});

const data = await response.json();
// Response:
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

### Calculate Feature Cost

```typescript
// Calculate cost for using 'intake' feature 75 times
const response = await fetch(
  '/api/v1/fm/pricing/tenants/{tenant_id}/feature-cost' +
  '?feature_name=intake&usage_count=75',
  { headers: { 'Authorization': `Bearer ${token}` } }
);

const cost = await response.json();
// Response:
{
  "feature_name": "intake",
  "tier": "growth",
  "included_uses": 50,
  "usage_count": 75,
  "billable_uses": 25,
  "per_use_price_cents": 8900,
  "total_cost_cents": 222500,  // $2,225.00
  "currency": "USD"
}
```

### Check Founding Intelligence Benefits

```typescript
const response = await fetch(
  '/api/v1/fm/pricing/tenants/{tenant_id}/founding-intelligence',
  { headers: { 'Authorization': `Bearer ${token}` } }
);

const benefits = await response.json();
// Response:
{
  "has_founding_benefits": true,
  "pricing_locked_until": "2029-01-01T00:00:00Z",
  "locked_unlock_price_cents": 9900,
  "is_still_locked": true,
  "savings_message": "Save $99.00 per unlock until 2029-01-01"
}
```

## Integration Points

### Billing Service Dependencies

The Financial Management Service expects the following endpoints from the Billing Service:

```
GET /billing/tenants/{tenant_id}/feature-access
Response:
{
  "tier": "solo" | "growth",
  "features": {
    "intake": { "per_use_price_cents": 9900 | 8900 },
    "settle": { "per_use_price_cents": 0 | 9900 }
  },
  "founding_intelligence": {
    "pricing_locked_until": "2029-01-01T00:00:00Z",
    "locked_unlock_price_cents": 9900
  }
}

GET /billing/tenants/{tenant_id}/addons
Response:
{
  "addons": [
    {
      "id": "uuid",
      "name": "Additional Intake Credits",
      "price_cents": 4900,
      "billing_cycle": "one_time",
      "quantity": 5
    }
  ]
}
```

### Environment Configuration

Add these environment variables to `.env`:

```bash
# Billing Service Integration
BILLING_SERVICE_URL=http://localhost:3003
BILLING_SERVICE_API_KEY=your-billing-service-api-key
```

## Testing

### Using Mock Data (Development)

When `BILLING_SERVICE_URL` is not set, the system uses `MockBillingAdapter` which returns:

```python
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

### Running Tests

```bash
# Test pricing endpoints
curl http://localhost:8000/api/v1/fm/pricing/tenants/{tenant_id}/feature-access \
  -H "Authorization: Bearer YOUR_TOKEN"

# Test with query parameters
curl "http://localhost:8000/api/v1/fm/pricing/tenants/{tenant_id}/feature-cost?feature_name=intake&usage_count=75" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Frontend Integration Example

### Hook Usage in React Components

```typescript
import { useToast } from '@/hooks/useToast'
import { apiClient } from '@/lib/apiClient'

function PricingComponent({ tenantId }: { tenantId: string }) {
  const { success, error } = useToast()
  const [pricing, setPricing] = useState(null)

  useEffect(() => {
    async function fetchPricing() {
      try {
        const response = await apiClient.get(`/fm/pricing/tenants/${tenantId}/feature-access`)
        setPricing(response.data)
        success('Pricing information loaded')
      } catch (err) {
        error('Failed to load pricing information')
      }
    }
    
    fetchPricing()
  }, [tenantId])

  if (!pricing) return <div>Loading...</div>

  return (
    <div>
      <h2>Tier: {pricing.tier}</h2>
      {pricing.founding_intelligence && (
        <div className="bg-green-50 p-4 rounded">
          <p className="text-green-800 font-semibold">
            Founding Intelligence Member
          </p>
          <p className="text-green-700 text-sm">
            Locked rate: ${pricing.founding_intelligence.locked_unlock_price_cents / 100}
          </p>
          <p className="text-green-600 text-xs">
            Until {new Date(pricing.founding_intelligence.pricing_locked_until).toLocaleDateString()}
          </p>
        </div>
      )}
    </div>
  )
}
```

## Next Steps

### For Backend Development
1. ✅ Implement pricing schemas
2. ✅ Create pricing service layer
3. ✅ Update billing adapter with pricing methods
4. ✅ Create pricing API routes
5. ⏳ Add integration tests for pricing endpoints
6. ⏳ Configure billing service mock server for testing

### For Frontend Development
1. ✅ Create toast notification system
2. ✅ Implement dynamic breadcrumbs
3. ✅ Build company statistics widget
4. ⏳ Integrate real pricing API calls into UI components
5. ⏳ Add pricing display components
6. ⏳ Create cost calculator UI

### For Billing Service
1. ⏳ Implement `/tenants/{tenant_id}/feature-access` endpoint
2. ⏳ Implement `/tenants/{tenant_id}/addons` endpoint
3. ⏳ Ensure proper authentication via API keys
4. ⏳ Document billing service API endpoints

## Files Changed/Created

### Backend
- ✅ `app/modules/ar/schemas/pricing_schemas.py` (NEW)
- ✅ `app/modules/ar/services/pricing_service.py` (NEW)
- ✅ `app/modules/ar/integrations/billing_adapter.py` (UPDATED)
- ✅ `app/modules/ar/api/routes/pricing_routes.py` (NEW)
- ✅ `app/api/v1/__init__.py` (UPDATED)

### Frontend
- ✅ `frontend/hooks/useCompanyOperations.ts` (NEW)
- ✅ `frontend/hooks/useApprovalWorkflows.ts` (UPDATED)
- ✅ `frontend/components/layout/Breadcrumbs.tsx` (UPDATED)
- ✅ `frontend/components/widgets/CompanyStatsWidget.tsx` (NEW)
- ✅ `frontend/components/layout/Sidebar.tsx` (UPDATED)

## Summary

All three enterprise features have been successfully implemented:

1. **✅ Toast Notifications** - Automatic notifications for all company operations
2. **✅ Dynamic Breadcrumbs** - Contextual navigation with clickable links
3. **✅ Contextual Sidebar** - Company statistics, KPIs, and status definitions

Additionally, the **Pricing Integration** has been fully implemented with:
- Complete backend service layer
- API endpoints for fetching pricing/tier information
- Founding Intelligence pricing lock support
- Add-on purchase retrieval
- Cost calculation based on usage

The system is production-ready pending Billing Service endpoint availability.
