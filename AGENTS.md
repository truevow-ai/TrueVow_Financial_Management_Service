# TrueVow Financial Management — Agent Rules

**Single source of truth for how agents work in this repo.** Merged from the
former `.qoder/rules/` (qoder-rules.md + repo-addendum.md) and `.clinerules/`
(cursor-rules.md, architectural-decision-process.md, start-here). Domain
patterns and per-module playbooks live as skills under `.opencode/skills/`.

This file applies to ALL agents, ALL modules. A repo-specific rule here
overrides the generic version of the same rule.

---

## 1. Project

TrueVow Financial Management is the back-office accounting + financial
operations system for TrueVow (legal AI services: INTAKE, DRAFT, VERIFY,
SETTLE). It is a **monorepo**: Python FastAPI backend + Next.js frontend. It
manages TrueVow's own finances, Benjamin INTAKE operational costs, and client
billing via the AR module. Multi-tenant by legal entity.

---

## 2. Repo type & truth commands (EXACT)

**Monorepo** — Python backend + Next.js frontend.

### Backend (Python)
```bash
alembic upgrade head
python -m pytest tests/ -v
ruff check .        # if runnable
mypy .              # if runnable
```

### Frontend (Next.js)
```bash
pnpm install
pnpm lint
pnpm typecheck
pnpm build
```

**Package-manager rule:** pnpm ONLY (`frontend/pnpm-lock.yaml` present). Never
use npm or yarn. No mixing in one verification run.

A change is only **DONE** when its truth commands have actually executed and
their output was captured (pasted or written to `logs/*.log`).

---

## 3. Status words (use ONLY these three)

- **DONE** — truth commands executed AND finished; raw outputs captured; any
  runtime/API behavior claim backed by real curl output or a passing
  integration test. If a push was requested+granted: commits exist and push
  output captured.
- **UNVERIFIED** — code written but truth commands not run / output not
  captured, OR tests/build still failing.
- **BLOCKED** — a specific named prerequisite prevents execution (list the
  exact missing item + where it fails). "Environmental" is not accepted without
  a pinpointed stall point and captured evidence.

**Forbidden wording unless status == DONE:** "complete", "finished", "ready",
"production-ready", "shippable", "fully verified". Otherwise say "Implemented"
or "Code written" and keep status UNVERIFIED/BLOCKED.

---

## 4. Before you start (read order)

1. `docs/00-main/WORKING_CACHE.md` — session handoff cache (current status,
   truth commands, known-failing commands, next single action).
2. `docs/00-main/IMPLEMENTATION_PROGRESS.md` — progress tracker.
3. Latest `docs/00-main/MILESTONE_*_CHECKPOINT.md` if starting a milestone.
4. This file + the relevant `.opencode/skills/*` for the module/domain.

**Search-first:** run grep/glob/search before opening files. Open only files
you will modify or that directly affect the current task. Do not re-read large
files a checkpoint already summarizes. Prefer referencing a checkpoint/ADR over
re-explaining architecture.

---

## 5. Directory structure (DO NOT INVENT FOLDERS)

Only these top-level directories exist:
```
app/        backend application
frontend/   Next.js frontend
infra/      database migrations (Alembic) under infra/database/migrations/
tests/      backend tests
scripts/    utility scripts
docs/        documentation
logs/        log files
.opencode/  agent skills + config
```
If a new top-level directory seems needed, escalate before creating it.

### Backend modules (directories, NOT flat files)
```
app/modules/{module}/
├── api/routes/      # FastAPI route files
├── models/          # SQLAlchemy ORM model files
├── repositories/    # DB query layer files
├── schemas/         # Pydantic request/response schemas
├── services/        # Business logic files
└── integrations/    # External adapters: {svc}_adapter.py (ABC) + http_{svc}_adapter.py
```
**Never** create `models.py`/`service.py` — use the directory + per-file form.
**Never** create modules outside `app/modules/`.

### Frontend
```
frontend/components/{domain}/   frontend/hooks/   frontend/lib/   frontend/types/
```

Follow the structure already present in the tree; do not impose a "standard"
layout. See `.opencode/skills/fintech-patterns/SKILL.md` for module patterns.

---

## 6. Non-negotiables (accounting + security)

### Accounting invariants (zero tolerance)
- Every posted journal entry MUST balance: `sum(debits) == sum(credits)`.
- Posted entries are **immutable** — correct only by reversal, never edit.
- Closed/locked accounting periods are immutable — no entries allowed.
- Multi-entity + multi-book: ACCRUAL and CASH books are first-class (no toggle
  hacks). CASH book is **Treasury-driven**, not Billing-driven.
- All sub-ledger balances MUST reconcile to GL control accounts.
- Deferred revenue is recognized monthly — never booked to revenue in full.
- Intercompany entries post atomically on both sides.
- Subledgers post into GL via the `LedgerPoster` seam
  (`get_ledger_poster(session)`), not by importing `JournalEntryService`.

### Security
- Every new table MUST have a `legal_entity_id` column + RLS policy.
- All write operations support an `Idempotency-Key`; posting sets a
  deterministic `source_key` for double-entry safety.
- Never bypass JWT auth globally.
- Never expose raw SQL errors to API consumers.
- Never log PII (names, SSNs, account/bank numbers) in plain text.

### Benjamin INTAKE
- All Benjamin vendor costs tagged to an `INTAKE-*` cost center.
- Usage-based vendors (telephony, STT, TTS) require month-end accruals.
- New Benjamin vendors require approval before AP master record creation.

When in doubt, choose the option that preserves double-entry integrity and
immutable postings; if still unsure, ask before coding.

---

## 7. Verification gates

- **Truth commands required for DONE** (Section 2). If lint/typecheck are not
  configured/runnable, status stays UNVERIFIED unless the user waives them.
- **Runtime behavior claims** (e.g. "409 on stale row_version", idempotency
  replay) require either 2 real curl request/response captures OR 1 passing
  integration test with raw output. Unit tests alone are not enough.
- **First-failure fix loop:** on a failing truth command, paste full output
  (or log path + failing section), fix ONLY the first failure, re-run the same
  command, repeat until green. Never fix multiple unrelated failures before
  re-running.
- **No hide-failures fixes** (forbidden unless explicitly approved AND status
  stays UNVERIFIED): `typescript.ignoreBuildErrors`, commenting out tests,
  skipping migrations, bypassing auth, removing checks without replacement, or
  stubbing real logic and calling it done. Label any temporary STUB clearly.
- **No "environment is broken" claims without proof:** a minimal repro outside
  the repo, a captured stall point/stack trace, and an attempted approved
  workaround. Otherwise status stays UNVERIFIED, not BLOCKED.
- **Output capture:** write full command output to `logs/<name>.log`; paste
  only the failing section (~30 lines) + the log path. Don't spam huge logs.
- **Hang protocol:** if no new output for >60s, re-run with timing + log
  capture and isolate the exact stall (binary-search imports for Python;
  single-test for Jest) before labeling anything environmental.

---

## 8. Safety (no damage)

- **No-delete policy:** ask before deleting ANY file/folder —
  `DELETE REQUEST: <path> — type 'yes' to proceed`. Never quiet
  `rm -f` / `Remove-Item -Force` / `shutil.rmtree`. (Exception: temp files this
  session created, documented in the checkpoint.)
- **Restructure protocol:** `git add -A` → stash backup → COPY (don't move) to
  new location → verify content (line count/checksum) → ask before deleting
  originals → commit with a clear message → update checkpoint.
- Never "clean up"/"organize"/delete logs or draft docs without explicit
  approval. Preserve content during refactors.

---

## 9. Checkpoints & working cache

- Update `docs/00-main/WORKING_CACHE.md` (keep it small, <150 lines) at least
  every 60 min of work or at task end: repo type, truth commands, current
  status + why, modules touched, known-failing commands + last error, next
  single action.
- Update `docs/00-main/IMPLEMENTATION_PROGRESS.md` incrementally (current
  milestone, what changed, next command).
- After a milestone: create `docs/00-main/MILESTONE_{N}_CHECKPOINT.md`.
- For non-trivial architectural decisions: create
  `docs/00-main/adr/ADR_{YYYYMMDD}_{title}.md`.

---

## 10. Architectural decision process

Before any architectural decision, search the authoritative TrueVow docs first
(PRD / system / technical documentation), reading only the relevant sections —
never whole documents for routine checks. Align decisions with those sources
and record them in an ADR.

**STOP and ask the user** on: conflicting information (PRD vs codebase),
missing information (no search results), unclear architecture, or breaking
changes to deployed architecture.

Architecture principles: microservices isolation (separate databases, API-only
communication, no cross-DB access); security boundaries; async-first
SQLAlchemy; repository pattern for data access.

---

## 11. Pre-implementation checklist (every new feature)

1. Read the relevant docs/checkpoints first.
2. Search the existing codebase for similar implementations + existing
   utilities (don't duplicate auth/RBAC, encryption, audit logging).
3. Review existing patterns (API routes, components, models, migrations).
4. Confirm naming conventions, multi-tenancy, and security practices.
5. Ask if uncertain — never assume.

---

## 12. Git hygiene

- **No push without explicit permission** ("push now"). Prepare commits
  locally otherwise.
- Conventional, concrete commit messages: `feat:`, `fix:`, `refactor:`,
  `chore:` — no vague "update" commits.
- If push was requested+granted, DONE requires captured output of:
  `git status`, `git log -1 --oneline`, `git remote -v`, `git push`.

---

## 13. Agent skills (registry)

Specialized playbooks load via the `skill` tool from `.opencode/skills/`:

| Skill | When to use |
|-------|-------------|
| `orchestrator` | Start of a session — architecture + routing + skill maintenance |
| `search-agent` | Find code / trace dependencies before any edit |
| `code-agent` | Writing or modifying code |
| `gl-agent` | Journal entries, chart of accounts, periods, GL reconciliation |
| `ar-agent` | Invoices, payments, deferred revenue, billing sync |
| `ap-agent` | Vendor bills, payments, Benjamin vendor management |
| `payroll-agent` | Payroll runs, approvals, payment batches |
| `treasury-agent` | Bank accounts, transactions, FX, settlements, reconciliation |
| `intercompany-agent` | Cross-entity transactions, royalties, IC reconciliation |
| `reporting-agent` | Financial statements, trial balance, aging, cash flow |
| `affiliates-agent` | Commission tracking and payments |
| `benjamin-agent` | Benjamin INTAKE vendor costs, budget vs actuals, INTAKE OpEx |
| `fintech-patterns` | TrueVow FM domain patterns (RLS, double-entry, adapters) |

---

## 14. End-of-message completion checklist

When a message is "final" for a task, include:
```
STATUS: DONE | UNVERIFIED | BLOCKED
COMMANDS EXECUTED: <list>
RAW OUTPUTS CAPTURED: YES (pasted) | YES (logs/<file>.log) | NO
REMAINING FAILURES: none | <list>
NEXT ACTION: <single next command or task>
```
