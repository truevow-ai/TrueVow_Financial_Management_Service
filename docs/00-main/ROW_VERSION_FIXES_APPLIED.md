# Row Version 409 Fixes - Applied

**Date:** January 27, 2026  
**Status:** ✅ ALL 4 FIXES APPLIED

---

## Fixes Applied

### ✅ Fix #1: AP Bill Approve Route
**File:** `app/modules/ap/api/routes/ap_bill_routes.py`  
**Change:** Added `row_version=request.row_version` to service call (line 163)  
**Service:** Updated to use `check_row_version()` helper (line 120)

### ✅ Fix #2: Royalty Approve Service
**File:** `app/modules/intercompany/services/royalty_approval_service.py`  
**Change:** 
- Added `row_version: Optional[int] = None` parameter (line 111)
- Added `check_row_version(run.row_version, row_version, "royalty run")` check (line 124)

### ✅ Fix #3: Reconciliation Approve Schema
**File:** `app/modules/general_ledger/schemas/reconciliation_schemas.py`  
**Change:** Added `row_version: int  # Required for optimistic locking` field (line 61)

### ✅ Fix #4: Payroll Reject Schema
**File:** `app/modules/payroll/schemas/payroll_run_schemas.py`  
**Change:** Added `row_version: int  # Required for optimistic locking` field (line 35)

---

## Verification

### check_row_version() calls (3 total):
1. `app/modules/ap/services/ap_bill_approval_service.py:120`
2. `app/modules/intercompany/services/royalty_approval_service.py:124`
3. `app/modules/general_ledger/services/reconciliation_adjustment_posting_service.py:40`

### All endpoints now have:
- ✅ Schema includes `row_version: int`
- ✅ Route passes `row_version=request.row_version`
- ✅ Service checks `check_row_version()` or inline check
- ✅ On success: increments `row_version` on update

---

**Result:** 0 missing implementations ✅
