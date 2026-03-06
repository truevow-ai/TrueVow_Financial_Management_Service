# Financial Management Service Agent - Pricing Integration Specification

**Version:** 1.0  
**Date:** February 16, 2026  
**Status:** Ready for Implementation  

---

## Purpose

This specification defines the integration contract between the **Financial Management Service** and the **Billing Service** for:
- Billing validation
- Pricing verification  
- Revenue recognition
- Invoice validation
- Revenue forecasting
- Founding Intelligence financial tracking

---

## 1. Unified Feature Access Endpoint

### 1.1 Endpoint Definition

```http
GET /api/v1/billing/tenants/{tenant_id}/feature-access
```

### 1.2 Path Parameters

| Parameter | Type   | Required | Description          |
|-----------|--------|----------|----------------------|
| tenant_id | UUID   | Yes      | Tenant identifier    |

### 1.3 Query Parameters

| Parameter | Type   | Required | Description                                      |
|-----------|--------|----------|--------------------------------------------------|
| user_id   | string | No       | Attorney user ID for founding benefits validation |

### 1.4 Response Structure

```typescript
interface FeatureAccessResponse {
  tenant_id: string;
  tier: 'solo' | 'growth';
  subscription_status: 'trial' | 'active' | 'suspended' | 'cancelled';
  
  // Tier features with pricing
  features: {
    intake: {
      enabled: boolean;
      source: 'tier' | 'addon' | 'founding_benefit' | null;
      per_use_price_cents: number;    // $99.00 or $89.00
      monthly_quota: number;
    };
    settle: {
      enabled: boolean;
      source: 'tier' | 'founding_benefit' | null;
      per_use_price_cents: number;    // $0 if founding member
      monthly_quota: number;
    };
    draft: {
      enabled: boolean;
      source: 'tier' | 'addon' | null;
      per_use_price_cents: number;
      monthly_quota: number;
    };
  };
  
  // Add-on purchases (recurring revenue)
  addons: Array<{
    addon_id: string;             // 'draft-per-use', 'draft-monthly'
    name: string;
    display_name: string;
    status: 'active' | 'cancelled' | 'expired';
    // Price info available via addon details endpoint
  }>;
  
  // Founding Intelligence pricing locks
  founding_intelligence: {
    is_member: boolean;
    user_id: string | null;
    benefits_enabled: boolean;
    pricing_locked_until: string | null;      // ISO timestamp
    locked_unlock_price_cents: number | null; // $99.00 locked for 36 months
    verified_submissions: number;              // Revenue share calculation
    dashboard_access_tier: number;
  } | null;
}
```

---

## 2. Pricing Validation Logic

### 2.1 Get Authoritative Per-Use Price

```typescript
/**
 * Get authoritative per-use price for service from billing data
 */
function getServicePrice(
  featureAccess: FeatureAccessResponse,
  service: 'intake' | 'settle' | 'draft'
): number {
  const feature = featureAccess.features[service];
  
  // Free if from founding benefit
  if (feature.source === 'founding_benefit') {
    return 0;
  }
  
  return feature.per_use_price_cents;
}
```

### 2.2 Validate Invoice Line Item

```typescript
interface ValidationResult {
  valid: boolean;
  discrepancy?: string;
}

/**
 * Validate invoice line item against authoritative pricing
 */
function validateInvoiceLineItem(
  featureAccess: FeatureAccessResponse,
  service: string,
  quantity: number,
  unitPriceCents: number,
  totalAmount: number
): ValidationResult {
  const expectedPrice = getServicePrice(featureAccess, service);
  const expectedTotal = expectedPrice * quantity;
  
  if (unitPriceCents !== expectedPrice) {
    return {
      valid: false,
      discrepancy: `Unit price mismatch: expected ${expectedPrice}, got ${unitPriceCents}`
    };
  }
  
  if (totalAmount !== expectedTotal) {
    return {
      valid: false,
      discrepancy: `Total amount mismatch: expected ${expectedTotal}, got ${totalAmount}`
    };
  }
  
  return { valid: true };
}
```

### 2.3 Calculate Monthly Recurring Revenue (MRR)

```typescript
/**
 * Calculate monthly recurring revenue from tier and add-ons
 */
function calculateMRR(featureAccess: FeatureAccessResponse): number {
  let mrr = 0;
  
  // Base tier MRR
  if (featureAccess.tier === 'solo') {
    mrr += 0; // Solo: pay-per-use, no base MRR
  } else if (featureAccess.tier === 'growth') {
    mrr += 129900; // $1,299/month
  }
  
  // Add-on MRR
  for (const addon of featureAccess.addons) {
    if (addon.status === 'active') {
      if (addon.addon_id === 'draft-monthly') {
        mrr += 49900; // $499/month example
      }
      // Other add-ons...
    }
  }
  
  return mrr;
}
```

### 2.4 Check Pricing Lock Status

```typescript
/**
 * Check if pricing is locked (Founding Intelligence benefit)
 */
function isPricingLocked(featureAccess: FeatureAccessResponse): boolean {
  const foundingMember = featureAccess.founding_intelligence;
  
  if (!foundingMember?.is_member || !foundingMember.pricing_locked_until) {
    return false;
  }
  
  const lockExpiry = new Date(foundingMember.pricing_locked_until);
  return new Date() < lockExpiry;
}
```

### 2.5 Get Locked Pricing Details

```typescript
interface LockedPricingResult {
  locked: boolean;
  priceCents: number;
  expiresAt: string | null;
}

/**
 * Get locked pricing details (if applicable)
 */
function getLockedPricing(featureAccess: FeatureAccessResponse): LockedPricingResult {
  const foundingMember = featureAccess.founding_intelligence;
  
  if (!foundingMember?.is_member || !foundingMember.pricing_locked_until) {
    return { locked: false, priceCents: 9900, expiresAt: null };
  }
  
  return {
    locked: true,
    priceCents: foundingMember.locked_unlock_price_cents || 9900,
    expiresAt: foundingMember.pricing_locked_until
  };
}
```

---

## 3. Example Usage Patterns

### 3.1 Validate Invoice Before Payment Processing

```typescript
class InvoiceValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'InvoiceValidationError';
  }
}

/**
 * Validate invoice against authoritative billing data
 */
async function validateInvoice(tenantId: string, invoiceData: any) {
  const response = await fetch(
    `${BILLING_URL}/api/v1/billing/tenants/${tenantId}/feature-access`,
    {
      headers: {
        'Authorization': `Bearer ${BILLING_API_KEY}`
      }
    }
  );
  
  if (!response.ok) {
    throw new Error(`Billing API error: ${response.status}`);
  }
  
  const featureAccess = await response.json();
  
  // Validate each line item
  for (const lineItem of invoiceData.line_items) {
    const validation = validateInvoiceLineItem(
      featureAccess,
      lineItem.service,
      lineItem.quantity,
      lineItem.unit_price_cents,
      lineItem.total_amount
    );
    
    if (!validation.valid) {
      throw new InvoiceValidationError(
        `Invalid pricing for ${lineItem.service}: ${validation.discrepancy}`
      );
    }
  }
  
  // Calculate expected total
  const expectedTotal = invoiceData.line_items.reduce(
    (sum, item) => sum + item.total_amount,
    0
  );
  
  if (invoiceData.total_amount !== expectedTotal) {
    throw new InvoiceValidationError(
      `Invoice total mismatch: expected ${expectedTotal}, got ${invoiceData.total_amount}`
    );
  }
  
  return { valid: true, expectedTotal };
}
```

### 3.2 Generate Revenue Forecast

```typescript
interface RevenueForecast {
  tenant_id: string;
  tier: string;
  monthly_recurring_revenue: number;
  is_pricing_locked: boolean;
  locked_price: number;
  potential_overage_revenue: number;
  founding_member_revenue_share: number;
}

/**
 * Generate revenue forecast for multiple tenants
 */
async function generateRevenueForecast(tenants: string[]): Promise<RevenueForecast[]> {
  const forecasts: RevenueForecast[] = [];
  
  for (const tenantId of tenants) {
    const response = await fetch(
      `${BILLING_URL}/api/v1/billing/tenants/${tenantId}/feature-access`,
      {
        headers: {
          'Authorization': `Bearer ${BILLING_API_KEY}`
        }
      }
    );
    
    const featureAccess = await response.json();
    
    forecasts.push({
      tenant_id: tenantId,
      tier: featureAccess.tier,
      monthly_recurring_revenue: calculateMRR(featureAccess),
      is_pricing_locked: isPricingLocked(featureAccess),
      locked_price: getLockedPricing(featureAccess).priceCents,
      potential_overage_revenue: estimateOverageRevenue(featureAccess),
      founding_member_revenue_share: calculateRevenueShare(featureAccess)
    });
  }
  
  return forecasts;
}

function estimateOverageRevenue(featureAccess: FeatureAccessResponse): number {
  // Implementation depends on historical usage data
  return 0; // Placeholder
}
```

### 3.3 Calculate Revenue Share for Founding Intelligence

```typescript
/**
 * Calculate revenue share for Founding Intelligence members (15% of verified submissions)
 */
function calculateRevenueShare(featureAccess: FeatureAccessResponse): number {
  const foundingMember = featureAccess.founding_intelligence;
  
  if (!foundingMember?.is_member || !foundingMember.benefits_enabled) {
    return 0;
  }
  
  // 15% revenue share on verified submissions
  const revenuePerSubmission = 150000; // $1,500 example
  const shareRate = 0.15;
  
  return foundingMember.verified_submissions * revenuePerSubmission * shareRate;
}
```

---

## 4. Pricing Discrepancy Detection

### 4.1 Audit Usage Records

```typescript
interface Discrepancy {
  record_id: string;
  service: string;
  expected_price: number;
  actual_price: number;
  difference: number;
  impact: number;
}

interface AuditResult {
  total_records: number;
  discrepancies_found: number;
  total_financial_impact: number;
  discrepancies: Discrepancy[];
}

/**
 * Audit usage records against billing data for pricing discrepancies
 */
async function auditUsageRecords(
  tenantId: string,
  usageRecords: any[]
): Promise<AuditResult> {
  const response = await fetch(
    `${BILLING_URL}/api/v1/billing/tenants/${tenantId}/feature-access`,
    {
      headers: {
        'Authorization': `Bearer ${BILLING_API_KEY}`
      }
    }
  );
  
  const featureAccess = await response.json();
  
  const discrepancies: Discrepancy[] = [];
  
  for (const record of usageRecords) {
    const expectedPrice = getServicePrice(featureAccess, record.service);
    
    if (record.unit_price_cents !== expectedPrice) {
      discrepancies.push({
        record_id: record.id,
        service: record.service,
        expected_price: expectedPrice,
        actual_price: record.unit_price_cents,
        difference: record.unit_price_cents - expectedPrice,
        impact: (record.unit_price_cents - expectedPrice) * record.quantity
      });
    }
  }
  
  return {
    total_records: usageRecords.length,
    discrepancies_found: discrepancies.length,
    total_financial_impact: discrepancies.reduce((sum, d) => sum + d.impact, 0),
    discrepancies
  };
}
```

---

## 5. Founding Intelligence Financial Tracking

### 5.1 Calculate Pricing Lock Exposure

```typescript
/**
 * Calculate financial exposure from pricing locks
 */
function calculatePricingLockExposure(featureAccess: FeatureAccessResponse): number {
  const pricing = getLockedPricing(featureAccess);
  
  if (!pricing.locked) {
    return 0;
  }
  
  // Calculate difference between locked rate and current rate
  const currentRate = 9900; // Current standard rate
  const lockDifference = currentRate - pricing.priceCents;
  
  // Estimate annual exposure (assuming 10 unlocks/year)
  const estimatedAnnualUnlocks = 10;
  return lockDifference * estimatedAnnualUnlocks;
}
```

### 5.2 Generate Founding Member Economics Report

```typescript
interface FoundingMemberReport {
  member_id: string | null;
  is_active: boolean;
  pricing_lock_value: number;
  revenue_share_earned: number;
  verified_contributions: number;
  dashboard_tier: number;
  lock_expires: string | null;
}

/**
 * Generate comprehensive founding member economics report
 */
function generateFoundingMemberReport(
  featureAccess: FeatureAccessResponse
): FoundingMemberReport | null {
  const foundingMember = featureAccess.founding_intelligence;
  
  if (!foundingMember?.is_member) {
    return null;
  }
  
  return {
    member_id: foundingMember.user_id,
    is_active: foundingMember.benefits_enabled,
    pricing_lock_value: calculatePricingLockExposure(featureAccess),
    revenue_share_earned: calculateRevenueShare(featureAccess),
    verified_contributions: foundingMember.verified_submissions,
    dashboard_tier: foundingMember.dashboard_access_tier,
    lock_expires: foundingMember.pricing_locked_until
  };
}
```

---

## 6. Error Handling

### 6.1 HTTP Error Codes

```typescript
// 404 - Tenant not found in billing system
if (response.status === 404) {
  throw new Error(`Tenant ${tenantId} not found - cannot validate pricing`);
}

// 400 - Invalid tenant ID format
if (response.status === 400) {
  throw new ValidationError('Invalid tenant ID format');
}

// 500 - Billing service unavailable
if (response.status === 500) {
  // For financial operations, fail closed
  throw new ServiceUnavailableError(
    'Billing service unavailable - cannot process financial transaction'
  );
}

// Data integrity check
if (!data.features || !data.tier) {
  throw new DataIntegrityError('Malformed feature access response');
}
```

### 6.2 Custom Error Classes

```typescript
class ValidationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ValidationError';
  }
}

class ServiceUnavailableError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'ServiceUnavailableError';
  }
}

class DataIntegrityError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'DataIntegrityError';
  }
}
```

---

## 7. Reconciliation Reports

### 7.1 Daily Revenue Reconciliation

```typescript
interface DailyReconciliation {
  date: string;
  total_tenants: number;
  by_tier: {
    solo: number;
    growth: number;
  };
  total_mrr: number;
  founding_members: number;
  pricing_locks_active: number;
  total_revenue_share_liability: number;
}

/**
 * Perform daily revenue reconciliation across all active tenants
 */
async function dailyRevenueReconciliation(date: string): Promise<DailyReconciliation> {
  // Get all active tenants from database
  const activeTenants = await getActiveTenants();
  
  const reconciliation: DailyReconciliation = {
    date,
    total_tenants: activeTenants.length,
    by_tier: {
      solo: 0,
      growth: 0
    },
    total_mrr: 0,
    founding_members: 0,
    pricing_locks_active: 0,
    total_revenue_share_liability: 0
  };
  
  for (const tenant of activeTenants) {
    const response = await fetch(
      `${BILLING_URL}/api/v1/billing/tenants/${tenant.id}/feature-access`,
      {
        headers: {
          'Authorization': `Bearer ${BILLING_API_KEY}`
        }
      }
    );
    
    const data = await response.json();
    
    reconciliation.by_tier[data.tier]++;
    reconciliation.total_mrr += calculateMRR(data);
    
    if (data.founding_intelligence?.is_member) {
      reconciliation.founding_members++;
      
      if (isPricingLocked(data)) {
        reconciliation.pricing_locks_active++;
      }
      
      reconciliation.total_revenue_share_liability += 
        calculateRevenueShare(data);
    }
  }
  
  return reconciliation;
}

async function getActiveTenants(): Promise<Array<{ id: string }>> {
  // Query database for active tenants
  return []; // Placeholder
}
```

---

## 8. Implementation Checklist

### 8.1 Backend Requirements

- [ ] Implement `GET /api/v1/billing/tenants/{tenant_id}/feature-access` endpoint
- [ ] Ensure response includes all fields specified in Section 1.4
- [ ] Support optional `user_id` query parameter for founding benefits
- [ ] Return proper HTTP status codes (200, 400, 404, 500)
- [ ] Include CORS headers for cross-origin requests
- [ ] Implement rate limiting (e.g., 100 requests/minute per API key)
- [ ] Log all pricing endpoint accesses for audit trail

### 8.2 Frontend Integration

- [ ] Create TypeScript types matching response structure
- [ ] Implement pricing validation hooks
- [ ] Add invoice validation UI component
- [ ] Create revenue forecasting dashboard widget
- [ ] Display founding member benefits status
- [ ] Show pricing lock expiry warnings (30 days before)

### 8.3 Testing Requirements

- [ ] Unit tests for all pricing validation functions
- [ ] Integration tests with mock billing service
- [ ] End-to-end tests for invoice validation workflow
- [ ] Load testing for concurrent pricing checks
- [ ] Verify zero tolerance for pricing discrepancies

---

## 9. Environment Configuration

### 9.1 Required Environment Variables

```bash
# Billing Service Configuration
BILLING_SERVICE_URL=http://localhost:3003
BILLING_SERVICE_API_KEY=your-billing-service-api-key

# Financial Management Service
FINANCIAL_MANAGEMENT_SERVICE_URL=http://localhost:8000
```

### 9.2 API Key Authentication

All requests to the billing service must include:

```http
Authorization: Bearer {BILLING_SERVICE_API_KEY}
```

---

## 10. Data Integrity Guarantees

### 10.1 Immutability

- Pricing data returned from billing service is considered **authoritative**
- Financial Management Service MUST NOT cache pricing data for >5 minutes
- All pricing validations must fetch fresh data from billing service

### 10.2 Audit Trail

All pricing validation operations must log:
- Timestamp
- Tenant ID
- User ID (if available)
- Service being validated
- Expected vs actual price
- Validation result (pass/fail)

### 10.3 Zero-Error Validation

- **No tolerance** for pricing discrepancies
- Any discrepancy > $0.01 must trigger immediate alert
- Failed validations must block financial transactions
- Manual override requires supervisor approval + audit log

---

## 11. Performance Requirements

### 11.1 Response Time SLA

- P95 latency: < 200ms
- P99 latency: < 500ms
- Timeout: 5 seconds

### 11.2 Availability SLA

- Uptime: 99.9%
- Maintenance window: Sundays 2-4 AM UTC
- Emergency maintenance: As needed with 24h notice

---

## 12. Security Considerations

### 12.1 Data Protection

- All pricing data transmitted over HTTPS only
- API keys stored in secure vault (never in code)
- Tenant IDs validated against authorization context
- Rate limiting to prevent abuse

### 12.2 Access Control

- Only authenticated users can access pricing data
- Tenant-scoped access (users can only see their tenant's data)
- Admin override requires elevated privileges
- All access logged for compliance

---

## Appendix A: Complete Response Example

```json
{
  "tenant_id": "968576f1-15bc-4adf-b450-3e53d0553c5a",
  "tier": "growth",
  "subscription_status": "active",
  "features": {
    "intake": {
      "enabled": true,
      "source": "tier",
      "per_use_price_cents": 8900,
      "monthly_quota": 50
    },
    "settle": {
      "enabled": true,
      "source": "founding_benefit",
      "per_use_price_cents": 0,
      "monthly_quota": 10
    },
    "draft": {
      "enabled": true,
      "source": "addon",
      "per_use_price_cents": 4900,
      "monthly_quota": 25
    }
  },
  "addons": [
    {
      "addon_id": "draft-monthly",
      "name": "Draft Monthly Plan",
      "display_name": "Draft Pro",
      "status": "active"
    }
  ],
  "founding_intelligence": {
    "is_member": true,
    "user_id": "attorney-123",
    "benefits_enabled": true,
    "pricing_locked_until": "2029-01-01T00:00:00Z",
    "locked_unlock_price_cents": 9900,
    "verified_submissions": 15,
    "dashboard_access_tier": 3
  }
}
```

---

## Appendix B: Quick Reference

| Function | Purpose | Returns |
|----------|---------|---------|
| `getServicePrice()` | Get authoritative price | `number` (cents) |
| `validateInvoiceLineItem()` | Validate line item | `{valid, discrepancy}` |
| `calculateMRR()` | Calculate monthly revenue | `number` (cents) |
| `isPricingLocked()` | Check lock status | `boolean` |
| `getLockedPricing()` | Get lock details | `{locked, priceCents, expiresAt}` |
| `calculateRevenueShare()` | Calculate 15% share | `number` (cents) |
| `auditUsageRecords()` | Detect discrepancies | `AuditResult` |
| `dailyRevenueReconciliation()` | Daily report | `DailyReconciliation` |

---

**END OF SPECIFICATION**
