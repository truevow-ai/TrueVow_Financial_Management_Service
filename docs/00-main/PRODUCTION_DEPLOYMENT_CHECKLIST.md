# Production Deployment Checklist

**Date:** January 25, 2026  
**Status:** ✅ Ready for Deployment (After Runtime Verification)

---

## Pre-Deployment Checklist

### ✅ Code Changes Complete

- [x] Payroll guard: Check for existing JE with source_key before creating
- [x] 425 → 409: Changed to 409 with `IDEMPOTENCY_IN_PROGRESS` code
- [x] Retry-After header: Included on 409 response
- [x] Source key standardization: All 17 endpoints documented

### ⏳ Runtime Verification Required

**Run these 5 tests ONCE before production:**

1. **Test A: Concurrent Post**
   - Send 2 simultaneous JE POST requests with same key
   - Expected: One runs, second returns 409 with Retry-After, third retry replays COMPLETED

2. **Test B: Kill Mid-Flight (Stuck PENDING)**
   - Start BANK_TX_IMPORT, kill worker mid-handler
   - Wait TTL+10s (610s for BANK_TX_IMPORT)
   - Retry with same key
   - Expected: Stale lock transitions to FAILED, request proceeds, no duplicates

3. **Test C: FAILED Retry Blocked Unless Safe**
   - Force FAILED state for temporarily unsafe endpoint
   - Verify retry refused without Retry-Idempotency header
   - Restore safety setting

4. **Test D: Response Status Replay**
   - Create endpoint returning 204
   - Verify replay returns 204 exactly

5. **Test E: Slow Handler vs TTL**
   - Simulate handler runtime 150s on 600s TTL
   - Confirm second request never takes over

**Test File:** `tests/test_idempotency_runtime_verification.py`

---

## Deployment Steps

### 1. Migrations

```bash
# Apply migrations
alembic upgrade head

# Verify schema
psql -d your_db -c "\d idempotency_keys"
psql -d your_db -c "\d journal_entry"
```

**Expected:**
- `idempotency_keys` table has `state`, `locked_at` columns
- `journal_entry` table has `source_key`, `legal_entity_id` columns
- Unique constraints exist

### 2. Unit Tests

```bash
# Run all tests
pytest tests/ -v

# Run idempotency tests specifically
pytest tests/test_idempotency_replay.py -v
pytest tests/test_idempotency_runtime_verification.py -v
```

**Expected:** All tests pass

### 3. Runtime Verification

Execute the 5 runtime tests manually or via test suite.

**Expected:** All 5 tests pass

### 4. Smoke Tests (Manual)

After deployment, verify:

1. **JE Post/Reverse:**
   - Create JE draft → post → replay post (same key) → no duplication
   - Reverse JE → replay reverse (same key) → no duplication

2. **Payroll:**
   - Post payroll run → replay post (same key) → no duplication
   - Verify guard works: Post twice with different idempotency keys → only one JE

3. **Bank Import:**
   - Import CSV → replay import (same key) → no duplication
   - Verify atomicity: Kill mid-import → retry → skips duplicates, completes rest

4. **Reconciliation:**
   - Create session → suggestions → adjustment batch post → close
   - Verify close does NOT post adjustments

---

## Go/No-Go Decision

### ✅ GO if ALL are true:

- [ ] Migrations applied cleanly on staging
- [ ] `pytest tests/ -v` passes
- [ ] All 5 runtime verification tests pass
- [ ] Smoke tests pass
- [ ] Source key standardization verified (no collisions)

### ❌ NO-GO if ANY are false:

- [ ] Fix failing tests
- [ ] Re-verify runtime tests
- [ ] Re-check source key collisions

---

## Post-Deployment Monitoring

### Key Metrics to Watch:

1. **Idempotency Hit Rate:**
   - Monitor `idempotency_keys` table for COMPLETED replays
   - Should see high replay rate for retries

2. **Stale Lock Detection:**
   - Monitor logs for "Stale PENDING lock detected" warnings
   - Should be rare (< 0.1% of requests)

3. **409 Responses:**
   - Monitor API logs for 409 with `IDEMPOTENCY_IN_PROGRESS`
   - Should see Retry-After header on all 409s

4. **Source Key Violations:**
   - Monitor for `DuplicateEntryError` on source_key
   - Should be zero (indicates guard working)

5. **Handler Runtime:**
   - Monitor handler execution times
   - Ensure all handlers complete within TTL

---

## Rollback Plan

If issues detected:

1. **Immediate Rollback:**
   ```bash
   alembic downgrade -1
   ```

2. **Code Rollback:**
   - Revert to previous commit
   - Restart services

3. **Data Integrity:**
   - Verify no duplicate JEs created
   - Check idempotency_keys table for orphaned records

---

**Status:** ✅ Ready for Production (after runtime verification)
