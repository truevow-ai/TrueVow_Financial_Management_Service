# Next Steps After Migrations (PowerShell)

**Migrations are at head:** `005_add_idempotency_metadata`  
**Date:** January 27, 2026

---

## 0. All-in-one: dev backend script (recommended)

From **repo root**:

```powershell
.\scripts\dev_backend.ps1
```

This script: loads `.env` / `.env.local`, activates venv, runs `pip install -r requirements.txt`, runs `alembic upgrade head`, then `python -m pytest tests/ -v`. If you use a remote DB (e.g. Supabase), it skips Docker. After it finishes, start the server with:

```powershell
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload
```

---

## 1. Install Python dependencies (if missing)

From repo root with venv activated:

```powershell
pip install -r requirements.txt
```

Or only what you need for run/tests:

```powershell
pip install "uvicorn[standard]" pytest pytest-asyncio
```

---

## 2. Start the backend (verify app + DB)

**PowerShell** (use `;` not `&&`):

```powershell
cd "c:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Financial-Management"
.\venv\Scripts\Activate.ps1
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Ensure `.env.local` has `FINANCIAL_MANAGEMENT_DATABASE_URL` or `FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL`.  
Open http://localhost:8000/docs to confirm the app and DB work.

---

## 3. Run tests

**PowerShell** — use `python -m pytest` (pytest may not be on PATH):

```powershell
python -m pytest tests/ -v
```

---

## 4. Frontend lint / typecheck / build

**PowerShell** — use `;` to chain commands (not `&&`):

```powershell
cd frontend
pnpm install
pnpm lint; pnpm typecheck; pnpm build
```

Or run one at a time:

```powershell
cd frontend
pnpm lint
pnpm typecheck
pnpm build
```

---

## Summary

| Step | Command (PowerShell) |
|------|----------------------|
| Install deps | `pip install -r requirements.txt` |
| Start backend | `python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000` |
| Run tests | `python -m pytest tests/ -v` |
| Frontend | `cd frontend; pnpm lint; pnpm typecheck; pnpm build` |
