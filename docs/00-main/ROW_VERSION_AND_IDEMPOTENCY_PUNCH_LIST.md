# Row Version 409 & Idempotency Implementation Punch List

**Status:** 🚧 IN PROGRESS  
**Date:** January 25, 2026  
**Goal:** Complete concurrency protection and idempotency across all write endpoints

---

## Part 1: Row Version 409 Conflicts (15 endpoints)

### Pattern Template (Payroll Approve - ✅ COMPLETE)
- **Schema:** `PayrollRunApproveRequest.row_version: int`
- **Service:** Check `if row_version != obj.row_version: raise HTTPException(409, ...)`
- **Route:** Pass `row_version=request.row_version` to service

---

### Payroll (3 remaining)
1. **`POST /books/{book_id}/payroll/runs/{run_id}/submit-approval`**
   - **File:** `app/modules/payroll/schemas/payroll_run_schemas.py`
   - **Schema:** `PayrollRunSubmitApprovalRequest` - Add `row_version: int`
   - **Service:** `app/modules/payroll/services/payroll_approval_service.py::submit_for_approval()` - Add `row_version: Optional[int]` param, check before update
   - **Route:** `app/modules/payroll/api/routes/payroll_run_routes.py::submit_payroll_for_approval()` - Pass `row_version=request.row_version`

2. **`POST /books/{book_id}/payroll/runs/{run_id}/reject`**
   - **File:** `app/modules/payroll/schemas/payroll_run_schemas.py`
   - **Schema:** `PayrollRunRejectRequest` - Add `row_version: int`
   - **Service:** `app/modules/payroll/services/payroll_approval_service.py::reject()` - Add `row_version: Optional[int]` param, check before update
   - **Route:** `app/modules/payroll/api/routes/payroll_run_routes.py::reject_payroll_run()` - Pass `row_version=request.row_version`

3. **`POST /books/{book_id}/payroll/runs/{run_id}/post`**
   - **File:** `app/modules/payroll/schemas/payroll_run_schemas.py`
   - **Schema:** `PayrollRunPostRequest` - Add `row_version: int`
   - **Service:** `app/modules/payroll/services/payroll_run_service.py::post_run()` - Add `row_version: Optional[int]` param, check before update
   - **Route:** `app/modules/payroll/api/routes/payroll_run_routes.py::post_payroll_run()` - Pass `row_version=request.row_version`

---

### AP Bills (4 endpoints)
4. **`POST /books/{book_id}/ap/bills/{bill_id}/submit-approval`**
   - **File:** `app/modules/ap/schemas/ap_bill_schemas.py`
   - **Schema:** `APBillSubmitApprovalRequest` - Add `row_version: int`
   - **Service:** `app/modules/ap/services/ap_bill_approval_service.py::submit_for_approval()` - Add `row_version: Optional[int]` param, check before update
   - **Route:** `app/modules/ap/api/routes/ap_bill_routes.py::submit_bill_for_approval()` - Pass `row_version=request.row_version`

5. **`POST /books/{book_id}/ap/bills/{bill_id}/approve`**
   - **File:** `app/modules/ap/schemas/ap_bill_schemas.py`
   - **Schema:** `APBillApproveRequest` - Add `row_version: int`
   - **Service:** `app/modules/ap/services/ap_bill_approval_service.py::approve()` - Add `row_version: Optional[int]` param, check before update
   - **Route:** `app/modules/ap/api/routes/ap_bill_routes.py::approve_bill()` - Pass `row_version=request.row_version`

6. **`POST /books/{book_id}/ap/bills/{bill_id}/reject`**
   - **File:** `app/modules/ap/schemas/ap_bill_schemas.py`
   - **Schema:** `APBillRejectRequest` - Add `row_version: int`
   - **Service:** `app/modules/ap/services/ap_bill_approval_service.py::reject()` - Add `row_version: Optional[int]` param, check before update
   - **Route:** `app/modules/ap/api/routes/ap_bill_routes.py::reject_bill()` - Pass `row_version=request.row_version`

7. **`POST /books/{book_id}/ap/bills/{bill_id}/post`**
   - **File:** `app/modules/ap/schemas/ap_bill_schemas.py`
   - **Schema:** `APBillPostRequest` - Add `row_version: int`
   - **Service:** `app/modules/ap/services/ap_bill_service.py::post_bill()` - Add `row_version: Optional[int]` param, check before update
   - **Route:** `app/modules/ap/api/routes/ap_bill_routes.py::post_bill()` - Pass `row_version=request.row_version`

---

### Reconciliation Adjustments (3 endpoints)
8. **`POST /books/{book_id}/reconciliations/{rec_id}/adjustments/submit-approval`**
   - **File:** `app/modules/general_ledger/schemas/reconciliation_schemas.py`
   - **Schema:** `ReconciliationAdjustmentSubmitRequest` - Add `row_version: int`
   - **Service:** `app/modules/general_ledger/services/reconciliation_approval_service.py::submit_for_approval()` - Add `row_version: Optional[int]` param, check before update
   - **Route:** `app/modules/general_ledger/api/routes/reconciliation_routes.py::submit_adjustment_for_approval()` - Pass `row_version=request.row_version`

9. **`POST /books/{book_id}/reconciliations/{rec_id}/adjustments/approve`**
   - **File:** `app/modules/general_ledger/schemas/reconciliation_schemas.py`
   - **Schema:** `ReconciliationAdjustmentApproveRequest` - Add `row_version: int`
   - **Service:** `app/modules/general_ledger/services/reconciliation_approval_service.py::approve()` - Add `row_version: Optional[int]` param, check before update
   - **Route:** `app/modules/general_ledger/api/routes/reconciliation_routes.py::approve_adjustment()` - Pass `row_version=request.row_version`

10. **`POST /books/{book_id}/reconciliations/{rec_id}/adjustments/reject`**
    - **File:** `app/modules/general_ledger/schemas/reconciliation_schemas.py`
    - **Schema:** `ReconciliationAdjustmentRejectRequest` - Add `row_version: int`
    - **Service:** `app/modules/general_ledger/services/reconciliation_approval_service.py::reject()` - Add `row_version: Optional[int]` param, check before update
    - **Route:** `app/modules/general_ledger/api/routes/reconciliation_routes.py::reject_adjustment()` - Pass `row_version=request.row_version`

---

### Period Close (2 endpoints)
11. **`POST /books/{book_id}/periods/{period_id}/submit-close`**
    - **File:** `app/modules/general_ledger/schemas/period_schemas.py`
    - **Schema:** `PeriodSubmitCloseRequest` - Add `row_version: int`
    - **Service:** `app/modules/general_ledger/services/period_close_approval_service.py::submit_for_close()` - Add `row_version: Optional[int]` param, check before update
    - **Route:** `app/modules/general_ledger/api/routes/period_routes.py::submit_period_for_close()` - Pass `row_version=request.row_version`

12. **`POST /books/{book_id}/periods/{period_id}/approve-close`**
    - **File:** `app/modules/general_ledger/schemas/period_schemas.py`
    - **Schema:** `PeriodApproveCloseRequest` - Add `row_version: int`
    - **Service:** `app/modules/general_ledger/services/period_close_approval_service.py::approve_close()` - Add `row_version: Optional[int]` param, check before update
    - **Route:** `app/modules/general_ledger/api/routes/period_routes.py::approve_period_close()` - Pass `row_version=request.row_version`

---

### Royalties (3 endpoints)
13. **`POST /books/{book_id}/intercompany/royalties/runs/{run_id}/submit-approval`**
    - **File:** `app/modules/intercompany/schemas/royalty_schemas.py`
    - **Schema:** `RoyaltySubmitApprovalRequest` - Add `row_version: int`
    - **Service:** `app/modules/intercompany/services/royalty_approval_service.py::submit_for_approval()` - Add `row_version: Optional[int]` param, check before update
    - **Route:** `app/modules/intercompany/api/routes/royalty_routes.py::submit_royalty_for_approval()` - Pass `row_version=request.row_version`

14. **`POST /books/{book_id}/intercompany/royalties/runs/{run_id}/approve`**
    - **File:** `app/modules/intercompany/schemas/royalty_schemas.py`
    - **Schema:** `RoyaltyApproveRequest` - Add `row_version: int`
    - **Service:** `app/modules/intercompany/services/royalty_approval_service.py::approve()` - Add `row_version: Optional[int]` param, check before update
    - **Route:** `app/modules/intercompany/api/routes/royalty_routes.py::approve_royalty()` - Pass `row_version=request.row_version`

15. **`POST /books/{book_id}/intercompany/royalties/runs/{run_id}/reject`**
    - **File:** `app/modules/intercompany/schemas/royalty_schemas.py`
    - **Schema:** `RoyaltyRejectRequest` - Add `row_version: int`
    - **Service:** `app/modules/intercompany/services/royalty_approval_service.py::reject()` - Add `row_version: Optional[int]` param, check before update
    - **Route:** `app/modules/intercompany/api/routes/royalty_routes.py::reject_royalty()` - Pass `row_version=request.row_version`

---

### PATCH Endpoints (2 endpoints - Lower Priority)
16. **`PATCH /books/{book_id}/treasury/bank-accounts/{account_id}`**
    - **File:** `app/modules/treasury/schemas/bank_account_schemas.py`
    - **Schema:** `BankAccountUpdateRequest` - Add `row_version: int`
    - **Service:** `app/modules/treasury/services/bank_account_service.py::update_account()` - Add `row_version: Optional[int]` param, check before update
    - **Route:** `app/modules/treasury/api/routes/bank_account_routes.py::update_bank_account()` - Pass `row_version=request.row_version`

17. **`PATCH /books/{book_id}/accounts/{account_id}`**
    - **File:** `app/modules/general_ledger/schemas/coa_schemas.py`
    - **Schema:** `GLAccountUpdateRequest` - Add `row_version: int`
    - **Service:** `app/modules/general_ledger/services/coa_service.py::update_account()` - Add `row_version: Optional[int]` param, check before update
    - **Route:** `app/modules/general_ledger/api/routes/coa_routes.py::update_account()` - Pass `row_version=request.row_version`

---

## Part 2: Idempotency Support (40+ endpoints)

### Pattern Template
- **Dependency:** Create `get_idempotency_key()` dependency to extract header
- **Service:** Check existing key before processing, store key after success
- **Route:** Use dependency, pass key to service

---

### Critical Posting Endpoints (P1 - High Priority)
1. **`POST /books/{book_id}/journal-entries/{entry_id}/post`**
2. **`POST /books/{book_id}/journal-entries/{entry_id}/reverse`**
3. **`POST /books/{book_id}/ap/bills/{bill_id}/post`**
4. **`POST /books/{book_id}/payroll/runs/{run_id}/post`**
5. **`POST /books/{book_id}/payroll/runs/{run_id}/reverse`**
6. **`POST /books/{book_id}/intercompany/royalties/calculations/{calculation_id}/post`**
7. **`POST /books/{book_id}/intercompany/transfers/{transfer_id}/post`**
8. **`POST /books/{book_id}/ar/invoices/{invoice_id}/post`**
9. **`POST /books/{book_id}/periods/{period_id}/lock`**
10. **`POST /books/{book_id}/treasury/sync/post-transactions`**

### Creation Endpoints (P2 - Medium Priority)
11. **`POST /books/{book_id}/journal-entries`** - ✅ Already has idempotency_key field
12. **`POST /books/{book_id}/ap/bills`**
13. **`POST /books/{book_id}/payroll/runs`**
14. **`POST /books/{book_id}/reconciliations`**
15. **`POST /books/{book_id}/intercompany/royalties/calculate`**
16. **`POST /books/{book_id}/intercompany/transfers`**
17. **`POST /books/{book_id}/treasury/bank-accounts`**
18. **`POST /books/{book_id}/treasury/transfers`**
19. **`POST /books/{book_id}/treasury/fx-conversions`**
20. **`POST /books/{book_id}/treasury/settlements`**
21. **`POST /books/{book_id}/accounts`**
22. **`POST /books/{book_id}/journal-entries/{entry_id}/lines:bulkUpsert`**

### Bulk Operations (P2 - Medium Priority)
23. **`POST /books/{book_id}/ap/bills/{bill_id}/lines:bulkUpsert`**
24. **`POST /books/{book_id}/payroll/runs/{run_id}/adjustments:bulkUpsert`**

---

## Implementation Order

### Phase 1: Row Version (15 endpoints) - **DO THIS FIRST**
1. Payroll (3) - submit, reject, post
2. AP Bills (4) - submit, approve, reject, post
3. Reconciliation (3) - submit, approve, reject
4. Period Close (2) - submit-close, approve-close
5. Royalties (3) - submit, approve, reject

### Phase 2: Idempotency Middleware (Infrastructure)
1. Create `IdempotencyKey` model if not exists
2. Create `get_idempotency_key()` dependency
3. Create `check_and_store_idempotency()` helper function

### Phase 3: Idempotency (Critical Posting - 10 endpoints)
1. Journal Entry post/reverse
2. AP Bill post
3. Payroll post/reverse
4. Royalty post
5. Intercompany transfer post
6. AR invoice post
7. Period lock
8. Treasury sync post-transactions

### Phase 4: Idempotency (Creation & Bulk - 14 endpoints)
1. All creation endpoints
2. All bulk upsert endpoints

---

## Helper Function to Create

### `app/core/idempotency.py`
```python
from typing import Optional
from fastapi import Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.modules.core.models.idempotency_model import IdempotencyKey

async def get_idempotency_key(
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> Optional[str]:
    """Extract idempotency key from header"""
    return idempotency_key

async def check_idempotency(
    key: str,
    object_type: str,
    db: AsyncSession
) -> Optional[dict]:
    """Check if idempotency key already processed, return cached response"""
    # Implementation here
    pass

async def store_idempotency(
    key: str,
    object_type: str,
    object_id: UUID,
    response_data: dict,
    db: AsyncSession
):
    """Store idempotency key and response"""
    # Implementation here
    pass
```

### `app/core/row_version.py`
```python
from fastapi import HTTPException, status

def check_row_version(
    current_version: int,
    provided_version: Optional[int],
    object_name: str = "object"
) -> None:
    """Check row version and raise 409 if mismatch"""
    if provided_version is not None and current_version != provided_version:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Row version mismatch for {object_name}. "
                   f"Expected {current_version}, got {provided_version}. "
                   "Please refresh and try again."
        )
```

---

## Testing Checklist

For each endpoint:
- [ ] Test with correct `row_version` → succeeds
- [ ] Test with stale `row_version` → returns 409
- [ ] Test with missing `row_version` → succeeds (if optional) or 400 (if required)
- [ ] Test idempotency: same `Idempotency-Key` twice → same response
- [ ] Test idempotency: different `Idempotency-Key` → different result
- [ ] Test idempotency: same key, different payload → 409 conflict

---

## Status Tracking

- ✅ Payroll approve (template)
- ✅ Payroll submit/reject/post (3) - COMPLETE
- ✅ AP Bills submit/approve/reject/post (4) - COMPLETE
- ✅ Reconciliation submit/approve/reject (3) - COMPLETE
- ✅ Period close submit/approve (2) - COMPLETE
- ✅ Royalties submit/approve/reject (3) - COMPLETE
- ⏳ PATCH endpoints (2) - Lower priority
- ⏳ Idempotency infrastructure
- ⏳ Idempotency posting endpoints (10)
- ⏳ Idempotency creation endpoints (14)
