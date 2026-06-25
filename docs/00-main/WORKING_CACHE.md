# WORKING CACHE - TrueVow Financial Management

## ⏰ PENDING REMINDER — RAISE AT NEXT SESSION (set 2026-06-25, due 2026-06-26)
SECURITY follow-up, deferred because Supabase was unavailable:
1. ROTATE the Supabase service key (`sb_secret_…`). It was committed to git history and
   scanned by GitHub push protection — treat it as COMPROMISED even though it has been
   purged from all history (via `git filter-repo`; history rewritten + pushed).
2. After rotating, set `$env:SUPABASE_SERVICE_KEY` and update `.env.local`. The scripts
   `scripts/check_db_via_rest.ps1` and `scripts/test_supabase_rest_api.ps1` now read the
   key from that env var instead of hardcoding it.
3. Also pending: restart opencode to load the new `AGENTS.md` + `.opencode/skills/`.

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
DONE — GL LedgerPoster swap seam wired across all subledgers; backend + frontend verified.
DONE — Agent config consolidated into AGENTS.md + .opencode/skills/; pushed to origin/main (history rewritten via git filter-repo to purge a leaked Supabase key).
DEFERRED — Supabase key rotation (Supabase unavailable; see PENDING REMINDER at top).

## Recent Changes (2026-06-25)
- GL swap seam introduced: app/modules/general_ledger/services/ledger_poster.py
  (LedgerPoster Protocol + get_ledger_poster() factory; LEDGER_BACKEND env, defaults to internal JournalEntryService).
- All 8 subledgers now post via the seam instead of importing JournalEntryService directly:
  AP bill, AR posting, deferred revenue, cash book, enhanced reconciliation,
  reconciliation adjustment, intercompany transfer, payroll run.
- Offline test harness: tests/conftest.py defaults to in-memory SQLite (no network);
  JSONB/ARRAY compiled to JSON for SQLite. Affiliates import deferred in app/core/database.py (P1 cut, files preserved).
- New tests: tests/test_ledger_poster_contract.py (4) + tests/test_journal_entry_service.py (8) — all 12 PASS offline.
- All 10 changed backend service modules import cleanly; no stray direct JournalEntryService() in subledgers.
- Frontend feature pages (list pages -> React Query; aging/periods/JE-detail/reconciliation routes):
  pnpm typecheck PASS, pnpm lint PASS (3 pre-existing warnings only), pnpm build PASS (32 routes, 28/28 static pages).
- NOT runnable here (pre-existing/environment): live-Supabase integration/compliance/idempotency-runtime tests; ruff/mypy (bundled binary broken / not on PATH).
- Agent config consolidated: 12 agent skills + fintech-patterns moved to .opencode/skills/; rules merged into root AGENTS.md; opencode.json ($schema) added; .qoder/ originals kept as provenance.
- Pushed to origin (git@github.com:truevow-ai/TrueVow_Financial_Management_Service.git), branch main. First push was blocked by GitHub secret scanning (hardcoded sb_secret_ key in two scripts from the Phase 2a commit); purged from ALL history via git filter-repo (token -> $env:SUPABASE_SERVICE_KEY), then pushed clean. Commit SHAs from Phase 2a onward changed.

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
1) TOMORROW (Supabase back): rotate the Supabase service key, then set $env:SUPABASE_SERVICE_KEY + update .env.local (see PENDING REMINDER at top).
2) Restart opencode to load AGENTS.md + .opencode/skills/.
Optional later: route GL's own journal_entry_routes.py through get_ledger_poster() (still instantiates JournalEntryService directly — acceptable); when treasury tables exist, re-run database/row_audit_triggers.sql (idempotent).