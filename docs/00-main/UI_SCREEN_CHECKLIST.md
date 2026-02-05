# FM/Treasury UI Screen Checklist — Grid (Excel/Airtable) + Form Toggle

**Date:** January 25, 2026  
**Status:** Implementation Guide

Goal: Finance users can do 80% of work without exporting to Excel.  
Rule: Every grid edits only DRAFT data; POST is separate and validated.

---

## 0) Global UI Standards (Apply to All Screens)

### 0.1 Toolbar (top of each editor)
- Entity selector (locked after posting)
- Book selector (ACCRUAL/CASH) (locked after posting)
- Period selector (auto from date; show status OPEN/SOFT_CLOSED/CLOSED/LOCKED)
- Status pill (DRAFT / PENDING_APPROVAL / APPROVED / POSTED / REJECTED)
- Buttons (dynamic by status + role):
  - Save (optional if autosave)
  - Validate
  - Submit for approval
  - Approve / Reject (approver roles)
  - Post
  - Reverse & Copy (admin only)
- "Last saved" timestamp + sync indicator
- Audit trail link (opens side panel)

### 0.2 Grid Defaults
- Virtualized rows on
- Sticky header + sticky totals footer
- Column resizing + reorder allowed (save per user)
- Column type enforcement:
  - currency columns use decimal string parsing
  - date columns strict date
  - enum columns use dropdown
- Paste handling:
  - paste multi-row multi-column from Excel into grid
  - map by column order in current view
  - show "paste preview" toast (rows inserted/updated)

### 0.3 Required keyboard shortcuts
- Arrow keys: move cell
- Tab/Shift+Tab: move cell (wrap to next row)
- Enter: commit edit and move down
- Esc: cancel edit
- Ctrl/Cmd+C/V: copy/paste cells and blocks
- Ctrl/Cmd+D: fill down for selected column
- Ctrl/Cmd+Z: undo last change (local buffer)
- Ctrl/Cmd+S: force save now (if autosave)

### 0.4 Side panel (Row detail)
- Opens on row click
- Shows complex fields without cluttering grid:
  - full memo
  - dimensions picker
  - attachments
  - source links (billing invoice, bank tx)
- Side panel saves back into draft via bulkUpsert

### 0.5 Inline validation UX
- Cell-level red border + tooltip message
- Row-level icon if any errors
- Header banner summarizing blockers
- Validate action returns server errors; highlight affected cells

---

## 1) Screen: Journal Entry Editor (JE) — REQUIRED (MVP)

### 1.1 Form Mode (Header)
Fields:
- JE Date (required)
- Period (auto; read-only, show status)
- Memo (required for manual JEs)
- Currency mode: (Functional only) / (Multi-currency enabled)
- Attachments (optional)
- Source (read-only if system-generated)

Controls:
- Auto-balance helper toggle (optional)
- Template dropdown: Load Template / Save as Template

### 1.2 Grid Mode (Lines)
Columns (minimum MVP):
1) Line #
2) Account (searchable dropdown; show code + name)
3) Description (text)
4) Debit (decimal)
5) Credit (decimal)
6) Transaction Currency (optional; default = book/entity functional)
7) FX Rate (optional; editable only if TC != FC and allowed)
8) COST_CENTER (required)
9) DEPARTMENT (required)
10) LOCATION (required)
11) CHANNEL (optional)
12) PRODUCT (optional)
13) Reference (optional; invoice/vendor)
14) Notes (short)

Footer:
- Total Debit
- Total Credit
- Balance (must be 0.00 to post)
- Count of lines
- Count of errors

Row actions:
- Add row
- Duplicate row
- Delete row
- Split amount (optional v2)

Bulk actions:
- Apply Account to selected
- Apply Dimensions to selected
- Fill down current column
- Clear selected cells

Posting rules:
- Validate required before Submit/Post
- Post button disabled if balance != 0 or errors exist

---

## 2) Screen: AP Bill Entry — REQUIRED (MVP)

### 2.1 Form Mode (Header)
Fields:
- Vendor (required; searchable)
- Vendor Invoice #
- Bill Date (required)
- Due Date
- Currency (default entity functional; allow override)
- Memo
- Attachments (invoice PDF)

Controls:
- Template: Load / Save
- "Allocate defaults from vendor" toggle (dimensions)

### 2.2 Grid Mode (Lines)
Columns:
1) Line #
2) Expense/Asset Account (required)
3) Description
4) Qty (decimal; default 1)
5) Unit Price (decimal)
6) Amount (computed; editable if qty/unit locked)
7) Tax Code (optional)
8) COST_CENTER (required)
9) DEPARTMENT (required)
10) LOCATION (required)
11) PROJECT (optional future)
12) Notes

Footer:
- Subtotal
- Tax total (if enabled)
- Total
- Error count

Actions:
- Validate
- Submit/Post (RBAC; approvals not required for normal AP bills in MVP unless you decide later)

---

## 3) Screen: Bank Transactions Grid (Treasury) — REQUIRED (MVP)

Purpose: statement review + classification + preparation for reconciliation.

Columns:
1) Date
2) Description
3) Amount (signed)
4) Currency
5) Bank Account
6) Counterparty (parsed if available)
7) Category (enum: Deposit/Withdrawal/Fee/Transfer/FX/Unknown)
8) Status (Unmatched/Matched/Excluded)
9) Suggested Match (top candidate summary)
10) Actions (Match / Mark Fee / Create Transfer / Create Adjustment Draft)

Filters:
- date range
- amount range
- unmatched only
- category
- keyword search

Bulk actions:
- Mark as fees (choose account + dimensions)
- Mark as transfers (select entity/from/to)
- Exclude selected (with reason; audit log)

---

## 4) Screen: Reconciliation Session — REQUIRED (MVP)

### 4.1 Header
Fields:
- Bank account
- Statement start/end date
- Statement ending balance
- Computed ledger ending balance
- Difference
- Status: DRAFT / PENDING_ADJ_APPROVAL / RECONCILED

### 4.2 Grid: Statement Lines
Columns:
- Date, Description, Amount, Currency
- Match Status
- Matched Object (payment/batch/transfer)
- Suggested matches (dropdown)
- Proposed adjustment (if needed)

Workflow:
1) Load statement lines
2) Accept suggestions (one-click)
3) For unmatched:
   - create adjustment rows in "Adjustment Batch" (draft)
4) Submit adjustments for approval (TREASURY_CLERK)
5) Approve/Post adjustments (TREASURY_APPROVER)
6) Close reconciliation (difference must be 0 unless override)

---

## 5) Screen: Payroll Run (MVP) — REQUIRED

### 5.1 Run Summary (Form)
Fields:
- Pay group (UAE_MONTHLY / PAK_MONTHLY)
- Period
- Pay date
- Currency
- Status + submitted/approved metadata

Buttons (by role/status):
- Calculate
- Submit for approval
- Approve / Reject
- Post
- Generate Payment Batch
- Mark Paid (linked to Treasury transactions)
- Export (Bank CSV / WPS)

### 5.2 Payroll Adjustments Grid (MVP)
Columns:
1) Employee
2) Component (BONUS/COMMISSION/OVERTIME/REIMBURSEMENT/etc.)
3) Amount
4) Currency
5) Memo
6) COST_CENTER (default from employee; editable)
7) DEPARTMENT (default)
8) LOCATION (default)

Bulk actions:
- Paste from Excel (employee email/name mapping)
- Apply component to selected
- Apply dimensions to selected

---

## 6) Screen: Intercompany Royalty Run — REQUIRED (MVP)

### 6.1 Summary
- Period
- From entity (UAE)
- To entity (Nevis)
- Basis: Recognized Revenue
- Rate: 50%
- Computed base + computed royalty
- Status: DRAFT / PENDING_APPROVAL / APPROVED / POSTED

### 6.2 Detail Grid (read-only after generate)
Columns:
- Revenue account group
- Recognized revenue amount
- Exclusions (refunds/contra if configured)
- Royalty amount

Actions:
- Generate draft
- Submit for approval
- Approve / Reject
- Post

---

## 7) Screen: Draft Inbox (Batch Control) — STRONGLY RECOMMENDED MVP

This prevents drafts from becoming a graveyard.

Tabs:
- Journal Entries
- AP Bills
- Payroll Runs
- Reconciliation Adjustment Batches
- Royalty Runs

Columns:
- Created At
- Created By
- Entity / Book / Period
- Status
- Error Count
- Amount/Total
- Next Action (Validate / Submit / Approve / Post)

Bulk actions:
- Validate selected
- Export errors CSV
- Submit selected (role-guarded)

---

## 8) UI Acceptance Tests (What must work in demo)

1) JE: paste 30 lines from Excel, fix 2 errors, validate, submit, approve, post
2) AP bill: paste lines, bulk apply cost center, validate, post
3) Bank rec: import statement lines, accept suggestions, draft 2 adjustments, submit/approve/post, close with diff=0
4) Payroll: paste adjustments, calculate, submit/approve/post, generate WPS/bank CSV export
5) Role enforcement: preparer cannot approve/post payroll; clerk cannot post adjustments

---

**END OF UI SPEC**
