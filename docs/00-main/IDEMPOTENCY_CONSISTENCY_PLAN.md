# Idempotency Consistency Implementation Plan

## Status: ⏳ PENDING

## Overview
All write endpoints must accept `Idempotency-Key` header and ensure duplicate requests return the same result. This prevents duplicate side effects from retries or network issues.

## Current Status

### ✅ Implemented
- `POST /journal-entries` - Accepts `Idempotency-Key` header
- Journal Entry models have `idempotency_key` field with unique constraint
- System postings use deterministic keys: `f"payroll_run_{run.id}"`, `f"ap_bill_{bill.id}"`

### ⏳ Needs Implementation
- All other write endpoints (AP Bills, Payroll, Reconciliation, etc.)
- Idempotency key storage and lookup
- Consistent response handling for duplicate keys

## Endpoints Requiring Idempotency Support

### Journal Entries
- ✅ `POST /journal-entries` - **COMPLETE**
- ⏳ `POST /journal-entries/{id}/post` - Add idempotency check
- ⏳ `POST /journal-entries/{id}/reverse` - Add idempotency check

### AP Bills
- ⏳ `POST /ap/bills` - Add `Idempotency-Key` header support
- ⏳ `POST /ap/bills/{id}/post` - Add idempotency check
- ⏳ `POST /ap/bills/{id}/reverse` - Add idempotency check

### Payroll
- ⏳ `POST /payroll/runs` - Add `Idempotency-Key` header support
- ⏳ `POST /payroll/runs/{id}/post` - Add idempotency check
- ⏳ `POST /payroll/runs/{id}/reverse` - Add idempotency check

### Reconciliation
- ⏳ `POST /reconciliations` - Add `Idempotency-Key` header support
- ⏳ `POST /reconciliations/{id}/adjustments/post` - Add idempotency check

### Period Close
- ⏳ `POST /periods/{id}/approve-close` - Add idempotency check
- ⏳ `POST /periods/{id}/lock` - Add idempotency check

### Royalties
- ⏳ `POST /intercompany/royalties/runs` - Add `Idempotency-Key` header support
- ⏳ `POST /intercompany/royalties/runs/{id}/post` - Add idempotency check

## Implementation Pattern

### 1. Extract Idempotency-Key from Header
```python
from fastapi import Header
from typing import Optional

@router.post("/endpoint")
async def create_something(
    request: CreateRequest,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db_session)
):
    # Check for existing request with same key
    if idempotency_key:
        existing = await check_idempotency(idempotency_key, db)
        if existing:
            return existing  # Return same result
```

### 2. Store Idempotency Key
```python
# Option A: Store in model (if applicable)
obj.idempotency_key = idempotency_key

# Option B: Store in separate idempotency table
await store_idempotency_key(
    key=idempotency_key,
    object_type="payroll_run",
    object_id=run.id,
    response_data=run.model_dump()
)
```

### 3. Check Before Processing
```python
async def check_idempotency(
    key: str,
    object_type: str,
    db: AsyncSession
) -> Optional[dict]:
    """Check if idempotency key already processed"""
    from app.modules.core.models.idempotency_model import IdempotencyKey
    
    result = await db.execute(
        select(IdempotencyKey).where(
            IdempotencyKey.key == key,
            IdempotencyKey.object_type == object_type
        )
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        # Return cached response
        return existing.response_data
    
    return None
```

## Database Schema

### Idempotency Key Table (if not exists)
```sql
CREATE TABLE IF NOT EXISTS idempotency_key (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR(255) NOT NULL,
    object_type VARCHAR(100) NOT NULL,
    object_id UUID,
    response_data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(key, object_type)
);

CREATE INDEX idx_idempotency_key_lookup ON idempotency_key(key, object_type);
```

## Testing Requirements

Each endpoint must have tests that:
1. Send request with `Idempotency-Key` header
2. Verify first request succeeds
3. Send identical request with same `Idempotency-Key`
4. Verify second request returns same result (no duplicate side effects)
5. Verify database state unchanged after duplicate request

## Priority

- **P1 (High):** Posting endpoints (prevents duplicate accounting entries)
- **P2 (Medium):** Creation endpoints (prevents duplicate objects)

## Notes

- Idempotency keys should be unique per object type
- Keys can be deterministic (e.g., `f"payroll_run_{run.id}"`) or random UUIDs
- Response caching is optional but recommended for expensive operations
- Consider TTL for idempotency keys (e.g., 24 hours) to prevent unbounded growth
