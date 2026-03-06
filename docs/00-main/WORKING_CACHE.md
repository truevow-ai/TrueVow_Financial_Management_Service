# WORKING CACHE - TrueVow Financial Management

## Repo Type
Monorepo (Python backend + Next.js frontend)
- Python indicators: requirements.txt, alembic.ini, tests/
- Node/Next indicators: frontend/package.json, frontend/pnpm-lock.yaml

## Truth Commands for THIS Repo
### Backend (Python)
```bash
alembic upgrade head
python -m pytest tests/ -v
ruff check .
mypy .
```

### Frontend (Next.js)
```bash
cd frontend
pnpm install
pnpm lint
pnpm typecheck
pnpm build
```

## Status Word Policy
Use ONLY: DONE / UNVERIFIED / BLOCKED

## No-Delete Policy
Must ask before deleting any file/folder:
"DELETE REQUEST: <path> — type 'yes' to proceed"

## First-Failure Fix Loop
1) Fix ONLY the first failure
2) Re-run the same command
3) Repeat until green

## Current Status
DONE — Row-level audit trigger deployed (migration 006)

## Recent Changes (2026-03-02)
- Phase 1 DEPLOYED: RLS policies (61 tables, 92 policies)
- Phase 2 DEPLOYED: Immutability triggers (10 triggers)
- Phase 3 DEPLOYED: Business constraints (86 check constraints)
- Connection pooler bypassed Windows firewall issues
- **Migration 006 DEPLOYED: row_audit_log table + fn_row_audit_log() trigger**
  - 47/53 tables covered (6 treasury tables don't exist in DB yet — pre-existing gap)
  - 141 trigger event rows confirmed (47 tables × 3 ops)
  - audit_context_middleware injects user_id/role/correlation_id as GUCs
  - get_db_session() sets SET LOCAL app.current_user_id/role/correlation_id

## Active Modules
- app/ (backend)
- database/ (migrations + security SQL)
- tests/
- frontend/

## Known Failing Commands
- Direct psql connection blocked (DNS resolution failure)
- Workaround: Use connection pooler (aws-1-us-east-1.pooler.supabase.com)
- Treasury tables (bank_account, bank_transaction, settlement, fx_conversion, transfer, sync_cursor) not in DB yet — pre-existing gap

## Next Single Action
When treasury tables are created, re-run database/row_audit_triggers.sql to attach their triggers (idempotent).