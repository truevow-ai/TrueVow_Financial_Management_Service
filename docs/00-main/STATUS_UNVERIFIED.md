# Module Status: UNVERIFIED

**Date:** January 27, 2026  
**Status:** ⚠️ **UNVERIFIED** - Code written, not system verified

---

## What Is Complete (Code Level)

✅ **Row Version 409 Logic:**
- All 17 endpoints now use `check_row_version()` helper (standardized)
- All 4 defects fixed
- All schemas include `row_version: int`
- All routes pass `row_version=request.row_version`
- All services validate using `check_row_version()` helper

✅ **Dev Setup Scripts:**
- `.env.example` created
- `scripts/dev_backend.ps1` / `.sh` created
- `scripts/dev_frontend.ps1` / `.sh` created
- `README_DEV_SETUP.md` created
- `scripts/audit_row_version.py` created

---

## What Is NOT Complete (System Verification)

❌ **Migrations:** `alembic upgrade head` - NOT RUN  
❌ **Backend Tests:** `pytest tests/ -v` - NOT RUN  
❌ **Frontend Build:** `pnpm lint && pnpm typecheck && pnpm build` - NOT RUN  
❌ **Runtime Tests:** Stale row_version returns 409 - NOT VERIFIED

**Until these commands are executed and pass, the module is UNVERIFIED.**

---

## Refactoring Complete: All Use check_row_version() Helper

**Changed:** All 14 inline checks refactored to use `check_row_version()` helper

**Files Updated:**
1. `app/modules/payroll/services/payroll_approval_service.py` - 3 methods
2. `app/modules/payroll/services/payroll_run_service.py` - 1 method
3. `app/modules/ap/services/ap_bill_approval_service.py` - 2 methods
4. `app/modules/ap/services/ap_bill_posting_service.py` - 1 method
5. `app/modules/ap/api/routes/ap_bill_routes.py` - 1 route handler
6. `app/modules/general_ledger/services/reconciliation_approval_service.py` - 3 methods
7. `app/modules/general_ledger/services/period_close_approval_service.py` - 2 methods
8. `app/modules/intercompany/services/royalty_approval_service.py` - 2 methods

**Result:** All 17 endpoints now use `check_row_version()` helper (consistent pattern)

---

## Verification Runbook

### Step 1: Backend Setup

```bash
# From repo root
cp .env.example .env
# Edit .env and set:
# - DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/fm_db
# - JWT_SECRET_KEY=your-secret-key-here

# Windows
.\scripts\dev_backend.ps1

# Linux/Mac
./scripts/dev_backend.sh
```

**Expected:** Script creates venv, installs deps, starts PostgreSQL, runs migrations, runs tests

---

### Step 2: Frontend Setup

```bash
# Windows
.\scripts\dev_frontend.ps1

# Linux/Mac
./scripts/dev_frontend.sh
```

**Expected:** Script installs dependencies, runs lint, typecheck, and build

---

### Step 3: Manual Verification Commands

**Run these three commands and paste raw outputs:**

```bash
# 1. Migrations
alembic upgrade head

# 2. Backend tests
pytest tests/ -v

# 3. Frontend build
pnpm lint && pnpm typecheck && pnpm build
```

**If any command fails, the module is NOT complete.**

---

### Step 4: Runtime Verification

**Requires:**
- Running server: `uvicorn app.main:app --reload`
- Database with test data
- Authentication token

**Test 1: AP Bill Approve with Stale row_version**
```bash
# Create bill, get row_version=1
# Submit for approval (row_version becomes 2)
# Try to approve with row_version=1
# Expected: 409 Conflict
```

**Test 2: Royalty Approve with Stale row_version**
```bash
# Create royalty, get row_version=1
# Submit for approval (row_version becomes 2)
# Try to approve with row_version=1
# Expected: 409 Conflict
```

**See:** `docs/01-main/RUNTIME_VERIFICATION_PLAN.md` for detailed curl commands

---

## Current Status

**Code:** ✅ Complete (all 17 endpoints use `check_row_version()` helper)  
**System:** ❌ UNVERIFIED (no raw command outputs)

**To Mark Complete:**
1. Run verification commands (Step 3)
2. Paste raw outputs (even if they fail)
3. Fix any failures
4. Run runtime tests (Step 4)
5. Verify 409 responses

**Until then:** Status remains **UNVERIFIED**

---

## Anti-Lie Rule

**The agent is NOT allowed to say "complete" unless:**
- Raw command outputs are pasted
- All three commands pass (`alembic`, `pytest`, `pnpm build`)
- Runtime tests show 409 responses

**If commands cannot run, status must be:**
- **UNVERIFIED**
- With exact runbook provided
