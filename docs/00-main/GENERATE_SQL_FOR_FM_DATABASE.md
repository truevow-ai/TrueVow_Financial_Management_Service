# Generate SQL for Financial Management Database

**Date:** January 24, 2026

---

## You're Absolutely Right!

The Financial Management database (`FINANCIAL_MANAGEMENT_DATABASE_URL`) is separate from Internal Ops, and you need SQL files to run directly in that database.

---

## Solution: Use Alembic to Generate SQL

Alembic can generate SQL without executing it, which gives you the SQL file to run in your Financial Management database.

### Step 1: Ensure Configuration

Make sure your `.env.local` has:
```bash
FINANCIAL_MANAGEMENT_DATABASE_URL=postgresql://postgres:Intakely%40786@db.ififhzrbhadmtedyvzhb.supabase.co:5432/postgres
JWT_SECRET_KEY=your-secret-key-here
```

### Step 2: Generate Migration (Creates Migration File)

```bash
alembic revision --autogenerate -m "Create initial schema for Financial Management"
```

This creates a migration file in `database/migrations/versions/`

### Step 3: Generate SQL from Migration (Without Executing)

```bash
alembic upgrade head --sql > database/fm_schema.sql
```

This:
- ✅ Generates SQL from the migration
- ✅ Outputs to `database/fm_schema.sql`
- ✅ **Does NOT execute** (safe to review first)

### Step 4: Review and Run SQL

1. **Review** `database/fm_schema.sql`
2. **Run in Supabase SQL Editor**:
   - Go to your Financial Management project
   - Open SQL Editor
   - Copy/paste the SQL file content
   - Execute

OR

3. **Run via psql**:
   ```bash
   psql "postgresql://postgres:Intakely%40786@db.ififhzrbhadmtedyvzhb.supabase.co:5432/postgres" -f database/fm_schema.sql
   ```

---

## Alternative: Direct Migration Execution

If you prefer to let Alembic execute directly:

```bash
# This will connect to FINANCIAL_MANAGEMENT_DATABASE_URL and create tables
alembic upgrade head
```

---

## Which Database Will Be Used?

The configuration now uses `FINANCIAL_MANAGEMENT_DATABASE_URL` from `.env.local`, so:

- ✅ **Migrations target**: Financial Management database
- ✅ **NOT**: Internal Ops database
- ✅ **Correct database**: `db.ififhzrbhadmtedyvzhb.supabase.co`

---

## Summary

1. ✅ Configuration updated to use `FINANCIAL_MANAGEMENT_DATABASE_URL`
2. ⏳ Generate migration: `alembic revision --autogenerate -m "Create initial schema"`
3. ⏳ Generate SQL: `alembic upgrade head --sql > database/fm_schema.sql`
4. ⏳ Review SQL file
5. ⏳ Run SQL in Financial Management database (Supabase SQL Editor)

---

**The SQL will be generated for the Financial Management database, not Internal Ops!**
