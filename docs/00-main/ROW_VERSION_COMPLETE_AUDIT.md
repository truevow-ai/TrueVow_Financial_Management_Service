# Row Version 409 - Complete Audit Results

**Date:** January 27, 2026  
**Method:** Automated script + manual verification

---

## RAW GREP OUTPUTS

### 1) ALL row_version schema fields

**Command:** `grep -n "row_version:\s*int" app/modules`

**Output:**
```
app\modules\general_ledger\schemas\reconciliation_schemas.py:53:    row_version: int  # Required for optimistic locking
app\modules\general_ledger\schemas\reconciliation_schemas.py:61:    row_version: int  # Required for optimistic locking
app\modules\general_ledger\schemas\reconciliation_schemas.py:69:    row_version: int  # Required for optimistic locking
app\modules\general_ledger\schemas\reconciliation_schemas.py:76:    row_version: int  # Required for optimistic locking
app\modules\payroll\schemas\payroll_run_schemas.py:22:    row_version: int  # Required for optimistic locking
app\modules\payroll\schemas\payroll_run_schemas.py:29:    row_version: int  # Required for optimistic locking
app\modules\payroll\schemas\payroll_run_schemas.py:36:    row_version: int  # Required for optimistic locking
app\modules\payroll\schemas\payroll_run_schemas.py:43:    row_version: int  # Required for optimistic locking
app\modules\payroll\schemas\payroll_run_schemas.py:92:    row_version: int
app\modules\general_ledger\schemas\period_schemas.py:25:    row_version: int  # Required for optimistic locking
app\modules\general_ledger\schemas\period_schemas.py:26:    row_version: int  # Required for optimistic locking
app\modules\general_ledger\schemas\period_schemas.py:33:    row_version: int  # Required for optimistic locking
app\modules\general_ledger\schemas\period_schemas.py:34:    row_version: int  # Required for optimistic locking
app\modules\general_ledger\schemas\period_schemas.py:56:    row_version: int
app\modules\intercompany\schemas\intercompany_schemas.py:73:    row_version: int  # Required for optimistic locking
app\modules\intercompany\schemas\intercompany_schemas.py:80:    row_version: int  # Required for optimistic locking
app\modules\intercompany\schemas\intercompany_schemas.py:87:    row_version: int  # Required for optimistic locking
app\modules\intercompany\schemas\intercompany_schemas.py:137:    row_version: int
app\modules\ap\schemas\ap_bill_schemas.py:37:    row_version: int  # Required for optimistic locking
app\modules\ap\schemas\ap_bill_schemas.py:44:    row_version: int  # Required for optimistic locking
app\modules\ap\schemas\ap_bill_schemas.py:50:    row_version: int  # Required for optimistic locking
app\modules\ap\schemas\ap_bill_schemas.py:57:    row_version: int  # Required for optimistic locking
app\modules\ap\schemas\ap_bill_schemas.py:106:    row_version: int
app\modules\general_ledger\schemas\journal_entry_schemas.py:134:    row_version: int | None = None
```

**Total:** 24 schema fields with `row_version: int`

---

### 2) ALL service methods accepting row_version

**Command:** `grep -n "row_version\s*:" app/modules/*/services`

**Output:**
```
app\modules\ap\services\ap_bill_approval_service.py:40:        row_version: Optional[int] = None
app\modules\ap\services\ap_bill_approval_service.py:107:        row_version: Optional[int] = None
app\modules\ap\services\ap_bill_approval_service.py:166:        row_version: Optional[int] = None
app\modules\ap\services\ap_bill_posting_service.py:31:        row_version: Optional[int] = None
app\modules\general_ledger\services\period_close_approval_service.py:45:        row_version: Optional[int] = None
app\modules\general_ledger\services\period_close_approval_service.py:122:        row_version: Optional[int] = None
app\modules\general_ledger\services\reconciliation_adjustment_posting_service.py:32:        row_version: Optional[int] = None
app\modules\general_ledger\services\reconciliation_approval_service.py:44:        row_version: Optional[int] = None
app\modules\general_ledger\services\reconciliation_approval_service.py:112:        row_version: Optional[int] = None
app\modules\general_ledger\services\reconciliation_approval_service.py:179:        row_version: Optional[int] = None
app\modules\intercompany\services\royalty_approval_service.py:39:        row_version: Optional[int] = None
app\modules\intercompany\services\royalty_approval_service.py:111:        row_version: Optional[int] = None
app\modules\intercompany\services\royalty_approval_service.py:175:        row_version: Optional[int] = None
app\modules\payroll\services\payroll_approval_service.py:40:        row_version: Optional[int] = None
app\modules\payroll\services\payroll_approval_service.py:109:        row_version: Optional[int] = None
app\modules\payroll\services\payroll_approval_service.py:177:        row_version: Optional[int] = None
app\modules\payroll\services\payroll_run_service.py:176:        row_version: Optional[int] = None
```

**Total:** 17 service methods accept `row_version` parameter

---

### 3) ALL 409 validation logic

**Command:** `grep -n "check_row_version\(|row_version.*!=|HTTPException\(409|status_code\s*=\s*409" app/modules`

**Output:**
```
app\modules\ap\services\ap_bill_approval_service.py:52:        if row_version is not None and bill.row_version != row_version:
app\modules\ap\services\ap_bill_approval_service.py:55:                status_code=status.HTTP_409_CONFLICT,
app\modules\ap\services\ap_bill_approval_service.py:120:        check_row_version(bill.row_version, row_version, "AP bill")
app\modules\ap\services\ap_bill_approval_service.py:181:        if row_version is not None and bill.row_version != row_version:
app\modules\ap\services\ap_bill_approval_service.py:184:                status_code=status.HTTP_409_CONFLICT,
app\modules\ap\api\routes\ap_bill_routes.py:215:    if request.row_version != bill.row_version:
app\modules\ap\api\routes\ap_bill_routes.py:217:            status_code=status.HTTP_409_CONFLICT,
app\modules\ap\services\ap_bill_posting_service.py:39:        if row_version is not None and bill.row_version != row_version:
app\modules\ap\services\ap_bill_posting_service.py:42:                status_code=status.HTTP_409_CONFLICT,
app\modules\intercompany\services\royalty_approval_service.py:51:        if row_version is not None and run.row_version != row_version:
app\modules\intercompany\services\royalty_approval_service.py:54:                status_code=status.HTTP_409_CONFLICT,
app\modules\intercompany\services\royalty_approval_service.py:124:        check_row_version(run.row_version, row_version, "royalty run")
app\modules\intercompany\services\royalty_approval_service.py:190:        if row_version is not None and run.row_version != row_version:
app\modules\intercompany\services\royalty_approval_service.py:193:                status_code=status.HTTP_409_CONFLICT,
app\modules\payroll\services\payroll_run_service.py:184:        if row_version is not None and run.row_version != row_version:
app\modules\payroll\services\payroll_run_service.py:187:                status_code=status.HTTP_409_CONFLICT,
app\modules\general_ledger\services\reconciliation_adjustment_posting_service.py:40:        check_row_version(batch.row_version, row_version, "reconciliation adjustment batch")
app\modules\general_ledger\services\period_close_approval_service.py:53:        if row_version is not None and period.row_version != row_version:
app\modules\general_ledger\services\period_close_approval_service.py:56:                status_code=status.HTTP_409_CONFLICT,
app\modules\general_ledger\services\period_close_approval_service.py:130:        if row_version is not None and period.row_version != row_version:
app\modules\general_ledger\services\period_close_approval_service.py:133:                status_code=status.HTTP_409_CONFLICT,
app\modules\general_ledger\services\reconciliation_approval_service.py:56:        if row_version is not None and batch.row_version != row_version:
app\modules\general_ledger\services\reconciliation_approval_service.py:59:                status_code=status.HTTP_409_CONFLICT,
app\modules\general_ledger\services\reconciliation_approval_service.py:124:        if row_version is not None and batch.row_version != row_version:
app\modules\general_ledger\services\reconciliation_approval_service.py:127:                status_code=status.HTTP_409_CONFLICT,
app\modules\general_ledger\services\reconciliation_approval_service.py:194:        if row_version is not None and batch.row_version != row_version:
app\modules\general_ledger\services\reconciliation_approval_service.py:197:                status_code=status.HTTP_409_CONFLICT,
app\modules\payroll\services\payroll_approval_service.py:52:        if row_version is not None and run.row_version != row_version:
app\modules\payroll\services\payroll_approval_service.py:55:                status_code=status.HTTP_409_CONFLICT,
app\modules\payroll\services\payroll_approval_service.py:121:        if row_version is not None and run.row_version != row_version:
app\modules\payroll\services\payroll_approval_service.py:124:                status_code=status.HTTP_409_CONFLICT,
app\modules\payroll\services\payroll_approval_service.py:192:        if row_version is not None and run.row_version != row_version:
app\modules\payroll\services\payroll_approval_service.py:195:                status_code=status.HTTP_409_CONFLICT,
```

**Summary:**
- **check_row_version() calls:** 3
- **Inline checks (row_version !=):** 12
- **HTTPException(409) raises:** 15 total
- **Route-level checks:** 1 (AP bill post)

---

## ENDPOINT-BY-ENDPOINT VERIFICATION

### Payroll (4 endpoints):

1. **submit-approval**
   - Schema: `payroll_run_schemas.py:22` ✅
   - Route: `payroll_run_routes.py:83` ✅ (passes row_version)
   - Service: `payroll_approval_service.py:52` ✅ (inline check, raises 409)

2. **approve**
   - Schema: `payroll_run_schemas.py:29` ✅
   - Route: `payroll_run_routes.py:108` ✅ (passes row_version)
   - Service: `payroll_approval_service.py:121` ✅ (inline check, raises 409)

3. **reject**
   - Schema: `payroll_run_schemas.py:36` ✅ (FIXED)
   - Route: `payroll_run_routes.py:132` ✅ (passes row_version)
   - Service: `payroll_approval_service.py:192` ✅ (inline check, raises 409)

4. **post**
   - Schema: `payroll_run_schemas.py:43` ✅
   - Route: `payroll_run_routes.py:174` ✅ (passes row_version)
   - Service: `payroll_run_service.py:184` ✅ (inline check, raises 409)

### AP Bills (4 endpoints):

1. **submit-approval**
   - Schema: `ap_bill_schemas.py:37` ✅
   - Route: `ap_bill_routes.py:138` ✅ (passes row_version)
   - Service: `ap_bill_approval_service.py:52` ✅ (inline check, raises 409)

2. **approve**
   - Schema: `ap_bill_schemas.py:44` ✅
   - Route: `ap_bill_routes.py:163` ✅ (FIXED - now passes row_version)
   - Service: `ap_bill_approval_service.py:120` ✅ (check_row_version(), raises 409)

3. **reject**
   - Schema: `ap_bill_schemas.py:50` ✅
   - Route: `ap_bill_routes.py:186` ✅ (passes row_version)
   - Service: `ap_bill_approval_service.py:181` ✅ (inline check, raises 409)

4. **post**
   - Schema: `ap_bill_schemas.py:57` ✅
   - Route: `ap_bill_routes.py:214` ✅ (route-level check at line 215, raises 409)
   - Service: `ap_bill_posting_service.py:39` ✅ (inline check, raises 409)

### Reconciliation (4 endpoints):

1. **submit-approval**
   - Schema: `reconciliation_schemas.py:53` ✅
   - Route: `reconciliation_routes.py:220` ✅ (passes row_version)
   - Service: `reconciliation_approval_service.py:56` ✅ (inline check, raises 409)

2. **approve**
   - Schema: `reconciliation_schemas.py:61` ✅ (FIXED)
   - Route: `reconciliation_routes.py:247` ✅ (passes row_version)
   - Service: `reconciliation_approval_service.py:124` ✅ (inline check, raises 409)

3. **reject**
   - Schema: `reconciliation_schemas.py:69` ✅
   - Route: `reconciliation_routes.py:272` ✅ (passes row_version)
   - Service: `reconciliation_approval_service.py:194` ✅ (inline check, raises 409)

4. **post**
   - Schema: `reconciliation_schemas.py:76` ✅
   - Route: `reconciliation_routes.py:315` ✅ (passes row_version)
   - Service: `reconciliation_adjustment_posting_service.py:40` ✅ (check_row_version(), raises 409)

### Period (2 endpoints):

1. **submit-close**
   - Schema: `period_schemas.py:25` ✅
   - Route: `period_routes.py:120` ✅ (passes row_version)
   - Service: `period_close_approval_service.py:53` ✅ (inline check, raises 409)

2. **approve-close**
   - Schema: `period_schemas.py:33` ✅
   - Route: `period_routes.py:145` ✅ (passes row_version)
   - Service: `period_close_approval_service.py:130` ✅ (inline check, raises 409)

### Royalties (3 endpoints):

1. **submit-approval**
   - Schema: `intercompany_schemas.py:73` ✅
   - Route: `royalty_routes.py:142` ✅ (passes row_version)
   - Service: `royalty_approval_service.py:51` ✅ (inline check, raises 409)

2. **approve**
   - Schema: `intercompany_schemas.py:80` ✅
   - Route: `royalty_routes.py:167` ✅ (passes row_version)
   - Service: `royalty_approval_service.py:124` ✅ (FIXED - check_row_version(), raises 409)

3. **reject**
   - Schema: `intercompany_schemas.py:87` ✅
   - Route: `royalty_routes.py:191` ✅ (passes row_version)
   - Service: `royalty_approval_service.py:190` ✅ (inline check, raises 409)

---

## SUMMARY

**Total Approval/Transition Endpoints:** 17  
**Complete:** 17 ✅  
**Missing:** 0 ✅

**Validation Methods:**
- `check_row_version()`: 3 endpoints
- Inline checks: 14 endpoints
- Route-level checks: 1 endpoint (AP bill post - has both route and service checks)

**All 17 endpoints have:**
- ✅ Schema includes `row_version: int`
- ✅ Route passes `row_version=request.row_version`
- ✅ Service validates row_version (either check_row_version() or inline)
- ✅ Raises HTTPException(409) on mismatch

---

**Status:** ✅ ALL 17 ENDPOINTS COMPLETE
