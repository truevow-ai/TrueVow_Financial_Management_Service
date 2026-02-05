# Idempotency Implementation Checkpoint

**Date:** January 25, 2026  
**Status:** 🚧 IN PROGRESS - 5/17 endpoints complete (29%)

---

## ✅ Completed (5 endpoints)

1. ✅ `POST /books/{book_id}/journal-entries/{entry_id}/post`
   - Idempotency applied
   - Source key: `JE:POST:{entry_id}`

2. ✅ `POST /books/{book_id}/journal-entries/{entry_id}/reverse`
   - Idempotency applied
   - Source key: `JE:REVERSE:{entry_id}`

3. ✅ `POST /books/{book_id}/payroll/runs/{run_id}/post`
   - Idempotency applied
   - Source key: `PAYROLL:POST:{run_id}`

4. ✅ `POST /books/{book_id}/payroll/runs/{run_id}/reverse`
   - Idempotency applied
   - Source key: `PAYROLL:REVERSE:{run_id}`

5. ✅ `POST /books/{book_id}/ap/bills/{bill_id}/post`
   - Idempotency applied
   - Source key: `AP_BILL:POST:{bill_id}`
   - **Created:** `APBillPostingService` (was missing)

---

## ⏳ Remaining (12 endpoints)

### Category 1 (6 remaining)
6. ⏳ `POST /books/{book_id}/intercompany/royalties/calculations/{calculation_id}/post`
7. ⏳ `POST /books/{book_id}/intercompany/transfers/{transfer_id}/post`
8. ⏳ `POST /books/{book_id}/ar/invoices/{invoice_id}/post`
9. ⏳ `POST /books/{book_id}/periods/{period_id}/lock`
10. ⏳ `POST /books/{book_id}/treasury/sync/post-transactions`
11. ⏳ `POST /books/{book_id}/reconciliations/{session_id}/close`

### Category 2 (4 remaining)
12. ⏳ `POST /books/{book_id}/treasury/bank-transactions/import`
13. ⏳ `POST /books/{book_id}/treasury/settlements`
14. ⏳ `POST /books/{book_id}/treasury/settlements/stripe/import`
15. ⏳ `POST /books/{book_id}/treasury/settlements/telr/import`

### Category 3 (2 remaining)
16. ⏳ `POST /books/{book_id}/integrations/billing/sync`
17. ⏳ `POST /books/{book_id}/integrations/treasury/sync`

---

## Infrastructure Status

### ✅ Complete
- IdempotencyKey model with scope fields
- JournalEntry model with source_key and legal_entity_id
- Core idempotency helpers (`app/core/idempotency.py`)
- JournalEntryService updated to set source_key
- PayrollRunService updated to set source_key
- APBillPostingService created

### ⏳ Pending
- Update remaining posting services to set source_key
- Fix reconciliation close (separate adjustment posting)
- Add treasury_sync_batch table
- Database migrations for schema changes

---

## Next Steps

1. Continue applying idempotency to remaining 12 endpoints
2. Update posting services (Royalty, IC Transfer, AR) to set source_key
3. Fix reconciliation close behavior
4. Add treasury_sync_batch table
5. Create database migrations
6. Write tests

---

**Pattern Established:** All endpoints follow the same pattern:
1. Add `idempotency_key: str = Depends(require_idempotency_key)`
2. Get `legal_entity_id` from book/entity
3. Wrap handler in `apply_idempotency()`
4. Update service to set `source_key` when creating journal entries
