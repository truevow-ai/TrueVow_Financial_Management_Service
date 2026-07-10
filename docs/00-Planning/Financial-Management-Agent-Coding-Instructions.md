# Financial Management — Coding Agent Operating Instructions
## Read This Before Writing a Single Line of Code

**Version:** 1.0
**Date:** July 2026
**Classification:** Engineering — Required Reading
**Service:** TrueVow Financial Management & Treasury — back-office double-entry accounting engine for TrueVow's OWN finances
**Trust domain:** PLATFORM_OPERATORS — internal TrueVow staff (finance controller, accountant, CFO)
**Prerequisite:** FM Service PRD, `ADDENDUM_A_ACCOUNTING_CONTROLS.md`, `ADDENDUM_D_ENGINEERING_RULES.md`, the FM AGENTS.md, the platform AGENTS.md

> This document is the operating standard for every line of code in the Financial Management service. It is not a set of guidelines. Any deviation requires explicit justification in the PR description and sign-off from the product owner.

---

## The One Thing That Matters Most

The person this service serves is **the TrueVow finance operator** — a controller, accountant, or CFO — who is responsible for TrueVow's actual books. Their job is to produce financial statements that are accurate enough to stand up to a tax audit, an investor diligence review, or a bank reconciliation. They are not a developer. They cannot read a stack trace. What they see in the UI must be the truth, because they will make decisions — and sign their name — based on it.

Every decision you make — every money type you use, every rounding rule, every posting atomicity, every audit trail entry — must be made with that finance operator in mind.

Not you. Not the demo. **That finance operator.**

If a journal entry that doesn't balance (debits != credits) is allowed to post, you have failed, and the books are corrupt. If a posted entry is edited in-place instead of reversed and re-posted, you have failed, and the audit trail is destroyed. If deferred revenue is booked to revenue in full instead of recognized monthly, you have failed, and the P&L is materially misstated. If an intercompany royalty posts to one entity but not the other, you have failed, and cross-entity reconciliation is broken. If the Billing-to-AR sync fails silently and collected revenue never appears in the GL, you have failed. If the UAE WPS payroll export is malformed and employees are not paid on time, you have failed — and that failure has real human consequences.

The second person this service serves is **the entity auditor** — external or internal — who will one day trace every number back to its source. Every shortcut you take today, every missing dimension, every soft-delete of a posted record, every stored float where a Decimal should be, will show up in their sample and become a finding. An unqualified audit opinion is a business asset. A qualified opinion is a fundraiser-killer.

Everything below exists because breaking it eventually hurts one of those two people — and by extension, the company's ability to operate, raise money, and pay its people.

---

## Part 0 — What Financial Management Is (So You Don't Break It)

Financial Management is TrueVow's **back-office double-entry accounting engine.** It is the single source of truth for the company's own books — not tenant books, not billing records, not SaaS admin metadata. It manages the general ledger, accounts receivable (AR synced from the Billing service), accounts payable, cash flow, profit & loss, payroll (including UAE WPS export), multi-currency treasury (USD/AED/PKR), bank reconciliation, intercompany royalties (Nevis 50%), commissions and affiliates, and tax — across the UAE (Ajman), Nevis, and Pakistan (Intakely + TrueVow Global Tech) legal entities.

The defining architectural fact: **this is a finance-grade system, not a CRUD app with a ledger table.** Every write that touches money must be idempotent, atomic, balanced, and audited. Posted entries are immutable — the only way to correct a posted journal entry is to reverse it (equal-and-opposite entry) and re-post. Closed accounting periods accept no entries. Every table has Row-Level Security scoped to `legal_entity_id`. Every subledger (AR, AP, Payroll, Treasury) posts into the GL through a single `LedgerPoster` seam, never by directly importing `JournalEntryService`.

Two constraints are non-negotiable and predate you:
1. **Double-entry balance invariant**: `sum(debits) == sum(credits)` on every posted journal entry. Every time. Never bypassed. Never relaxed for "bulk convenience."
2. **Immutable postings**: Once a journal entry has `status = posted`, its lines are immutable. Correction is always reversal-and-repost. Never an UPDATE on posted line amounts.

---

## Part 1 — Build Philosophy

### 1.1 Boring is a Feature
Do not adopt a new framework because it is interesting, or a new accounting abstraction because it demoed well at a fintech conference. Use the oldest, most boring, most documented solution that works. Boring double-entry code still balances in three years when the person who wrote it is gone and the auditor is in the room. **The test:** *Has this been done 10,000 times and does it have a Stack Overflow answer from 2018?* If yes, do it that way.

### 1.2 Simple is Not Simplistic
Simple code is the hardest code to write — it requires understanding the problem deeply enough to solve it without cleverness. Simple code has one function that does one thing, names that say what they contain, functions short enough to see on one screen, no nested ternaries or magic, and comments that explain *why*. **Junior developer test:** can a developer who has never seen this codebase understand a function in 30 seconds? If not, rewrite it.

### 1.3 No Premature Abstractions
The `LedgerPoster` seam exists because routing every subledger through a single posting path is a *real, known* requirement — that abstraction earns its keep. The `SubledgerSync` interface exists because the AR sync from Billing needs idempotent replay semantics. Everything else: build the simplest thing that works today. **Write the code twice before you abstract it.** If you are writing the third copy, abstract then — not before.

### 1.4 The Finance Operator is Always Right About the Number
If a finance operator sees a number on screen that doesn't match what they expect from the source system or the bank statement, the behavior is wrong — even if the code is technically correct to its own logic. When unsure about a financial display decision, ask: *would a controller signing a P&L to the board believe this number?* Build that.

---

## Part 2 — Code Quality Rules (Non-Negotiable)

### 2.1 Every Function Does One Thing
A function that does two things is two functions. Max length is what fits on one screen (~40–50 lines including docstring). `post_journal_entry()` and `validate_balance()` are two functions, not one.

### 2.2 Name Everything Like a Sentence
Code is read far more than written. `compute_deferred_revenue_rollforward(schedule_id, period_end)` — not `roll_fwd(s, p)`. Never single-letter names outside loop counters. Never abbreviate unless the full word exceeds 15 characters. Never name a variable `data`, `result`, `info`, `obj`, `thing`, or `stuff`.

### 2.3 Explicit Over Implicit
Never rely on implicit behavior when explicit is available. Keyword arguments, not positional. No `*args`/`**kwargs` in business logic. Name posting parameters explicitly — a mis-ordered positional argument in a journal entry silently corrupts the books.

### 2.4 Type Everything
Every function signature, model field, and return value is typed. Run `mypy` on every commit and fail CI on errors. Type hints are part of the code, not optional documentation. Money-typed returns must use `Decimal`, never `float`.

### 2.5 Handle Every Error Path — Especially During Posting
No bare `except:`, no swallowed exceptions, no silent failures. A posting operation is a multi-step atomic unit; an unhandled exception mid-transaction must roll back completely and produce an observable, actionable error — not a half-posted entry that leaves the books unbalanced.

```python
# Wrong — a swallowed exception here is a corrupt ledger
try:
    await post_journal_entry(db, entry, user_id)
except Exception:
    pass

# Right — explicit, logged, rolled back, and returns an error the finance operator can act on
try:
    await post_journal_entry(db, entry, user_id)
except PostingValidationError as e:
    logger.warning(
        "Posting rejected — validation failed",
        extra={"entity_id": str(entry.entity_id), "book_id": str(entry.book_id), "error": str(e)},
    )
    raise HTTPException(status_code=422, detail={"code": "POSTING_REJECTED", "message": str(e)})
```

### 2.6 DRY — But Not at the Cost of Clarity
Don't Repeat Yourself is a guideline, not a religion. If extracting a shared helper forces a reader to jump files to understand a payroll posting, the duplication is better. **Never** share code *between accounting and non-accounting modules* just to avoid duplication — that is exactly how a non-accounting change breaks a posting invariant (see §3.4).

### 2.7 Comments Explain Why, Not What

```python
# Wrong — restates the code
# round the amount to 2 decimal places
rounded = round_money(amount, currency)

# Right — explains the financial reason
# USD/AED/PKR all use 2 decimal places. We use HALF_UP rounding because the auditor
# expects the same rounding convention as the UAE banks and TELR settlement files.
rounded = round_money(amount, currency)
```

### 2.8 Write the Test Before You Think You're Done
Every piece of business logic has a test before the PR opens — not after. The pyramid: unit tests for posting validation, balance checks, SoD rules, and commission calculations; integration tests for each subledger's posting path against a real database transaction; at least one end-to-end test per subledger (payroll run, AR sync, royalty run, bank reconciliation adjustment) that posts to GL and verifies the trial balance. Coverage floor is 80%; the **posting validation, balance invariant, SoD enforcement, and idempotency logic must be at 95%+** and must have tests proving they reject/block when they should.

---

## Part 3 — Architecture Rules (Non-Negotiable)

### 3.1 One Module Per Subledger / One File Per Resource
Follow the repo layout exactly: `app/modules/general_ledger/`, `app/modules/accounts_receivable/`, `app/modules/accounts_payable/`, `app/modules/payroll/`, `app/modules/treasury/`, `app/modules/intercompany/`. Each module owns its API routes, models, repositories, services, and schemas.

### 3.2 Never Edit Core Modules to Fix One Subledger
This rule has its own section because the mistake is catastrophic. `app/modules/core/` (especially `posting_guardrails.py`, `LedgerPoster`, the `money.py` utilities) is **shared infrastructure**. A change there to satisfy one subledger can silently break every other subledger's posting — and every entity's books — at once.

- New subledger behavior goes in the subledger's own module.
- Changes to `app/modules/core/` require the four-eyes review in §6.2 and a test run across **all** subledgers.
- If you feel you must edit a core module, stop and read `ADDENDUM_A_ACCOUNTING_CONTROLS.md` first.

### 3.3 No Business Logic in Routers
FastAPI routers are for HTTP — parse, authorize, route, format. Business logic lives in service classes; posting logic lives in the relevant subledger service and the `LedgerPoster` seam. No SQL in routers, no posting `if/else` in routers.

### 3.4 The Service Layer Owns Business Logic
Every service takes its dependencies via constructor injection and is testable without a live database, a live Supabase connection, or a live Billing service. A posting validator you cannot unit-test is a posting validator you cannot trust.

### 3.5 Database Access is Explicit — and Always Entity-Scoped
Use async SQLAlchemy with explicit loads (`selectinload`/`joinedload`); no lazy loading, no N+1. **Every query that touches entity data includes a `legal_entity_id` scope filter. No exceptions.** A missing scope means one entity sees another entity's financial data. Build a scoped base-query helper so it is physically impossible to forget.

### 3.6 Migrations Are Permanent (Alembic)
Every schema change is an Alembic migration with a working `downgrade()`. Never edit an applied migration; write a new one to correct it. Never run raw SQL against production. Test the downgrade in dev before merge. **No migration merges on a Friday.**

### 3.7 Environment Variables Are the Only Configuration
No hardcoded URLs, keys, thresholds, currency scales, or rounding modes. Every value that differs between environments is an env var. Keep `.env.example` current in the **same PR** that adds a variable. Never commit a real `.env`.

### 3.8 Explicit Disabled State — Never Infer Capability from Absence
Every optional capability (a payable integration, a payroll plugin, a feature phase) has an explicit `disabled` state via env var. An absent env var is a misconfiguration, not an "off" switch. A job that reads a disabled backend raises immediately with a message that tells the developer exactly what to set and why — never a silent wrong default.

### 3.9 Auth — Consume `@truevow/auth-client`, Never Import Clerk Directly
The platform auth standard is Clerk (App 2 "TrueVow-Operators" for this service). The FM frontend consumes the shared `@truevow/auth-client` (`ClerkWrapper`) — it never imports `@clerk/nextjs` directly. The FastAPI backend verifies the Clerk-issued JWT in its auth middleware and normalizes the claims into an `AuthContext(user_id, platform_role, permissions)`. **Every service and job consumes `AuthContext`, never a raw Clerk object or JWT field.** Why: services stay testable (mock `AuthContext`), intent stays readable, and any claim change is isolated to one adapter.

**Platform operators are not firm-scoped.** An operator may access multiple legal entities. Every privileged action (post to a closed period, override SoD, approve a payroll run, adjust a reconciliation) must be audit-logged with `operator_id`, timestamp, and reason — regardless of their role in the platform. There is no "super-admin exemption" from audit.

### 3.10 Observability Is Part of the Feature
Financial Management ships OpenTelemetry + SigNoz (otel) + Sentry. Every posting attempt, every validation failure, every subledger sync, and every reconciliation match emits a span/metric. A finance system you cannot observe in real time is a finance system you cannot explain when the trial balance does not balance at month-end. Metrics must carry `entity_id`, `book_id`, `module`, and `operation` — never transaction amounts, account numbers, or payroll PII. Errors go to the platform Sentry.

### 3.11 Schema First — Add Fields Before You Need Them
If the PRD's data model shows a field a future phase will populate, add it now as a nullable column. One migration line today beats a production migration touching every journal line later.

---

## Part 4 — Financial Integrity & Audit (Zero Tolerance)

### 4.1 The Double-Entry Balance Invariant Is Immovable
Every posted journal entry must balance: `sum(debits) == sum(credits)`, validated with exact Decimal comparison (not floating-point epsilon). The balance check runs once in validation, once in the posting guardrail, and is enforced by the `LedgerPoster` seam. There is no code path that bypasses it. There is no "force" flag that overrides it. Unbalanced entries return a specific error code (`UNBALANCED`) with the exact difference — never a generic 500.

### 4.2 Posted Entries Are Immutable — Reverse, Never Edit
Once a journal entry has `status = 'posted'`, its lines are immutable. The ONLY allowed correction path is: reverse the original entry (generate equal-and-opposite lines posted to the next open period) and create a new corrected entry. Editing posted line amounts DELETE the audit trail. The `reverse()` method on a journal entry must itself produce a journal entry, validate its balance, and post atomically.

### 4.3 Idempotency on Every Money-Write
Every operation that creates, modifies, or moves money — posting a journal entry, recording a payment, executing a payroll run, posting a royalty, adjusting a reconciliation — must be idempotent. Every endpoint that writes money accepts an `Idempotency-Key` header, stores the response keyed by that value, and on replay returns the stored result with HTTP 200 (not a 409 conflict). Internally, every posting operation sets a deterministic `source_key` (e.g. `PAYROLL:run_id:book_id`, `REVREC:schedule_period_id:book_id`) with a unique database constraint — the last line of defense against a double-post.

### 4.4 Row-Level Security on Every Table
Every table that contains entity-scoped data has a `legal_entity_id` column and a Supabase RLS policy. Every query is filtered to the operator's authorized entities. A platform operator who is authorized for UAE must never accidentally see Nevis financial data — and vice versa.

### 4.5 Complete Audit Trail — No Exception
Every approval action (payroll submit/approve/reject, reconciliation adjustment, period close, royalty run) is logged with `operator_id`, `action`, `before_json`, `after_json`, and timestamp. Every posting action is logged with the same detail. Every override of segregation of duties is logged with `operator_id` and `reason`. No write to money tables happens without an audit record. The audit log is append-only.

### 4.6 Multi-Book Accounting (ACCRUAL + CASH)
Every entity operates both ACCRUAL and CASH books. The CASH book is **treasury-driven** — it reflects reality from bank movements and settlement files, not from Billing "payment succeeded" events. The ACCRUAL book recognizes revenue when earned (via deferred revenue schedules) and expenses when incurred (via AP bills). Never assume one book's posting implies the other. The `book_id` is a required dimension on every journal line.

### 4.7 Money Types — Never Float
Every monetary value is stored as `DECIMAL` (or `NUMERIC`) in the database and as Python `Decimal` in code. Never `float`. Never `double`. Never an implicit conversion from a JSON number. Currency codes are stored alongside every monetary field. Rounding uses `HALF_UP` by default, with per-currency precision configuration (USD=2, AED=2, PKR=2). See `app/core/money.py`.

### 4.8 Source Key Everywhere — Traceability is Non-Negotiable
Every journal line carries a `source_key` that traces back to the originating system and object. The `source_object_map` table is the universal lookup: given an external system + object type + external ID, it returns the internal GL entity. This is how the Billing-to-AR sync deduplicates and how the auditor traces a P&L line item back to the source invoice. Never post a journal entry without populating the source map.

### 4.9 Segregation of Duties — Enforced Server-Side
Payroll, reconciliation adjustments, period close, and royalty runs all require different operators for submit vs. approve vs. post. The `sod_validator.py` enforces this server-side; no UI-level-only enforcement. A `FINANCE_ADMIN` may override SoD, but the override is audit-logged with reason.

### 4.10 Secrets Never Touch Git
`fly secrets set` for production, `.env.local` for dev, `.env.example` (placeholders only) in git. If a secret is ever committed: rotate it first, then scrub history, then notify the team.

---

## Part 5 — The Finance Operator Experience (This Is the Product)

### 5.1 Every Number on Screen Is Traced to Its Source
The finance operator must be able to click any number in the P&L, trial balance, or AR aging report and drill down to the underlying journal entries — and from those entries to the source document (invoice, payment, payroll run, royalty run). If a number cannot be traced, the finance operator cannot trust it, and therefore the feature is incomplete.

### 5.2 Errors the Operator Sees Are Actionable
On the finance operator dashboard side, error states are plain English with a next action — never HTTP codes, stack traces, "null", "undefined", "timeout", or JSON. Every error tells the operator: what happened, why, and what to do now. Example: "This period is closed. To post, first re-open the period from Settings > Accounting Periods, then try again. If you need to post into a closed period, contact a Finance Admin."

### 5.3 The GL and Trial Balance Must Reconcile to the Subledger — Always
Every subledger detail report (AR aging, AP aging, payroll register, bank reconciliation) must have a control total that ties to the corresponding GL control account for the same period. If the control total doesn't match, the operator must see both numbers — the subledger total and the GL balance — with a clear reconciliation view showing the differences.

### 5.4 Multi-Currency Must Never Feel Like an Afterthought
Every monetary display shows the currency code. FX rates are stored per posting line, not just per entry. When viewing a cross-entity report (e.g. consolidated P&L), the operator can toggle between functional currency view and reporting currency view. Never silently convert currencies; always show the rate and the date it was effective.

### 5.5 Approval Workflows Are the Default, Not a Setting
Every payroll run, reconciliation adjustment, royalty run, and AP payment batch requires approval before posting. An unapproved object cannot post. The approval flow is always visible in the UI: submitted by, submitted at, pending approval, approved/rejected by, approved/rejected at, reason. If an approval step is missing, the operator won't know what's blocking — and neither will you, at 3am.

---

## Part 6 — Code Review Standards

### 6.1 The PR Description Is Part of the Code
Every PR states: what changed (plain English), why (link to PRD/ADR/spec), how to test it manually (step by step), and any risks. "Fixed the thing" is not mergeable.

### 6.2 Four-Eyes Rule for High-Stakes Code
Explicit second-reviewer sign-off — a comment confirming the specific concern was checked, not just "approved" — is required for any change that:
- touches a **core module** (`app/modules/core/`, `LedgerPoster`, `posting_guardrails.py`, `money.py`),
- modifies **posting validation** or the **balance invariant**,
- modifies **SoD enforcement** or the **approval workflow**,
- modifies **idempotency** or **source_key** generation logic,
- changes **auth/authorization** or entity scoping,
- changes how **payroll PII** or **bank details** are stored or accessed.

### 6.3 Migrations Require Extra Care
Before merge: `alembic upgrade head` and `alembic downgrade -1` both succeed on a fresh DB and on a DB with existing data; the schema matches the PRD data model. No migration merges on a Friday.

### 6.4 No Dead Code
No commented-out code, no unused imports, no TODOs older than a sprint. The only allowed marker is `# AGENT CHOICE: [description] — flagged for review`, to be resolved next sprint.

---

## Part 7 — Deployment Rules

### 7.1 Production Is Sacred
Production is where real finance operators manage real TrueVow money. Pipeline: merge to `main` → auto-deploy to staging → full test suite → manual, signed-off production deploy, logged (who/when/what). No production deploys on Friday afternoon. No production deploy that has not run in staging — **including a real end-to-end posting of at least one journal entry across all subledgers.**

### 7.2 Secrets Never Touch Git
See §4.10. `fly secrets set` is the only path for production credentials.

### 7.3 Rollback Must Be Possible in Under 5 Minutes
Every deploy is rollback-able and tested in staging first. A bad deploy that corrupts the GL is a company-ending event — rollback must be tested and practiced.

---

## Part 8 — The Simplicity Test

Before marking any work complete, run it through these:

1. **Would a developer joining today understand this code in 30 minutes without asking anyone?** If no: simplify or comment until yes.
2. **Would a controller signing a P&L to the board trust the number this code produces?** If no: fix it.
3. **Could this expose entity financial data — bank details, payroll amounts, GL transactions — in a log, URL, error message, or metric?** If yes: fix before merging.
4. **Could a change in this subledger break another subledger's posting?** If yes: move it into the subledger's own module or get four-eyes sign-off on the core module.
5. **If this breaks at 2am on the last day of the month, does the finance operator get a clear, actionable error rather than a silent wrong balance?** If no: add validation, observability, and a user-facing error flow.

---

## Report to the Orchestrator — Mandatory Session Protocol

You are not working alone. This service reports to the TrueVow CTO Orchestrator, whose **only** real-time visibility into your work comes from two channels: your **git state** and your **check-ins**. If you never check in, the orchestrator dashboard shows this service as `NEGLECTED`, the CTO is flying blind, and stalled or half-finished work stays invisible.

A task is not "done" until the check-in is posted. **Intent is not completion.**

**Start of every session:**
```
python ../TrueVow_Shared_Orchestration/orchestrator.py sync-memory
python ../TrueVow_Shared_Orchestration/orchestrator.py scan-services
python ../TrueVow_Shared_Orchestration/orchestrator.py agent-checkin start "FM: <task> | resuming from <state> | goal: <what success looks like>"
```

**During work — record decisions as they happen:**
```
python ../TrueVow_Shared_Orchestration/memory.py remember <category> "<title>" "<content>" --importance N
```

**End of session — write back, then push:**
```
python ../TrueVow_Shared_Orchestration/orchestrator.py agent-checkin done "FM: <accomplished> | outcome: <result> | learned: <insight> | next: <remaining>" --status DONE
python ../TrueVow_Shared_Orchestration/orchestrator.py push-memory
```

**If blocked — raise it immediately, never go silent:**
```
python ../TrueVow_Shared_Orchestration/orchestrator.py agent-checkin blocked "FM: <blocker> | attempted: <what you tried> | need: <what unblocks you>"
```

**RULE 0 — No fabrication.** Never report a build, a test count, or a metric you did not actually produce. If a command did not run green in front of you, it is not green. A stub result is not a real result. Binding platform-wide.

---

## The Final Instruction

You are not building a CRUD app with some ledger tables. You are building the system that TrueVow's finance team — and eventually its auditors, investors, and tax authorities — will trust to represent the company's financial position.

A single unbalanced journal entry means the trial balance doesn't balance, and the finance team cannot close the month. A single edited posted entry means the auditor finds a material weakness and the audit opinion is qualified. A single missing idempotency check means a double-posted payment that the bank won't return and the books can't explain. A single missing audit log entry for a SoD override means the controller cannot prove who did what — and in finance, if it isn't logged, it didn't happen.

The code you write is the difference between a finance team that trusts their system and closes the month in two days, and a finance team that rebuilds their GL in Excel because they can't trust yours.

Write code like the audit depends on it. Because it does.

---

*These instructions apply to every line of code written for Financial Management. They are the operating standard, not guidelines. Any deviation requires explicit justification in the PR description and product-owner sign-off.*

*Last updated: July 2026*
