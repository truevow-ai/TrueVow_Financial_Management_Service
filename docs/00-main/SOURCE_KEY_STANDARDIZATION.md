# Source Key Standardization

**Date:** January 25, 2026  
**Status:** ✅ Complete - All 17 Endpoints Standardized

---

## Source Key Format Standards

All source keys follow the pattern: `{PREFIX}:{ACTION}:{IDENTIFIER}`

### Format Rules:
1. **PREFIX**: Uppercase, descriptive (e.g., `JE`, `PAYROLL`, `AP_BILL`)
2. **ACTION**: Uppercase action verb (e.g., `POST`, `REVERSE`, `IMPORT`)
3. **IDENTIFIER**: UUID or business key (e.g., `{entry_id}`, `{run_id}`)
4. **Separator**: Single colon `:`
5. **No spaces**: All underscores for multi-word prefixes

---

## Complete Source Key List (17 Endpoints)

### Journal Entry Endpoints

| Endpoint | Source Key Format | Example |
|----------|------------------|---------|
| JE Post | `JE:POST:{entry_id}` | `JE:POST:550e8400-e29b-41d4-a716-446655440000` |
| JE Reverse | `JE:REVERSE:{entry_id}` | `JE:REVERSE:550e8400-e29b-41d4-a716-446655440000` |

### Accounts Payable

| Endpoint | Source Key Format | Example |
|----------|------------------|---------|
| AP Bill Post | `AP_BILL:POST:{bill_id}` | `AP_BILL:POST:550e8400-e29b-41d4-a716-446655440000` |

### Payroll

| Endpoint | Source Key Format | Example |
|----------|------------------|---------|
| Payroll Post | `PAYROLL:POST:{run_id}` | `PAYROLL:POST:550e8400-e29b-41d4-a716-446655440000` |
| Payroll Reverse | `PAYROLL:REVERSE:{run_id}` | `PAYROLL:REVERSE:550e8400-e29b-41d4-a716-446655440000` |

### Intercompany

| Endpoint | Source Key Format | Example |
|----------|------------------|---------|
| Royalty Post | `ROYALTY:POST:{calculation_id}` | `ROYALTY:POST:550e8400-e29b-41d4-a716-446655440000` |
| IC Transfer Post (FROM) | `IC_TRANSFER:POST:{transfer_id}:FROM` | `IC_TRANSFER:POST:550e8400-e29b-41d4-a716-446655440000:FROM` |
| IC Transfer Post (TO) | `IC_TRANSFER:POST:{transfer_id}:TO` | `IC_TRANSFER:POST:550e8400-e29b-41d4-a716-446655440000:TO` |

### Accounts Receivable

| Endpoint | Source Key Format | Example |
|----------|------------------|---------|
| AR Invoice Post | `AR_INVOICE:POST:{external_invoice_id}` or `AR_INVOICE:POST:INTERNAL:{invoice_id}` | `AR_INVOICE:POST:inv_123456` or `AR_INVOICE:POST:INTERNAL:550e8400-e29b-41d4-a716-446655440000` |

### Period Management

| Endpoint | Source Key Format | Example |
|----------|------------------|---------|
| Period Lock | `PERIOD:LOCK:{period_id}` | `PERIOD:LOCK:550e8400-e29b-41d4-a716-446655440000` |

### Treasury

| Endpoint | Source Key Format | Example |
|----------|------------------|---------|
| Treasury Post TX | `TREASURY:POST_TX:{entity_id}:{batch_id}:{external_id or tx_id}` | `TREASURY:POST_TX:550e8400-e29b-41d4-a716-446655440000:batch_123:tx_ext_456` |
| Treasury Sync | `TREASURY:SYNC:{entity_id}:{sync_batch_id}` | `TREASURY:SYNC:550e8400-e29b-41d4-a716-446655440000:550e8400-e29b-41d4-a716-446655440001` |
| Bank TX Import | `BANK_TX:IMPORT:{book_id}:{bank_account_id}:{file_hash}` | `BANK_TX:IMPORT:550e8400-e29b-41d4-a716-446655440000:acc_123:hash_abc` |

### Settlement

| Endpoint | Source Key Format | Example |
|----------|------------------|---------|
| Settlement Create | `SETTLEMENT:CREATE:{provider}:{external_settlement_id}` | `SETTLEMENT:CREATE:STRIPE:po_1234567890` or `SETTLEMENT:CREATE:TELR:telr_1234567890` |
| Settlement Stripe Import | `SETTLEMENT:STRIPE:IMPORT:{stripe_payout_id}` | `SETTLEMENT:STRIPE:IMPORT:po_1234567890` |
| Settlement Telr Import | `SETTLEMENT:TELR:IMPORT:{telr_payout_id}` | `SETTLEMENT:TELR:IMPORT:telr_1234567890` |

### Reconciliation

| Endpoint | Source Key Format | Example |
|----------|------------------|---------|
| Reconciliation Close | `RECONCILIATION:CLOSE:{session_id}` | `RECONCILIATION:CLOSE:550e8400-e29b-41d4-a716-446655440000` |
| Reconciliation Adj Post | `RECON_ADJ:POST:{batch_id}` | `RECON_ADJ:POST:550e8400-e29b-41d4-a716-446655440000` |

### Billing Sync

| Endpoint | Source Key Format | Example |
|----------|------------------|---------|
| Billing Sync | `BILLING:SYNC:{entity_id}:{sync_batch_id}` | `BILLING:SYNC:550e8400-e29b-41d4-a716-446655440000:550e8400-e29b-41d4-a716-446655440001` |

---

## Collision Analysis

### ✅ No Collisions Detected

**Prefix Uniqueness:**
- `JE` - Journal Entry (unique)
- `AP_BILL` - Accounts Payable (unique)
- `PAYROLL` - Payroll (unique)
- `ROYALTY` - Royalty (unique)
- `IC_TRANSFER` - Intercompany Transfer (unique, uses `:FROM` and `:TO` suffixes)
- `AR_INVOICE` - Accounts Receivable (unique)
- `PERIOD` - Period Management (unique)
- `TREASURY` - Treasury (unique, uses action suffixes)
- `BANK_TX` - Bank Transaction (unique)
- `SETTLEMENT` - Settlement (unique, uses provider suffixes)
- `RECONCILIATION` / `RECON_ADJ` - Reconciliation (unique)
- `BILLING` - Billing (unique)

**Action Uniqueness:**
- `POST` - Standard posting action
- `REVERSE` - Reversal action
- `LOCK` - Period locking
- `CLOSE` - Reconciliation closing
- `IMPORT` - Import operations
- `SYNC` - Sync operations
- `CREATE` - Settlement creation
- `POST_TX` - Treasury transaction posting

**Identifier Uniqueness:**
- UUIDs ensure uniqueness within entity/book scope
- Business keys (external_id, cursor) ensure uniqueness within context
- Suffixes (`:FROM`, `:TO`) ensure uniqueness for multi-entry operations

---

## Long-Term Maintainability

### ✅ Standards for Future Endpoints

1. **New Posting Endpoint:**
   - Format: `{MODULE}:POST:{entity_id}`
   - Example: `EXPENSE:POST:{expense_id}`

2. **New Import Endpoint:**
   - Format: `{MODULE}:IMPORT:{identifier}`
   - Example: `INVOICE:IMPORT:{file_hash}`

3. **New Sync Endpoint:**
   - Format: `{MODULE}:SYNC:{entity_id}:{cursor}`
   - Example: `CRM:SYNC:{entity_id}:{cursor}`

### ✅ Naming Conventions

- **Module Prefixes:** Use uppercase, underscore for multi-word (e.g., `AP_BILL`, `IC_TRANSFER`)
- **Actions:** Use uppercase verbs (e.g., `POST`, `REVERSE`, `IMPORT`, `SYNC`)
- **Identifiers:** Use UUIDs for entities, business keys for external systems
- **Suffixes:** Use uppercase for directional/contextual suffixes (e.g., `:FROM`, `:TO`)

---

## Implementation Locations

| Service | File | Line |
|---------|------|------|
| JournalEntryService | `app/modules/general_ledger/services/journal_entry_service.py` | 214, 294 |
| PayrollRunService | `app/modules/payroll/services/payroll_run_service.py` | 222, 331 |
| APBillPostingService | `app/modules/ap/services/ap_bill_posting_service.py` | 96 |
| ARPostingService | `app/modules/ar/services/ar_posting_service.py` | 130-133 |
| CashBookPostingService | `app/modules/general_ledger/services/cash_book_posting_service.py` | 315 (post_settlement) |
| IntercompanyTransferService | `app/modules/intercompany/services/intercompany_transfer_service.py` | 160, 203 |
| ReconciliationAdjustmentPostingService | `app/modules/general_ledger/services/reconciliation_adjustment_posting_service.py` | 121 |
| TreasurySyncService | `app/modules/general_ledger/api/routes/treasury_sync_routes.py` | 159 |

---

**Status:** ✅ Complete - All source keys standardized and collision-free
