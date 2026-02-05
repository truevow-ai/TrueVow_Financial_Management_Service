# ADDENDUM A — Accounting Controls That Must Exist (MVP)

**Date:** January 25, 2026  
**Status:** Mandatory Implementation

These are not "nice to have". Without them, your FM module won't survive real finance usage.

---

## A1) Segregation of Duties (SoD) Rules (enforced server-side)

### Hard rules:
1. **Payroll:** `submitted_by != approved_by != posted_by` (unless FINANCE_ADMIN override with reason)
2. **Reconciliation adjustments:** `submitted_by != approved_by != posted_by` (unless FINANCE_ADMIN override)
3. **Period close:** `requester != approver` (unless FINANCE_ADMIN override)
4. **Royalty run:** `generator != approver` (unless FINANCE_ADMIN override)

### Override policy:
- Only FINANCE_ADMIN can override SoD.
- Override requires `reason` (non-empty) and is audit-logged.

### Implementation:
See `app/modules/core/services/sod_validator.py`

---

## A2) Posting Guardrails

### 1) Prevent posting if:
- period is CLOSED or LOCKED
- required dimensions missing
- debits != credits (JE/adjustment JEs)

### 2) Prevent duplicate postings via unique constraints:
- `(entity_id, book_id, source_service, source_type, source_id)` unique for journal entries

### 3) Reversal rules:
- reverse creates equal-and-opposite JE in next OPEN period if original is in locked period
- "reverse & copy" UI action creates new draft from reversed entry

### Implementation:
See `app/modules/core/services/posting_guardrails.py`

---

## A3) Close Checklist (minimal, but mandatory)

Before period can move to PENDING_CLOSE_APPROVAL, system must confirm:

- Bank reconciliations for all active bank accounts are CLOSED for the period
- RevRec run completed for period (ACCRUAL)
- Payroll runs posted (if applicable)
- Intercompany royalty run posted (if applicable)
- AR/AP aging generated (read-only is fine, but must be computed)

### Storage:
- `fm.period_close_checklist(period_id, item_code, status, computed_at, computed_by, notes)`

### Items:
- `BANK_REC_DONE`
- `REVREC_DONE`
- `PAYROLL_POSTED`
- `ROYALTY_POSTED`
- `AR_AGING_READY`
- `AP_AGING_READY`

### Implementation:
See `app/modules/general_ledger/models/period_close_checklist_model.py`

---

**END OF ADDENDUM A**
