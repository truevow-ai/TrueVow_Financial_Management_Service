# Idempotency Endpoint List for Review

**Date:** January 25, 2026  
**Status:** 📋 **AWAITING USER REVIEW**

---

## Endpoints Requiring Idempotency Enforcement

### Category 1: Critical Posting/Money Movement (MVP - Must Have)

These endpoints create or modify financial postings and MUST be idempotent:

1. **`POST /books/{book_id}/journal-entries/{entry_id}/post`**
   - **Route:** `app/modules/general_ledger/api/routes/journal_entry_routes.py::post_journal_entry`
   - **Creates:** Posted journal entry (immutable)
   - **Source Key Format:** `JE:{entry_id}`

2. **`POST /books/{book_id}/journal-entries/{entry_id}/reverse`**
   - **Route:** `app/modules/general_ledger/api/routes/journal_entry_routes.py::reverse_journal_entry`
   - **Creates:** Reversal journal entry
   - **Source Key Format:** `JE_REVERSE:{entry_id}`

3. **`POST /books/{book_id}/ap/bills/{bill_id}/post`**
   - **Route:** `app/modules/ap/api/routes/ap_bill_routes.py::post_bill`
   - **Creates:** Posted AP bill + journal entries
   - **Source Key Format:** `AP_BILL:{bill_id}`

4. **`POST /books/{book_id}/payroll/runs/{run_id}/post`**
   - **Route:** `app/modules/payroll/api/routes/payroll_run_routes.py::post_payroll_run`
   - **Creates:** Posted payroll run + journal entries
   - **Source Key Format:** `PAYROLL:{run_id}`

5. **`POST /books/{book_id}/payroll/runs/{run_id}/reverse`**
   - **Route:** `app/modules/payroll/api/routes/payroll_run_routes.py::reverse_payroll_run`
   - **Creates:** Reversal journal entries for payroll
   - **Source Key Format:** `PAYROLL_REVERSE:{run_id}`

6. **`POST /books/{book_id}/intercompany/royalties/calculations/{calculation_id}/post`**
   - **Route:** `app/modules/intercompany/api/routes/royalty_routes.py::post_royalty_calculation`
   - **Creates:** Posted royalty calculation + journal entries
   - **Source Key Format:** `ROYALTY:{calculation_id}`

7. **`POST /books/{book_id}/intercompany/transfers/{transfer_id}/post`**
   - **Route:** `app/modules/intercompany/api/routes/intercompany_transfer_routes.py::post_intercompany_transfer`
   - **Creates:** Posted intercompany transfer + journal entries
   - **Source Key Format:** `IC_TRANSFER:{transfer_id}`

8. **`POST /books/{book_id}/ar/invoices/{invoice_id}/post`**
   - **Route:** `app/modules/ar/api/routes/ar_routes.py::post_invoice`
   - **Creates:** Posted AR invoice + journal entries
   - **Source Key Format:** `AR_INVOICE:{invoice_id}`

9. **`POST /books/{book_id}/periods/{period_id}/lock`**
   - **Route:** `app/modules/general_ledger/api/routes/period_routes.py::lock_period`
   - **Modifies:** Period status (prevents future postings)
   - **Source Key Format:** `PERIOD_LOCK:{period_id}`

10. **`POST /books/{book_id}/treasury/sync/post-transactions`**
    - **Route:** `app/modules/general_ledger/api/routes/treasury_sync_routes.py::sync_and_post_transactions`
    - **Creates:** Multiple journal entries from treasury transactions
    - **Source Key Format:** `TREASURY_SYNC_POST:{entity_id}:{sync_batch_id}` (needs batch_id)

11. **`POST /books/{book_id}/reconciliations/{session_id}/close`**
    - **Route:** `app/modules/general_ledger/api/routes/reconciliation_routes.py::close_reconciliation`
    - **Creates:** Reconciliation adjustments (journal entries)
    - **Source Key Format:** `RECONCILE_CLOSE:{session_id}`

---

### Category 2: Treasury Import Endpoints (MVP - Per File/Batch)

These endpoints import external data and create transactions. Must be idempotent per file/batch:

12. **`POST /books/{book_id}/treasury/bank-transactions/import`**
    - **Route:** `app/modules/treasury/api/routes/bank_transaction_routes.py::import_csv_transactions`
    - **Creates:** Bank transactions from CSV
    - **Source Key Format:** `BANK_TX_IMPORT:{file_hash}` or `{external_batch_id}`

13. **`POST /books/{book_id}/treasury/settlements`**
    - **Route:** `app/modules/treasury/api/routes/settlement_routes.py::create_settlement`
    - **Creates:** Settlement record
    - **Source Key Format:** `SETTLEMENT:{external_id}` (if available)

14. **`POST /books/{book_id}/treasury/settlements/stripe/import`**
    - **Route:** `app/modules/treasury/api/routes/settlement_routes.py::import_stripe_settlement`
    - **Creates:** Settlement from Stripe import
    - **Source Key Format:** `SETTLEMENT_STRIPE:{stripe_payout_id}`

15. **`POST /books/{book_id}/treasury/settlements/telr/import`**
    - **Route:** `app/modules/treasury/api/routes/settlement_routes.py::import_telr_settlement`
    - **Creates:** Settlement from Telr import
    - **Source Key Format:** `SETTLEMENT_TELR:{telr_payout_id}`

---

### Category 3: Sync Endpoints (MVP - Per Sync Batch)

These endpoints sync external data. Should be idempotent per sync batch:

16. **`POST /books/{book_id}/integrations/billing/sync`**
    - **Route:** `app/modules/ar/api/routes/billing_sync_routes.py::sync_billing`
    - **Creates:** AR invoices, customers from billing system
    - **Source Key Format:** `BILLING_SYNC:{entity_id}:{since_cursor}` or `{sync_batch_id}`

17. **`POST /books/{book_id}/integrations/treasury/sync`**
    - **Route:** `app/modules/general_ledger/api/routes/treasury_sync_routes.py::sync_treasury`
    - **Creates:** Bank transactions, settlements from treasury
    - **Source Key Format:** `TREASURY_SYNC:{entity_id}:{since_cursor}` or `{sync_batch_id}`

---

### Category 4: Nice-to-Have Later (Approval Transitions)

These are less risky but still benefit from idempotency:

18. **`POST /books/{book_id}/payroll/runs/{run_id}/submit-approval`**
19. **`POST /books/{book_id}/payroll/runs/{run_id}/approve`**
20. **`POST /books/{book_id}/payroll/runs/{run_id}/reject`**
21. **`POST /books/{book_id}/ap/bills/{bill_id}/submit-approval`**
22. **`POST /books/{book_id}/ap/bills/{bill_id}/approve`**
23. **`POST /books/{book_id}/ap/bills/{bill_id}/reject`**
24. **`POST /books/{book_id}/reconciliations/{rec_id}/adjustments/submit-approval`**
25. **`POST /books/{book_id}/reconciliations/{rec_id}/adjustments/approve`**
26. **`POST /books/{book_id}/reconciliations/{rec_id}/adjustments/reject`**
27. **`POST /books/{book_id}/periods/{period_id}/submit-close`**
28. **`POST /books/{book_id}/periods/{period_id}/approve-close`**
29. **`POST /books/{book_id}/intercompany/royalties/runs/{run_id}/submit-approval`**
30. **`POST /books/{book_id}/intercompany/royalties/runs/{run_id}/approve`**
31. **`POST /books/{book_id}/intercompany/royalties/runs/{run_id}/reject`**

---

## Questions for User Review

1. **Which endpoints should require `Idempotency-Key` header in MVP?**
   - All Category 1 (1-11)?
   - All Category 1 + Category 2 (1-15)?
   - All Category 1 + Category 2 + Category 3 (1-17)?

2. **What should be the idempotency scope?**
   - Proposed: `(legal_entity_id, book_id, endpoint_name)`
   - Should we include `actor_user_id` or omit it for safe retries across systems?

3. **Source Key Format Review:**
   - Are the proposed `source_key` formats correct for each endpoint?
   - For sync endpoints, should we use `sync_batch_id` if available, or `entity_id:since_cursor`?

4. **Treasury Sync Post-Transactions:**
   - Does this endpoint have a `sync_batch_id` or similar identifier we can use for `source_key`?

5. **Reconciliation Adjustments:**
   - I don't see a direct `POST /adjustments/post` endpoint. Does closing a reconciliation session create the adjustments, or is there a separate posting step?

---

## Next Steps (After User Review)

1. User marks which endpoints require idempotency in MVP
2. User confirms scope and source_key formats
3. I implement:
   - `IdempotencyKey` model
   - `get_idempotency_key()` dependency
   - `check_and_store_idempotency()` helper
   - Apply to all marked endpoints
   - Add `source_key` unique constraint to journal entries
