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
UNVERIFIED — truth commands not yet executed

## Active Modules
- app/ (backend)
- database/ (migrations)
- tests/
- frontend/

## Known Failing Commands
None yet (not run)

## Next Single Action
Run: alembic upgrade head > logs/alembic.log 2>&1