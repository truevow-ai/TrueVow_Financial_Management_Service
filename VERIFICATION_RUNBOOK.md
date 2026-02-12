# Verification Runbook

**Date:** January 27, 2026  
**Purpose:** Run verification commands for source key updates

---

## Git setup (run from project root)

If `git status` says **fatal: not a git repository**, run these from the **project root** (the folder that contains `app/`, `frontend/`, `alembic.ini`), **not** from `frontend/`:

```powershell
cd C:\Users\yasha\OneDrive\Documents\TrueVow\Cursor\TrueVow-Financial-Management
git init
git remote add origin https://github.com/truevow-ai/Financial_Management_Service.git
git remote -v
```

Then stage and commit:

```powershell
git add -A
git status
git commit -m "wip: verification pipeline prep (lint/build/typecheck/test fixes)"
```

**Note:** If you get "Permission denied" or "unable to unlink .git/config.lock", close other apps (OneDrive, other Cursor windows) that might be locking the folder, or run the same commands in an **external** terminal (e.g. Windows Terminal) from the same path.

---

## Prerequisites

### Environment Variables Required

Create `.env` file in project root with:

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/fm_db

# JWT
JWT_SECRET_KEY=your-secret-key-here-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30

# Optional
BILLING_SERVICE_URL=http://localhost:8001
TREASURY_SERVICE_URL=http://localhost:8002
```

### Python Dependencies

```bash
pip install -r requirements.txt
```

### Node Dependencies

```bash
cd frontend
pnpm install
```

---

## Verification Commands

### 1. Migration Chain Verification

```bash
# Check migration chain
python -m alembic heads
python -m alembic history --verbose

# Run migrations (requires DATABASE_URL)
python -m alembic upgrade head
```

**Expected Output:**
- Single head: `005_add_idempotency_metadata`
- Clean linear chain: `001` → `002` → `003` → `004` → `005`
- No errors on `upgrade head`

---

### 2. Backend Tests

```bash
# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/test_idempotency.py -v
pytest tests/test_source_keys.py -v
```

**Expected:** All tests pass (or skip if DB not available)

---

### 3. Frontend Build

```bash
cd frontend

# Lint
pnpm lint

# Type check
pnpm typecheck

# Build
pnpm build
```

**Expected:** No errors, build succeeds

---

### 4. Code Compilation Check

```bash
# Check Python syntax
python -m py_compile app/**/*.py

# Or use mypy if configured
mypy app/
```

**Expected:** No syntax errors

---

## What Was Changed

### Source Key Formats Updated

1. **Billing Sync:** `BILLING:SYNC:{entity_id}:{sync_batch_id}` (batch-based)
2. **Treasury Sync:** `TREASURY:SYNC:{entity_id}:{sync_batch_id}` (batch-based)
3. **Settlement Create:** `SETTLEMENT:CREATE:{provider}:{external_settlement_id}`
4. **AR Invoice Post:** `AR_INVOICE:POST:{external_invoice_id}` or `AR_INVOICE:POST:INTERNAL:{invoice_id}`

### Database Migrations

- `003_add_billing_sync_batch.py` - Creates `billing_sync_batch` table
- `004_fix_settlement_uniqueness.py` - Composite unique index on `(source, external_settlement_id)`
- `005_add_idempotency_metadata.py` - Adds `metadata_json` to `idempotency_keys`

### Code Changes

- `app/modules/ar/api/routes/billing_sync_routes.py` - Batch creation + metadata
- `app/modules/general_ledger/api/routes/treasury_sync_routes.py` - Batch creation + metadata
- `app/core/idempotency.py` - Metadata support
- `app/modules/core/models/idempotency_model.py` - `metadata_json` column
- `app/modules/general_ledger/services/cash_book_posting_service.py` - Settlement source_key
- `app/modules/ar/services/ar_posting_service.py` - AR invoice source_key standardization

### Row Version Standardization

All approval endpoints now use `check_row_version()` helper (already standardized).

---

## Verification Checklist

- [ ] Migration chain is clean (single head)
- [ ] Migrations run without errors
- [ ] All Python files compile
- [ ] Tests pass (or skip gracefully)
- [ ] Frontend builds successfully
- [ ] No linter errors

---

**Status:** Ready for verification (requires environment setup)
