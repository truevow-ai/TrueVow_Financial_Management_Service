# Row Version 409 Conflict Implementation Plan

## Status: ⏳ PENDING (Template Created for Payroll Approve)

## Overview
All PATCH and approval transition endpoints must check `row_version` and return 409 Conflict if the version doesn't match. This prevents concurrent edit conflicts.

## Pattern Established
✅ **Payroll Approve Endpoint** - Template implementation complete:
- `PayrollRunApproveRequest` schema includes `row_version: int`
- `PayrollApprovalService.approve()` checks `row_version` and raises 409 on mismatch
- Route passes `row_version` to service

## Endpoints Requiring Implementation

### Approval Endpoints (11 endpoints)
1. ✅ `POST /payroll/runs/{id}/approve` - **COMPLETE (Template)**
2. ⏳ `POST /payroll/runs/{id}/submit-approval` - Add `row_version` to request
3. ⏳ `POST /payroll/runs/{id}/reject` - Add `row_version` to request
4. ⏳ `POST /ap/bills/{id}/submit-approval` - Add `row_version` to request
5. ⏳ `POST /ap/bills/{id}/approve` - Add `row_version` to request
6. ⏳ `POST /ap/bills/{id}/reject` - Add `row_version` to request
7. ⏳ `POST /reconciliations/{id}/adjustments/submit-approval` - Add `row_version` to request
8. ⏳ `POST /reconciliations/{id}/adjustments/approve` - Add `row_version` to request
9. ⏳ `POST /reconciliations/{id}/adjustments/reject` - Add `row_version` to request
10. ⏳ `POST /periods/{id}/submit-close` - Add `row_version` to request
11. ⏳ `POST /periods/{id}/approve-close` - Add `row_version` to request
12. ⏳ `POST /intercompany/royalties/runs/{id}/submit-approval` - Add `row_version` to request
13. ⏳ `POST /intercompany/royalties/runs/{id}/approve` - Add `row_version` to request
14. ⏳ `POST /intercompany/royalties/runs/{id}/reject` - Add `row_version` to request

### PATCH Endpoints (2 endpoints)
1. ⏳ `PATCH /bank-accounts/{id}` - Add `row_version` check
2. ⏳ `PATCH /accounts/{id}` - Add `row_version` check

## Implementation Steps (Per Endpoint)

1. **Update Request Schema:**
   ```python
   class XxxRequest(BaseModel):
       # ... existing fields ...
       row_version: int  # Required for optimistic locking
   ```

2. **Update Service Method:**
   ```python
   async def xxx(self, ..., row_version: Optional[int] = None) -> Xxx:
       obj = await self.repo.get_by_id(obj_id)
       
       # Check row_version for optimistic locking
       if row_version is not None and obj.row_version != row_version:
           raise HTTPException(
               status_code=status.HTTP_409_CONFLICT,
               detail=f"Row version mismatch. Expected {obj.row_version}, got {row_version}."
           )
       
       # ... rest of method ...
   ```

3. **Update Route:**
   ```python
   approved = await service.xxx(
       ...,
       row_version=request.row_version
   )
   ```

## Files to Update

### Schemas
- `app/modules/payroll/schemas/payroll_run_schemas.py` - ✅ Approve done, ⏳ Submit/Reject pending
- `app/modules/ap/schemas/ap_bill_schemas.py` - ⏳ All approval requests
- `app/modules/general_ledger/schemas/reconciliation_schemas.py` - ⏳ All adjustment requests
- `app/modules/general_ledger/schemas/period_schemas.py` - ⏳ Close requests
- `app/modules/intercompany/schemas/royalty_schemas.py` - ⏳ All approval requests
- `app/modules/treasury/schemas/bank_account_schemas.py` - ⏳ Update request
- `app/modules/general_ledger/schemas/coa_schemas.py` - ⏳ Update request

### Services
- `app/modules/payroll/services/payroll_approval_service.py` - ✅ Approve done, ⏳ Submit/Reject pending
- `app/modules/ap/services/ap_bill_approval_service.py` - ⏳ All methods
- `app/modules/general_ledger/services/reconciliation_approval_service.py` - ⏳ All methods
- `app/modules/general_ledger/services/period_close_approval_service.py` - ⏳ All methods
- `app/modules/intercompany/services/royalty_approval_service.py` - ⏳ All methods
- `app/modules/treasury/services/bank_account_service.py` - ⏳ Update method
- `app/modules/general_ledger/services/coa_service.py` - ⏳ Update method

### Routes
- All corresponding route files need to pass `row_version` to services

## Testing Requirements

Each endpoint must have a test that:
1. Creates an object and gets its `row_version`
2. Updates the object in another transaction (simulating concurrent edit)
3. Attempts to approve/update with stale `row_version`
4. Verifies 409 Conflict response

## Priority

- **P1 (High):** Approval endpoints (prevents concurrent approval conflicts)
- **P2 (Medium):** PATCH endpoints (prevents concurrent edit conflicts)

## Notes

- Frontend must send `row_version` in all approval/PATCH requests
- Frontend must handle 409 responses by refreshing data and showing conflict message
- Consider using `If-Match` header (ETag) as alternative to `row_version` in request body (more RESTful)
