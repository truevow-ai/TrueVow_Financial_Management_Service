# TrueVow Financial Management + Treasury Services
## Complete Product Requirements Document

**Version:** 2.0  
**Date:** December 21, 2025  
**Status:** Active Development  
**Last Updated:** December 21, 2025  
**Owner:** TrueVow Internal Ops  
**Audience:** Coding Agent + Tech Lead + Finance Lead

---

## 📋 Table of Contents

1. [Non-Negotiables (Read First)](#0-non-negotiables-read-first)
2. [Executive Summary](#executive-summary)
3. [Problem Statement](#1-problem-statement)
4. [Scope & Out of Scope](#2-scope--out-of-scope)
5. [Service Boundaries (Microservices)](#3-service-boundaries-microservices)
6. [Entities, Currencies & Books](#4-entities-functional-currencies--books)
7. [Dimensions (Tags) System](#5-dimensions-tags--required-everywhere)
8. [Accounting Engine Requirements](#6-accounting-engine-requirements-fm)
9. [Subledgers & Workflows](#7-subledgers--workflows)
10. [Payroll Engine](#8-payroll-built-in)
11. [Intercompany Royalties & Transfers](#9-intercompany-royalties--transfers)
12. [API Specifications](#10-apis-versioned-v1)
13. [Data Model](#13-data-model-minimum-viable-tables)
14. [Idempotency & Sync Patterns](#14-idempotency--sync-required-patterns)
15. [Posting Matrices](#15-posting-matrices-clear-and-implementable)
16. [Security, Roles & Audit](#16-security-roles-audit)
17. [Non-Functional Requirements](#17-non-functional-requirements)
18. [Acceptance Criteria](#18-acceptance-criteria-must-pass)
19. [Seed Pack (YAML)](#19-seed-pack-yaml--single-source-of-truth)
20. [Implementation Plan](#20-implementation-plan-milestones--deliverables)
21. [Coding Agent Instructions](#21-coding-agent-instruction-set-strict)
22. [Project Structure](#project-structure)

---

## 0) Non-Negotiables (Read First)

1. **Double-entry accounting.** Every posted transaction is balanced (debits == credits).
2. **Posted journal entries are immutable.** Corrections happen via reversal + new entry.
3. **Multi-entity + multi-book (ACCRUAL + CASH) are first-class.** No "toggle basis" hacks.
4. **Everything write-side is idempotent** (Idempotency-Key + stored response).
5. **External sync is replay-safe** (sync cursor + external-id mapping + dedupe).
6. **Dimensions/tags are mandatory on journal lines** (cost center, department, etc.).
7. **Cash book is driven by Treasury cash movements** (bank/settlement), not by Billing "payment succeeded" alone.

---

## 🎯 Executive Summary

TrueVow requires an **auditable, multi-entity, multi-book, multi-currency accounting + treasury foundation** with payroll, AR/AP, deferred revenue, intercompany royalties, commissions, affiliates, and bank reconciliation.

**Primary Goal:** Build finance-grade accounting system that supports:
- General ledger (GL), chart of accounts, periods/close, reporting
- AR sourced from Billing (subscriptions, usage, invoices, payments, refunds, chargebacks)
- AP for vendors/consultants/affiliate payouts and allocations
- Treasury cash management: bank accounts, bank transactions, gateway settlements, FX conversions, intercompany transfers
- Bank reconciliation workflow
- Payroll engine (not external provider): employees, pay runs, commissions, bonuses, deductions, payouts, WPS export plugin for UAE
- Intercompany royalties: Nevis receives 50% of revenue as royalties (accounted and settled)
- Multi-currency: collect USD, spend AED/PKR, transfer USD to Nevis and Pakistan, convert when needed

**Key Differentiators:**
- **Finance-Grade Accounting:** Double-entry, immutable postings, multi-book support
- **Multi-Entity Architecture:** UAE, Nevis, Pakistan entities with separate books
- **Treasury-Driven Cash Book:** Cash reality from bank movements, not billing events
- **Built-In Payroll:** Complete payroll engine with WPS export for UAE
- **Intercompany Management:** Automated royalty calculations and settlements
- **Commission & Affiliate System:** HYBRID commission basis (recognized + collected)

---

## 1) Problem Statement

TrueVow needs an internal accounting and treasury system to manage:

- **General Ledger (GL):** Chart of accounts, periods/close, reporting
- **AR:** Sourced from Billing (subscriptions, usage, invoices, payments, refunds, chargebacks)
- **AP:** Vendors/consultants/affiliate payouts and allocations
- **Treasury:** Bank accounts, bank transactions, gateway settlements, FX conversions, intercompany transfers
- **Bank Reconciliation:** Workflow for matching and adjustments
- **Payroll Engine:** Employees, pay runs, commissions, bonuses, deductions, payouts, WPS export plugin for UAE
- **Intercompany Royalties:** Nevis receives 50% of revenue as royalties (accounted and settled)
- **Multi-Currency:** Collect USD, spend AED/PKR, transfer USD to Nevis and Pakistan, convert when needed

---

## 2) Scope & Out of Scope

### In Scope (MVP)

- **Two Microservices:** Treasury + FM
- **Entities:** UAE (Ajman), Nevis, Pakistan (Intakely + TrueVow Global Tech)
- **Two Books per Entity:** ACCRUAL + CASH
- **Multi-Currency Transactions:** FX rates stored per posting line
- **GL + Periods + Close/Lock + Reversal**
- **Billing → FM AR Sync:** Via API pull
- **Deferred Revenue:** Schedules and monthly recognition
- **Payroll (Built-In):** Salary, allowances, commissions (recognized + collected), bonuses, deductions, employer contributions (config-driven), payslips data, payout batch exports (generic bank CSV + UAE WPS plugin scaffolding)
- **AP:** Vendor bills + payments + allocations; affiliates/consultants paid via AP
- **Treasury:** Bank accounts, bank transactions import (CSV first), settlements (Stripe/TELR) via API integration later, FX conversions, transfers
- **Reconciliation:** Sessions + matching + adjustments posting
- **Core Reports:** Trial Balance, P&L, Balance Sheet, Cash Position, AR/AP aging, GL detail
- **Audit Log + Permissions + Observability**

### Explicitly Out of Scope (MVP)

- Full HR suite (leave, hiring, performance reviews workflows)
- Government filing automation (tax filings submission)
- Perfect statutory-rate accuracy baked into code (rates live in config tables and are set by Finance)
- Complex rev rec beyond "immediate vs deferred schedule"
- Automated bank feeds integration if not ready (CSV import is MVP fallback)

---

## 3) Service Boundaries (Microservices)

### 3.1 Billing Service (Existing)

**Owns:**
- Customers, subscriptions, pricing, usage calculation, invoice issuance
- Payment intent status: Stripe/TELR payments, refunds, disputes/chargebacks (logical layer)

**Provides:**
- Invoice + lines (including service period metadata)
- Payment/refund/chargeback/fee events via API pull

**Location:** `C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\2025-TrueVow-Billing-Services-App`

### 3.2 Treasury Service (New)

**Owns:**
- Bank accounts (per entity; multiple accounts; currency per account)
- Bank transactions (statement lines)
- Gateway settlements (Stripe payouts / TELR settlements) as "cash reality"
- FX conversions (realized rates)
- Transfers (including intercompany cash movements)

**Provides to FM:**
- Bank transactions feed + settlement objects + conversion objects + transfer objects
- Reconciliation inputs and cash book truth

### 3.3 FM Service (New)

**Owns:**
- Accounting system of record: GL + subledgers + reports
- AR/AP, payroll, intercompany balances, deferred revenue
- Posting engine to ACCRUAL and CASH books
- Reconciliation workflow and adjustments posting

---

## 4) Entities, Functional Currencies & Books

### Entities

1. **TV_UAE:** TrueVow Global Tech FZE LLC (Ajman UAE)
   - **Functional Currency:** AED
   - **Role:** Head Office, Distribution, Customer Management, Contracts, Billing, Collection

2. **TV_NEVIS:** TrueVow Global Technologies (Nevis)
   - **Functional Currency:** USD
   - **Role:** Owner of the Software

3. **TV_PAK_INT:** Intakely Technologies PVT LTD (Pakistan)
   - **Functional Currency:** PKR
   - **Role:** Engineering, Implementation, Deployment, Maintenance

4. **TV_PAK_TV:** TrueVow Global Technologies PVT LTD (Pakistan)
   - **Functional Currency:** PKR
   - **Role:** Sales, Marketing, Customer Support, Operations

### Books per Entity

- **ACCRUAL** - Accrual basis accounting
- **CASH** - Cash basis accounting

**Key Rule:** Every accounting object is scoped by `(legal_entity_id, book_id)`.

---

## 5) Dimensions (Tags) — Required Everywhere

### Dimensions

- **COST_CENTER:** DEV, SALES, GNA
- **DEPARTMENT:** Engineering, Sales, Finance, Support, Marketing, Admin
- **LOCATION:** UAE, Pakistan, Nevis
- **CHANNEL:** Direct, Affiliate, Partner
- **PRODUCT:** TrueVowCore, AddOns
- **EMPLOYEE_TYPE:** Employee, Contractor, Affiliate

### Storage

- `dimension(code, name)`
- `dimension_value(dimension_code, value_code, value_name)`
- `journal_line_dimension(journal_line_id, dimension_value_id)`

### Validation

- Journal lines must include at least **COST_CENTER + DEPARTMENT + LOCATION**
- AR/AP/payroll generated postings must auto-attach default dimensions based on source object

---

## 6) Accounting Engine Requirements (FM)

### 6.1 Chart of Accounts (CoA)

- CoA per entity, per book (can be seeded from template)
- Account types: assets/liabilities/equity/revenue/expense + special types (AR/AP/CASH/DEFERRED/etc.)
- Support "mapping keys" for system postings:
  - `gl_account_mapping(legal_entity_id, book_id, map_key, gl_account_id)`

### 6.2 Journal Entries (JE)

- **JE States:** DRAFT, POSTED, REVERSED
- **JE Source Tracking:**
  - `source_service` (billing/treasury/fm/payroll/ap/manual)
  - `source_type` (invoice_issued, payout_received, payroll_run_posted, etc.)
  - `source_id` (external id or internal id)
  - `idempotency_key`

### 6.3 Periods + Close/Lock

- Accounting periods: **Monthly**
- **Period States:** OPEN, SOFT_CLOSED, CLOSED, LOCKED
- **Posting Rules:**
  - **OPEN:** Allowed
  - **SOFT_CLOSED:** Allowed with elevated role + audit reason
  - **CLOSED/LOCKED:** Blocked (must post adjustment into next open period with linkage)

### 6.4 Multi-Currency on Every Line

- Store both **transaction currency (TC)** and **functional currency (FC)** on journal lines:
  - `debit_tc`/`credit_tc` + `currency`
  - `debit_fc`/`credit_fc`
  - `fx_rate` + `fx_source` + `fx_timestamp`
- FX gain/loss account mapping exists per entity/book

---

## 7) Subledgers & Workflows

### 7.1 AR (from Billing)

FM AR mirrors Billing invoices and status.

**Objects:**
- `ar_customer` (mapped to billing customer)
- `ar_invoice` + lines (service period metadata)
- `ar_payment` + allocations
- `ar_credit`/refund/chargeback adjustments

**Posting - ACCRUAL Book:**
- **Invoice issued (deferrable):**
  - Dr AR
  - Cr Deferred Revenue
- **Invoice issued (immediate):**
  - Dr AR
  - Cr Revenue
- **Revenue recognition (monthly schedule):**
  - Dr Deferred Revenue
  - Cr Revenue
- **Payment received:**
  - Dr Cash Clearing (or Bank)
  - Cr AR
- **Fees:**
  - Dr Processing Fee Expense
  - Cr Cash
- **Refund/chargeback:**
  - Dr Contra Revenue / Chargeback Expense
  - Cr Cash (or AR reopening)

**Posting - CASH Book:**
- **Customer cash receipt deposit:**
  - Dr Bank Cash
  - Cr Cash Revenue (or Revenue)
- **Gateway fee debit:**
  - Dr Processing Fee Expense
  - Cr Bank Cash
- **Refund:**
  - Dr Contra Revenue/Refunds
  - Cr Bank Cash

**Key:** CASH book events come from Treasury settlement/bank transactions.

### 7.2 Deferred Revenue

- `revenue_schedule` generated from invoice lines with `service_start`/`service_end`
- **Cadence:** Monthly (MVP)
- Schedule runner produces recognition JEs per period, idempotent per `(schedule_period_id, book_id)`

### 7.3 AP (vendors, consultants, affiliates)

**Objects:**
- `ap_vendor`
- `ap_bill` + lines
- `ap_payment` + allocations
- `ap_withholding_profile` (optional, config-driven)

**Posting - ACCRUAL:**
- **Bill:**
  - Dr Expense/Asset
  - Cr AP
- **Pay:**
  - Dr AP
  - Cr Cash

**Posting - CASH:**
- **Pay only when cash moves:**
  - Dr Expense
  - Cr Cash

**Consultants:** Model as AP vendors with contract metadata.

**Affiliates:** Earned commissions accrue payable, then pay via AP.

### 7.4 Treasury (bank cash reality)

Treasury stores:
- Bank accounts
- Bank statement lines
- Settlements/payouts (Stripe/TELR)
- FX conversions with realized rates
- Transfers (including intercompany)

Treasury provides API pull endpoints for FM.

### 7.5 Bank Reconciliation

**Workflow:**
1. Create `reconciliation_session` (bank_account, statement period, ending balance)
2. Import statement lines (from Treasury)
3. Match statement lines to:
   - AR receipts (settlements)
   - AP payments
   - Payroll payments
   - Transfers
   - FX conversions
   - Fees
4. Unmatched can be posted as adjustments (requires account selection + dimensions)
5. Close only when difference == 0, or require override approval + reason (config flag)

---

## 8) Payroll (Built-In)

### 8.1 People Types

- **Employee** (paid via payroll)
- **Contractor/Consultant** (paid via AP)
- **Affiliate** (paid via AP)

### 8.2 Payroll Engine Capabilities

**Employee Master Data:**
- Entity, country, location, pay group, currency
- Bank/WPS fields (store required identifiers even if bank not finalized)
- Base salary + component assignments
- Commission plan + bonus plan links
- Deduction profiles (loans, advances)
- Statutory profile (config keys; not hardcoded law)

**Pay Components:**
- **Earnings:** BASIC, HOUSING, TRANSPORT, OVERTIME, COMMISSION, BONUS, REIMBURSEMENT
- **Deductions:** TAX_WITHHOLDING, BENEFIT_EMP, LOAN_DEDUCT, ADVANCE_DEDUCT
- **Employer Contributions:** GPSSA_EMPR, EOBI_EMPR, SOCIALSEC_EMPR (placeholders; finance sets)

**Formula/Rules Engine:**
- Safe deterministic expression language
- Configurable per entity/country rule set
- Supports caps, floors, conditional logic

### 8.3 Commission + Bonus

**Commissions:**
- **HYBRID plan:** Earned on both recognized revenue and collected cash
- Basis components configurable by role/employee/team and SKU/product filters
- Commission ledger accrues payable
- Payout can be via payroll or AP (default payroll for employees)

**Bonuses:**
- One-time or periodic
- Can accrue and pay later

### 8.4 Payroll Run Lifecycle

**Statuses:** DRAFT → CALCULATED → APPROVED → POSTED → PAID → CLOSED

**Rules:** POSTED runs immutable; changes require adjustment run or reversal.

### 8.5 Payroll Posting

**ACCRUAL:**
- At posting time (pay date or period end based on config):
  - Dr Wages/Allowances/Commission/Bonus Expense
  - Dr Employer contribution expense
  - Cr Payroll Payable (net)
  - Cr Tax/Benefits/Contribution payables

**CASH:**
- When cash is actually paid (Treasury bank movement):
  - Dr Payroll Payable / liabilities
  - Cr Cash

### 8.6 Payroll Payout Exports

- Generic Bank CSV exporter (per bank template)
- UAE WPS exporter plugin system:
  - Generic SIF structure as baseline
  - Bank-specific adapters later when bank chosen
- Store every generated file payload hash + metadata and link to `payroll_payment_batch`

---

## 9) Intercompany Royalties & Transfers

### 9.1 Royalties: 50% of Revenue to Nevis (Policy)

**Accrual recognition-driven monthly (recommended):**

**Determine royalty base:**
- Recognized revenue in UAE ACCRUAL book (exclude refunds/contra as configured)

**Calculate 50% royalty amount**

**Post reciprocal entries:**

**UAE (ACCRUAL):**
- Dr Royalty Expense
- Cr Intercompany Payable (to Nevis)

**Nevis (ACCRUAL):**
- Dr Intercompany Receivable (from UAE)
- Cr Royalty Income

**Settlement (when paid, via Treasury transfers):**
- **UAE:**
  - Dr Intercompany Payable
  - Cr Cash
- **Nevis:**
  - Dr Cash
  - Cr Intercompany Receivable

### 9.2 Transfers to Pakistan

Treat as configurable:
- Service fee, cost reimbursement, intercompany loan, etc.
- MVP: Default to intercompany payable/receivable with manual classification option

### 9.3 Transfers to Pakistan (Intakely + TrueVow)

Treat as configurable:
- Salaries, ops, vendors, commissions, bonus, liabilities, intercompany loans, etc.

---

## 10) APIs (Versioned /v1)

### 10.1 Common API Rules

- All write endpoints accept: **Idempotency-Key header**
- All endpoints return: **correlation_id**
- Pagination on list endpoints
- Role-based access control

### 10.2 Treasury Service API (Minimum)

**Base:** `/v1`

**Health:**
- `GET /health`

**Bank Accounts:**
- `POST /bank-accounts`
- `GET /bank-accounts`
- `GET /bank-accounts/{id}`

**Bank Transactions:**
- `POST /bank-transactions/import` (CSV)
- `GET /bank-transactions?updated_after=...&limit=...&cursor=...`
- `GET /bank-transactions/{id}`

**Settlements:**
- `POST /settlements/stripe/import` (manual/CSV/json)
- `POST /settlements/telr/import`
- `GET /settlements?updated_after=...`

**FX Conversions:**
- `POST /fx/conversions` (record realized conversion)
- `GET /fx/conversions?updated_after=...`

**Transfers:**
- `POST /transfers` (intercompany or intra-entity)
- `GET /transfers?updated_after=...`

**Sync Cursors:**
- `GET /sync/status`

### 10.3 FM Service API (Minimum)

**Base:** `/v1`

**Health:**
- `GET /health`

**Entities/Books:**
- `POST /entities`
- `GET /entities`
- `POST /entities/{entity_id}/books` (create ACCRUAL & CASH)
- `GET /entities/{entity_id}/books`

**Dimensions:**
- `POST /dimensions`
- `POST /dimensions/{code}/values`
- `GET /dimensions`
- `GET /dimensions/{code}/values`

**CoA:**
- `POST /books/{book_id}/accounts`
- `GET /books/{book_id}/accounts`
- `PATCH /accounts/{account_id}`
- `POST /books/{book_id}/account-mappings` (map_key → gl_account)

**Periods:**
- `POST /books/{book_id}/periods/generate`
- `GET /books/{book_id}/periods`
- `POST /periods/{period_id}/close`
- `POST /periods/{period_id}/lock`

**Journal Entries:**
- `POST /books/{book_id}/journal-entries`
- `GET /books/{book_id}/journal-entries`
- `GET /journal-entries/{id}`
- `POST /journal-entries/{id}/reverse`

**Billing Sync:**
- `POST /integrations/billing/sync` { entity_id, since_cursor?, full_resync? }
- `GET /integrations/billing/status`

**Treasury Sync:**
- `POST /integrations/treasury/sync` { entity_id, since_cursor?, full_resync? }
- `GET /integrations/treasury/status`

**AR:**
- `GET /books/{book_id}/ar/invoices`
- `GET /books/{book_id}/ar/aging`
- `GET /books/{book_id}/ar/customers/{id}/balance`

**Deferred Revenue:**
- `POST /books/{book_id}/revrec/run?period_id=...`
- `GET /books/{book_id}/revrec/schedules`

**AP:**
- `POST /books/{book_id}/ap/vendors`
- `POST /books/{book_id}/ap/bills`
- `POST /books/{book_id}/ap/bills/{bill_id}/pay`
- `GET /books/{book_id}/ap/aging`

**Payroll:**
- `POST /entities/{entity_id}/employees`
- `GET /entities/{entity_id}/employees`
- `POST /entities/{entity_id}/pay-groups`
- `POST /entities/{entity_id}/pay-components`
- `POST /entities/{entity_id}/commission-plans`
- `POST /entities/{entity_id}/bonus-plans`
- `POST /books/{book_id}/payroll/runs`
- `POST /payroll/runs/{run_id}/calculate`
- `POST /payroll/runs/{run_id}/approve`
- `POST /payroll/runs/{run_id}/post`
- `POST /payroll/runs/{run_id}/generate-payment-batch`
- `POST /payroll/runs/{run_id}/mark-paid`
- `POST /payroll/runs/{run_id}/reverse`
- `GET /payroll/runs/{run_id}/export/wps`
- `GET /payroll/runs/{run_id}/export/bank-csv`

**Intercompany:**
- `POST /intercompany/relationships` (royalty 50% config)
- `POST /books/{book_id}/intercompany/royalties/run?period_id=...`
- `GET /books/{book_id}/intercompany/balances`

**Reconciliation:**
- `POST /bank-accounts/{bank_account_id}/reconciliations`
- `POST /reconciliations/{rec_id}/match`
- `POST /reconciliations/{rec_id}/close`
- `GET /reconciliations/{rec_id}`

**Reporting:**
- `GET /books/{book_id}/reports/trial-balance`
- `GET /books/{book_id}/reports/pl`
- `GET /books/{book_id}/reports/balance-sheet`
- `GET /books/{book_id}/reports/cash-position`
- `GET /books/{book_id}/reports/gl-detail`

---

## 13) Data Model (Minimum Viable Tables)

### Shared Concepts
- `legal_entity`
- `book`
- `dimension`
- `dimension_value`
- `journal_line_dimension`
- `audit_log`
- `idempotency_keys`
- `external_sync_cursor`
- `source_object_map` (source, object_type, external_id, internal_id, entity_id, book_id)

### FM Core
- `gl_account`
- `gl_account_mapping`
- `accounting_period`
- `journal_entry`
- `journal_line`

### AR
- `ar_customer`
- `ar_invoice`
- `ar_invoice_line`
- `ar_payment`
- `ar_allocation`

### Deferred Revenue
- `revenue_schedule`
- `revenue_schedule_period`

### AP
- `ap_vendor`
- `ap_bill`
- `ap_bill_line`
- `ap_payment`
- `ap_allocation`
- `ap_withholding_profile` (optional)

### Payroll
- `hr_employee`
- `hr_employee_bank`
- `pay_group`
- `pay_component_definition`
- `pay_component_assignment`
- `pay_rule_set`
- `pay_rule`
- `stat_contribution_rule`
- `tax_withholding_table`
- `payroll_run`
- `payroll_run_item`
- `payroll_run_component_line`
- `payroll_payment_batch`
- `payroll_export_template`
- `payroll_liability_balance`
- `commission_plan`
- `commission_rule`
- `commission_ledger`
- `bonus_plan`
- `bonus_result`

### Affiliates
- `affiliate_partner`
- `affiliate_agreement`
- `affiliate_earning_event`
- `affiliate_payout`

### Treasury
- `treasury_bank_account`
- `treasury_bank_transaction`
- `treasury_settlement`
- `treasury_fx_conversion`
- `treasury_transfer`
- `treasury_import_cursor`

---

## 14) Idempotency & Sync (Required Patterns)

### 14.1 Write API Idempotency

- `idempotency_keys`: (key, route, request_hash) → response_blob
- On repeated key+route with same hash, return stored response
- If key repeats with different hash, reject (409 conflict)

### 14.2 External Sync Pattern (Billing/Treasury)

- `external_sync_cursor` per (source, entity, object_type)
- `source_object_map` to map external IDs to internal IDs
- For each imported object:
  - Upsert with external_id unique constraint
  - Ensure posting JEs are unique on (entity, book, source_service, source_type, source_id)

---

## 15) Posting Matrices (Clear and Implementable)

### 15.1 Billing → AR (ACCRUAL)

**Invoice issued (deferrable line):**
- Dr AR
- Cr Deferred Revenue

**Invoice issued (immediate):**
- Dr AR
- Cr Revenue

**Revenue recognition (monthly):**
- Dr Deferred Revenue
- Cr Revenue

**Payment received (optional clearing):**
- Dr Cash Clearing
- Cr AR

### 15.2 Treasury → Cash Book (CASH)

**Bank deposit from gateway/customer:**
- Dr Bank Cash
- Cr Cash Revenue (or Revenue)

**Gateway fee debit:**
- Dr Processing Fee Expense
- Cr Bank Cash

**Refund outflow:**
- Dr Contra Revenue / Refunds
- Cr Bank Cash

### 15.3 AP (ACCRUAL)

**Bill:**
- Dr Expense/Asset
- Cr AP

**Payment:**
- Dr AP
- Cr Bank Cash

### 15.4 Payroll (ACCRUAL)

**Post run:**
- Dr Wages/Allow/Commission/Bonus Expense
- Dr Employer contribution expense
- Cr Payroll Payable (net)
- Cr Tax/Benefits payables

**Pay cash (CASH / from Treasury movement):**
- Dr Payroll Payable / liabilities
- Cr Bank Cash

### 15.5 Intercompany Royalties (ACCRUAL)

**Monthly accrual:**
- UAE: Dr Royalty Expense, Cr Interco Payable
- Nevis: Dr Interco Receivable, Cr Royalty Income

**Settlement:**
- UAE: Dr Interco Payable, Cr Cash
- Nevis: Dr Cash, Cr Interco Receivable

### 15.6 FX Conversions (Treasury-driven)

**On realized conversion (USD→AED):**
- Dr AED Bank Cash (TC= AED, FC= AED for UAE)
- Cr USD Bank Cash (TC= USD, FC= AED via fx)
- Post difference to FX Gain/Loss if needed (realized)

---

## 16) Security, Roles, Audit

### Roles
- `FM_ADMIN`
- `ACCOUNTANT`
- `PAYROLL_ADMIN`
- `AP_CLERK`
- `AR_CLERK`
- `TREASURY_ADMIN`
- `VIEWER`
- `SERVICE` (integration pulls)

### Audit
- Every mutation writes `audit_log`:
  - `actor_id`, `role`, `action`, `object_type`, `object_id`, `before`, `after`, `reason`, `timestamp`

---

## 17) Non-Functional Requirements

- **ACID Posting:** All posting operations in DB transactions
- **Observability:** Structured logs + metrics + correlation IDs
- **Performance:**
  - Index `journal_line` on (book_id, gl_account_id, posted_at)
  - Index AR/AP aging fields
  - Consider materialized views later; keep schema ready
- **Backups + Migrations:** Must be safe and reversible

---

## 18) Acceptance Criteria (Must Pass)

1. Multi-entity + ACCRUAL/CASH books exist and operate independently
2. Journal postings balance and are immutable after posting
3. Billing sync is replay-safe: same invoice/payment imported twice produces no duplicate JEs
4. Treasury sync drives CASH book correctly from bank movements
5. Deferred revenue monthly run posts correct recognition entries idempotently
6. Payroll run calculates, posts, generates payout file metadata, and can be reversed
7. Commissions HYBRID accrual works (recognized + collected components)
8. Affiliate payout supports both monthly and threshold-based carry-forward
9. Dimensions are enforced and appear on all system-generated journal lines
10. Reports (TB, P&L, BS) reconcile with ledger totals

---

## 19) Seed Pack (YAML) — Single Source of Truth

See separate seed YAML file for complete configuration. Key elements:
- Entities (TV_UAE, TV_NEVIS, TV_PAK_INT, TV_PAK_TV)
- Dimensions (COST_CENTER, DEPARTMENT, LOCATION, CHANNEL, PRODUCT, EMPLOYEE_TYPE)
- Chart of Accounts template
- GL mapping keys
- Treasury bank accounts
- Payroll pay groups, components, export templates
- Commission plans
- Affiliate agreements
- Intercompany royalty relationships

---

## 20) Implementation Plan (Milestones + Deliverables)

### Development Approach

**Backend-First Strategy:**
- Milestones 0-7: Backend services and APIs
- Milestones 8-14: UI/UX development (can run parallel after Milestone 8)

**Parallel Development:**
- UI foundation (Milestone 8) can start after Milestone 1
- UI modules can be developed in parallel with backend milestones
- Final integration and polish (Milestone 14) after all features complete

### Milestone 0 — Repo + Platform (2–4 days)
- Create two services: treasury-service, fm-service
- DB migrations + OpenAPI generation + auth middleware
- Observability skeleton (logs + correlation IDs)
- Seed loader (reads YAML and inserts into DB)

**Deliverables:** Running docker-compose with Postgres + both services + seeded data

### Milestone 1 — FM Core Ledger (1–2 weeks)
- CoA + mappings
- Periods generate/close/lock
- Journal entry create/post/reverse with validations + immutability
- Dimensions enforced on journal lines

**Tests:** JE balancing tests, period lock tests, idempotency tests

### Milestone 2 — Treasury Core (1–2 weeks)
- Bank accounts CRUD
- Bank tx import CSV + list with cursor
- Transfers + FX conversions recording
- Settlement import endpoints (manual JSON/CSV for MVP)

**Tests:** Cursor pagination, duplicate bank line dedupe, FX conversion integrity

### Milestone 3 — Sync + Cash Book Posting (1–2 weeks)
- FM pulls Treasury transactions and posts CASH book entries
- Mapping rules for deposits/fees/refunds/transfers/FX
- Create reconciliation session workflow (basic matching)

### Milestone 4 — Billing AR + Deferred Revenue (2–3 weeks)
- Billing adapter client interface + incremental sync + mapping tables
- AR invoice and payment ingestion
- Deferred revenue schedules created from invoice lines
- Monthly revrec runner posts recognition JEs (idempotent)

### Milestone 5 — Payroll Engine (2–3 weeks)
- Employee master + pay components + rule engine
- Payroll runs: calculate → approve → post (ACCRUAL) + batch export
- WPS exporter plugin interface + generic SIF output
- Mark-paid via Treasury bank movements (linking)

### Milestone 6 — Commissions + Bonuses + Affiliates/AP (2–3 weeks)
- Commission HYBRID ledger generation:
  - Recognized component from FM recognized revenue
  - Collected component from Treasury cash receipts
- Affiliate earnings ledger + payout policy (monthly + threshold carry-forward)
- AP vendor bills/payments for consultants and affiliates

### Milestone 7 — Reporting + Hardening (2–3 weeks)
- Trial Balance, P&L, Balance Sheet, Cash Position, AR/AP aging, GL detail
- Indexing + performance checks
- Expand reconciliation matching + adjustment postings
- Audit log coverage review

### Milestone 8 — UI/UX Foundation (1–2 weeks)
- UI framework selection and setup (React/Vue/Server-side templates)
- Design system and component library
- Authentication UI (login, token management)
- Layout and navigation structure
- Responsive design framework
- Accessibility (WCAG 2.1 AA compliance)

**Deliverables:** Working UI foundation with authentication and navigation

### Milestone 9 — Core UI Modules (2–3 weeks)
- Dashboard and overview pages
- Journal Entry UI (create, view, post, reverse)
- Chart of Accounts management UI
- Period management UI (generate, close, lock)
- Dimensions management UI
- Basic reporting UI (Trial Balance, P&L preview)

**Dependencies:** Milestone 1 (FM Core Ledger), Milestone 8 (UI Foundation)

### Milestone 10 — AR/AP UI Modules (2–3 weeks)
- AR Summary pages (list, detail, aging reports)
- AP Vendor management UI
- AP Invoice entry and management UI
- AP Payment processing UI
- AR/AP aging reports UI
- Deferred revenue schedule UI

**Dependencies:** Milestone 4 (Billing AR + Deferred Revenue), Milestone 9 (Core UI)

### Milestone 11 — Payroll UI Modules (2–3 weeks)
- Employee management UI (list, profile, form)
- Payroll run UI (create, calculate, approve, post)
- Payroll component management UI
- Commission plan configuration UI
- Bonus plan configuration UI
- Payroll export UI (WPS, CSV)
- Payroll reports and payslips UI

**Dependencies:** Milestone 5 (Payroll Engine), Milestone 9 (Core UI)

### Milestone 12 — Treasury & Reconciliation UI (2–3 weeks)
- Bank account management UI
- Bank transaction import UI (CSV upload)
- Bank reconciliation UI (matching, adjustments)
- FX conversion UI
- Transfer management UI
- Cash position dashboard

**Dependencies:** Milestone 2 (Treasury Core), Milestone 3 (Sync + Cash Book), Milestone 9 (Core UI)

### Milestone 13 — Reporting & Analytics UI (2–3 weeks)
- Financial reports UI (Trial Balance, P&L, Balance Sheet)
- Cash flow statement UI
- GL detail viewer UI
- Report export functionality (PDF, Excel)
- Custom report builder UI (basic)
- Dashboard with key metrics

**Dependencies:** Milestone 7 (Reporting + Hardening), Milestone 9 (Core UI)

### Milestone 14 — UI Polish & Integration (1–2 weeks)
- UI/UX refinements based on user feedback
- Performance optimization (lazy loading, caching)
- Mobile responsiveness testing and fixes
- Accessibility audit and improvements
- Cross-browser testing
- User acceptance testing (UAT)
- Documentation and help system

**Dependencies:** All previous UI milestones

---

## 21) Coding Agent Instruction Set (Strict)

1. **Do not hardcode statutory rates.** Store in config tables; seed with zeros.
2. **Every write endpoint must support Idempotency-Key** and return stable IDs.
3. **Every external object must be mapped** with `source_object_map` and protected by unique constraints.
4. **All postings happen inside DB transactions.**
5. **All system-generated lines must include required dimensions** (auto defaults).
6. **No edits to posted JEs;** implement reversal endpoint.
7. **CASH book postings only from Treasury movements.**
8. **Build adapters as interfaces** (BillingAdapter, TreasuryAdapter) so sources can change without refactor.
9. **Implement "safe formula evaluator"** for payroll rules:
   - No arbitrary code execution
   - Deterministic and testable
10. **Provide integration tests** that simulate:
    - Replayed billing sync
    - Replayed treasury sync
    - Revrec run repeated twice
    - Payroll posting repeated twice

---

## Project Structure

### Granular, Junior-Developer-Friendly Architecture

Each module is self-contained with predictable sub-folders. A junior developer can easily navigate to any component, page, route, script, or asset without searching through a "sea of code".

**Structure Pattern:**
```
app/modules/{module_name}/
├── pages/                    # UI pages/templates organized by feature
├── api/routes/               # API endpoints organized by resource
├── scripts/
│   ├── calculations/        # Calculation logic
│   ├── validators/          # Validation logic
│   └── processors/          # Processing logic
├── services/                # Service layer classes
├── models/                   # Database models
├── repositories/             # Data access layer
├── schemas/                  # Pydantic schemas
├── assets/                   # Static assets (CSS, JS, images)
├── utils/                    # Module-specific utilities
└── tests/                    # Tests (unit, integration, fixtures)
```

**Navigation Examples:**
- Employee Profile Page: `app/modules/hr_payroll/pages/employees/employee_profile.html`
- Salary Calculator: `app/modules/hr_payroll/scripts/calculations/salary_calculator.py`
- Payroll API Route: `app/modules/hr_payroll/api/routes/payroll.py`
- Employee Validator: `app/modules/hr_payroll/scripts/validators/employee_validator.py`
- Payroll Tests: `app/modules/hr_payroll/tests/unit/calculations/test_salary_calculator.py`

For detailed structure, see [FM_Service_Detailed_Implementation_Guide.md](./FM_Service_Detailed_Implementation_Guide.md#component-architecture).

---

## 🔄 Document Maintenance

**Update Frequency:** This document should be updated:
- After each milestone completion
- When requirements change
- When new features are added
- When scope changes
- At least monthly for status updates

**Change Log:**
- **v2.1 (2025-12-21):** Added UI/UX development milestones (8-14)
- **v2.0 (2025-12-21):** Comprehensive PRD with Treasury + FM microservices, multi-entity, multi-book, payroll, intercompany, commissions
- **v1.0 (2025-12-21):** Initial PRD creation

---

**Document Owner:** TrueVow Internal Ops  
**Reviewers:** Engineering, Finance, Security  
**Approval Status:** Pending Approval
