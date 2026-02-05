# Handler Atomicity Verification

**Date:** January 25, 2026  
**Status:** ⚠️ Verification Required

---

## Posting Handlers - Transaction Atomicity

### ✅ Journal Entry Posting
**File:** `app/modules/general_ledger/services/journal_entry_service.py::post_entry()`

**Transaction Pattern:**
- Single `await self.session.commit()` at end (line 241)
- All updates happen before commit
- **Atomic:** ✅ Yes

**Verification:**
```python
# All operations before commit:
- Validate entry
- Check period status
- Verify balance
- Check source_key uniqueness
- Update entry status
await self.session.commit()  # Single commit
```

### ⚠️ Payroll Posting
**File:** `app/modules/payroll/services/payroll_run_service.py::post_run()`

**Need to verify:**
- Does it commit mid-way?
- Does it use single transaction?

**Action Required:** Check if `post_run()` commits before creating journal entry.

### ⚠️ Bank Transaction Import
**File:** `app/modules/treasury/services/bank_transaction_service.py::import_csv_transactions()`

**Current Pattern:**
- Calls `create_transaction()` for each row
- `create_transaction()` commits per transaction (line 70)
- **NOT atomic** - partial imports possible

**Issue:**
- If handler fails mid-import, some transactions are committed
- Retry would skip duplicates (external_id) but incomplete state remains

**Fix Required:**
- Use batch insert with single commit
- Or use import_batch_id to track progress and allow resume

---

## Import Endpoints - Batch Safety

### Bank TX Import
**Uniqueness Guards:**
- ✅ `external_id` unique constraint (prevents duplicate rows)
- ✅ `import_batch_id` tracks batch

**Issue:**
- Commits per transaction (not atomic batch)
- Retry would skip duplicates but may leave incomplete batch

**Recommendation:**
- Change to batch insert with single commit
- Or document that partial imports are acceptable (skip duplicates on retry)

### Treasury Sync
**Uniqueness Guards:**
- ✅ `sync_batch_id` unique constraint
- ✅ Uses batch tracking

**Need to verify:** Does it commit atomically?

### Billing Sync
**Uniqueness Guards:**
- ✅ `since_cursor` prevents duplicate syncs

**Need to verify:** Does it commit atomically?

---

## Response Size Audit

### Endpoints That May Exceed 100KB

1. **BANK_TX_IMPORT**
   - Current: Returns `{"created": N, "skipped": M, "total": T}`
   - ✅ Already summary format
   - **Safe:** ✅

2. **TREASURY_SYNC**
   - Current: Returns sync summary
   - **Need to verify:** Response format

3. **BILLING_SYNC**
   - Current: Returns sync summary
   - **Need to verify:** Response format

4. **TREASURY_SYNC_POST_TX**
   - Current: Returns batch summary
   - **Need to verify:** Response format

**Action:** Verify all import/sync endpoints return summaries, not full data.

---

## Required Fixes

### 1. Endpoint-Specific TTL ✅
- Implemented `get_lock_ttl_seconds(endpoint_key)`
- TTL values set per endpoint (30s to 15 minutes)

### 2. Handler Atomicity ⚠️
- **Journal Entry:** ✅ Atomic (single commit)
- **Payroll:** ⚠️ Need to verify
- **Bank Import:** ❌ NOT atomic (commits per transaction)
- **Treasury Sync:** ⚠️ Need to verify
- **Billing Sync:** ⚠️ Need to verify

### 3. Response Size ✅
- Truncation implemented
- Need to verify import endpoints return summaries

### 4. Naive Datetime Logging ✅
- Added warning log when normalizing naive datetimes

---

## Next Steps

1. **Verify Payroll Handler:**
   - Check if `post_run()` uses single transaction
   - Ensure no mid-way commits

2. **Fix Bank Import:**
   - Change to batch insert with single commit
   - Or document partial import behavior

3. **Verify Sync Handlers:**
   - Check transaction atomicity
   - Verify batch tracking

4. **Audit Response Formats:**
   - Ensure all import/sync endpoints return summaries
