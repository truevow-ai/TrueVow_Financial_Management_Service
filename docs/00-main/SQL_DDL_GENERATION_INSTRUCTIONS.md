# SQL DDL Generation Instructions

**Date:** January 24, 2026

---

## Overview

You're absolutely right! Since the Financial Management database already exists separately, you should have SQL DDL files to run directly in that database instead of using Alembic migrations.

---

## Two Options

### Option 1: Generate SQL DDL File (Recommended for Direct Execution)

1. **Run the DDL generator script**:
   ```bash
   python scripts/generate_sql_ddl.py
   ```

2. **This creates**: `database/schema.sql` with all CREATE TABLE statements

3. **Run in your Financial Management database**:
   - **Via Supabase SQL Editor**: Copy and paste the SQL file content
   - **Via psql**: `psql <your-connection-string> -f database/schema.sql`

### Option 2: Use Alembic Migrations (For Version Control)

If you prefer version-controlled migrations:

1. **Generate migration**:
   ```bash
   alembic revision --autogenerate -m "Create initial schema"
   ```

2. **Apply to Financial Management database**:
   ```bash
   alembic upgrade head
   ```
   (This will use `FINANCIAL_MANAGEMENT_DATABASE_URL` from `.env.local`)

---

## Database Connection

Your Financial Management database is configured in `.env.local`:
```
FINANCIAL_MANAGEMENT_DATABASE_URL=postgresql://postgres:Intakely%40786@db.ififhzrbhadmtedyvzhb.supabase.co:5432/postgres
```

**This is the database where the schema should be created.**

---

## Next Steps

1. ✅ Configuration updated to use `FINANCIAL_MANAGEMENT_DATABASE_URL`
2. ⏳ Generate SQL DDL: `python scripts/generate_sql_ddl.py`
3. ⏳ Review `database/schema.sql`
4. ⏳ Run SQL in Financial Management database (Supabase SQL Editor or psql)
5. ⏳ Verify tables created

---

## Why SQL DDL Instead of Migrations?

- ✅ **Direct execution** in Supabase SQL Editor
- ✅ **No Python dependencies** needed
- ✅ **Easier to review** before execution
- ✅ **Can be version controlled** as SQL files
- ✅ **Works with any PostgreSQL client**

---

**Status:** Ready to generate SQL DDL for Financial Management database
