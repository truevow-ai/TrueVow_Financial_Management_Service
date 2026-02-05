# SQL Schema Idempotent Fix

**Date:** January 24, 2026

---

## Issue

When running the SQL schema file in Supabase, you encountered:
```
ERROR: 42710: type "book_type" already exists
```

This happened because the SQL file was trying to create ENUM types and tables that already existed in the database.

---

## Solution

Updated the SQL file to be **idempotent** (can be run multiple times safely):

### 1. ✅ ENUM Types
Changed from:
```sql
CREATE TYPE book_type AS ENUM ('ACCRUAL', 'CASH');
```

To:
```sql
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'book_type') THEN
        CREATE TYPE book_type AS ENUM ('ACCRUAL', 'CASH');
    END IF;
END $$;
```

**Applied to all 15 ENUM types:**
- book_type
- period_status
- account_type
- journal_entry_status
- invoice_status
- payment_status
- schedule_status
- transaction_type
- transfer_type
- reconciliation_status
- payroll_run_status
- component_type
- pay_frequency
- pay_day_rule
- employee_type

### 2. ✅ Tables
Changed from:
```sql
CREATE TABLE legal_entity (
```

To:
```sql
CREATE TABLE IF NOT EXISTS legal_entity (
```

**Applied to all 60+ tables.**

### 3. ✅ Indexes
Changed from:
```sql
CREATE INDEX idx_legal_entity_code ON legal_entity(code);
```

To:
```sql
CREATE INDEX IF NOT EXISTS idx_legal_entity_code ON legal_entity(code);
```

**Applied to all indexes.**

---

## Result

The SQL file `database/fm_schema.sql` is now **fully idempotent**:
- ✅ Can be run multiple times without errors
- ✅ Won't fail if types/tables/indexes already exist
- ✅ Safe to re-run after partial failures
- ✅ Perfect for Supabase SQL editor

---

## Usage

Simply copy and paste the entire `database/fm_schema.sql` file into your Supabase SQL Editor and run it. It will:
1. Create all ENUM types (if they don't exist)
2. Create all tables (if they don't exist)
3. Create all indexes (if they don't exist)
4. Skip anything that already exists

**No more errors!** 🎉
