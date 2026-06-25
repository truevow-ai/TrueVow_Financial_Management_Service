# TrueVow Financial Management — Repo Rules Addendum
**Version:** 1.0
**Date:** 2026-03-06
**Applies to:** This repo only. Overrides structure decisions from global qoder-rules.md where noted.

---

## 1. REPO TYPE

**Monorepo** — Python FastAPI backend + Next.js frontend

---

## 2. TRUTH COMMANDS (EXACT)

### Backend
```bash
alembic upgrade head
python -m pytest tests/ -v
```

### Frontend
```bash
pnpm install
pnpm lint
pnpm build
```

**Package manager rule:** pnpm ONLY (pnpm-lock.yaml present). Never use npm or yarn.

---

## 3. DIRECTORY STRUCTURE CONSTRAINTS

### Backend — New Modules Go Here
```
app/modules/{module_name}/
├── api/
│   └── routes/           # FastAPI route files
├── models/               # SQLAlchemy ORM model files
├── repositories/         # Database query layer files
├── schemas/              # Pydantic request/response schemas
├── services/             # Business logic files
└── integrations/         # External service adapters (if needed)
    ├── {service}_adapter.py        # Abstract interface (ABC)
    └── http_{service}_adapter.py   # HTTP implementation
```

**CRITICAL:** Modules use **directories**, not flat files. Do NOT create `models.py` — create `models/` directory with individual model files.

**DO NOT** create modules anywhere else.
**DO NOT** invent top-level folders.

### Frontend — New Components Go Here
```
frontend/components/{domain}/     # New UI components
frontend/hooks/                   # New custom hooks
frontend/lib/                     # New API client functions
frontend/types/                   # New TypeScript types
```

### Database — Migrations Go Here
```
infra/database/migrations/        # Alembic migration files
```

### Agent Skills Go Here
```
.qoder/agents/{name}-agent/SKILL.md
.qoder/skills/                    # Domain patterns
```

---

## 4. NON-NEGOTIABLES (SECURITY + ACCOUNTING)

### Security
- Every new table MUST have `legal_entity_id` column + RLS policy
- Never bypass JWT auth globally
- Never log PII (names, SSNs, account numbers, bank details) in plain text
- Never expose raw SQL errors to API consumers

### Accounting Invariants
- Every journal entry MUST balance: `sum(debits) == sum(credits)`
- Closed accounting periods are IMMUTABLE — no entries allowed
- All sub-ledger balances MUST reconcile to GL control accounts
- Deferred revenue MUST be recognized monthly — never booked directly to revenue in full
- IC entries MUST be posted atomically on both sides

### Benjamin INTAKE
- All Benjamin vendor costs tagged to `INTAKE-*` cost center
- Usage-based vendors (telephony, STT, TTS) MUST have month-end accruals
- New Benjamin vendors require approval before AP master record creation

---

## 5. AGENT REGISTRY QUICK REFERENCE

| Agent | When to Use |
|-------|-------------|
| orchestrator | Start of any session — read this first |
| search-agent | Before touching any file |
| code-agent | Writing or modifying code |
| gl-agent | Journal entries, chart of accounts, period close |
| ar-agent | Invoices, payments, deferred revenue, billing sync |
| ap-agent | Vendor bills, payments, Benjamin vendor management |
| payroll-agent | Payroll runs, approvals, payments |
| treasury-agent | Bank reconciliation, transfers, FX |
| intercompany-agent | Cross-entity transactions, royalties |
| reporting-agent | Financial statements, trial balance, INTAKE P&L |
| affiliates-agent | Commission tracking and payments |
| benjamin-agent | Benjamin vendor costs, budget vs actuals, INTAKE OpEx |

---

## 6. DO NOT INVENT FOLDERS

These are the ONLY top-level directories:
```
app/          backend application
frontend/     Next.js frontend
infra/        database migrations
tests/        backend tests
scripts/      utility scripts
docs/         documentation
logs/         log files
.qoder/       agent skills and rules
```

If a new directory seems needed, escalate to orchestrator first.

---

## 7. WORKING CACHE LOCATION
- Progress: `docs/01-main/IMPLEMENTATION_PROGRESS.md`
- Session cache: `docs/01-main/WORKING_CACHE.md`
- Checkpoints: `docs/01-main/MILESTONE_{N}_CHECKPOINT.md`
- ADRs: `docs/01-main/adr/ADR_{YYYYMMDD}_{title}.md`

---

**End of Addendum**
