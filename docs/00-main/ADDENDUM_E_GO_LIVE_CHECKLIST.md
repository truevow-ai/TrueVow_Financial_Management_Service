# ADDENDUM E — MVP "Go-Live" Checklist (So Finance Doesn't Reject It)

**Date:** January 25, 2026  
**Status:** Pre-Production Checklist

This is the checklist before you let real finance users touch it.

---

## E1) Data Setup

- [ ] Entities created (UAE/Nevis/Pak)
- [ ] Books created (Accrual/Cash per entity)
- [ ] CoA seeded per entity
- [ ] Mapping keys fully mapped:
  - [ ] AR accounts (receivables, revenue, deferred revenue)
  - [ ] AP accounts (payables, expenses)
  - [ ] Deferred revenue accounts
  - [ ] Payroll accounts (expenses, liabilities)
  - [ ] FX accounts (gains/losses)
  - [ ] Fee accounts
  - [ ] Royalty accounts
- [ ] Dimensions seeded and required dimensions enforced:
  - [ ] COST_CENTER (required)
  - [ ] DEPARTMENT (required)
  - [ ] LOCATION (required)
  - [ ] CHANNEL (optional)
  - [ ] PRODUCT (optional)
- [ ] Approval policies set (default approvals ON)

---

## E2) Workflows Verified End-to-End

### Billing Sync → AR + Deferred Revenue
- [ ] Billing sync imports invoices + lines
- [ ] Posts AR in ACCRUAL book
- [ ] Posts Deferred Revenue in ACCRUAL book
- [ ] Revenue recognition runner posts monthly recognition

### Treasury Import → Cash Book
- [ ] Treasury import ingests bank statement
- [ ] Posts CASH book entries
- [ ] Matches transactions correctly

### Reconciliation → Adjustments
- [ ] Reconciliation session created
- [ ] Auto-matching suggests candidates
- [ ] Manual matches work
- [ ] Adjustment batch created
- [ ] Adjustment batch submitted for approval
- [ ] Adjustment batch approved
- [ ] Adjustment batch posted
- [ ] Reconciliation closes with diff=0

### Payroll Run
- [ ] Payroll run created
- [ ] Payroll calculated
- [ ] Adjustments added via grid
- [ ] Run submitted for approval
- [ ] Run approved
- [ ] Run posted (creates JE)
- [ ] Payment batch exported (WPS/CSV)
- [ ] Payment batch marked paid via treasury transaction

### Royalty Run
- [ ] Royalty run generated for period
- [ ] Run submitted for approval
- [ ] Run approved
- [ ] Run posted (creates intercompany JEs)
- [ ] Settlement via transfer

---

## E3) Reporting Verified

- [ ] Trial balance balances (debits == credits)
- [ ] P&L generates for each entity/book
- [ ] Balance Sheet generates for each entity/book
- [ ] Cash position equals reconciled bank balances
- [ ] AR aging generated
- [ ] AP aging generated
- [ ] GL Detail report works with filters

---

## E4) Control & Safety Verified

### Immutability
- [ ] Posted objects cannot be edited
- [ ] Posted objects can only be reversed
- [ ] Reversal creates new JE in next OPEN period

### SoD Rules
- [ ] Payroll: submitter != approver != poster (unless FINANCE_ADMIN override)
- [ ] Reconciliation: submitter != approver != poster (unless FINANCE_ADMIN override)
- [ ] Period close: requester != approver (unless FINANCE_ADMIN override)
- [ ] Royalty: generator != approver (unless FINANCE_ADMIN override)

### Posting Guardrails
- [ ] Cannot post into CLOSED/LOCKED periods
- [ ] Cannot post unbalanced JEs
- [ ] Cannot post without required dimensions
- [ ] Duplicate postings prevented (idempotency)

### Audit Logging
- [ ] Every approval action logged
- [ ] Every posting logged
- [ ] Every reversal logged
- [ ] Audit log includes before/after JSON

### Period Close Checklist
- [ ] Bank reconciliations checked
- [ ] RevRec run checked
- [ ] Payroll runs checked
- [ ] Royalty runs checked
- [ ] AR/AP aging checked
- [ ] All items must be COMPLETE before approval

---

## E5) UI/UX Verified

### Grid Functionality
- [ ] Excel copy/paste works (multi-row, multi-column)
- [ ] Keyboard navigation works (arrows, Tab, Enter, Esc)
- [ ] Fill-down (Ctrl+D) works
- [ ] Bulk apply dimensions works
- [ ] Inline validation shows errors
- [ ] Running totals update correctly

### Approval Workflows
- [ ] Status banners show correctly
- [ ] Submit button appears for preparers
- [ ] Approve/Reject buttons appear for approvers
- [ ] Post button appears after approval
- [ ] Read-only mode enforced for PENDING_APPROVAL (preparer view)

### Error Handling
- [ ] Validation errors shown clearly
- [ ] SoD violations shown clearly
- [ ] Period lock errors shown clearly
- [ ] Network errors handled gracefully

---

## E6) Performance Verified

- [ ] Grid handles 1000+ rows smoothly
- [ ] Reports generate in < 5 seconds
- [ ] Bulk upsert handles 2000 rows
- [ ] Reconciliation matching completes in < 10 seconds for 1000 transactions

---

## E7) Security Verified

- [ ] RBAC enforced on all endpoints
- [ ] JWT tokens validated
- [ ] User roles checked before actions
- [ ] Approval policies respected
- [ ] Audit logs capture user actions

---

**END OF ADDENDUM E**
