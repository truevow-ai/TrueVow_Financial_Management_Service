# Database Migration Instructions

**Date:** January 25, 2026  
**Status:** Migration File Created

---

## Migration Created

**File:** `database/migrations/versions/001_add_approval_workflow_fields_and_period_close_checklist.py`

**What it does:**
- Creates the `period_close_checklist` table with all required fields
- Creates indexes and unique constraints
- Creates enum types for checklist item codes and statuses

**Note:** Approval workflow fields (submitted_by, submitted_at, approved_by, etc.) are already defined in the models for:
- `accounting_period`
- `payroll_run`
- `reconciliation_adjustment_batch`
- `royalty_calculation`

If these fields don't exist in your database yet, you'll need to run autogenerate to add them.

---

## How to Apply the Migration

### Option 1: Apply Migration Directly (Recommended)

```bash
# Make sure your .env.local has the database URL and JWT_SECRET_KEY
alembic upgrade head
```

This will:
- Connect to your database
- Create the `period_close_checklist` table
- Create the enum types
- Create indexes and constraints

### Option 2: Generate SQL First (Review Before Applying)

```bash
# Generate SQL without executing
alembic upgrade head --sql > migration_001.sql

# Review the SQL file
cat migration_001.sql

# Then apply it manually in your database
```

### Option 3: Check for Missing Approval Fields

If approval fields are missing from existing tables, run:

```bash
# This will detect missing fields and create a new migration
alembic revision --autogenerate -m "Add missing approval workflow fields"

# Review the generated migration
# Then apply it
alembic upgrade head
```

---

## Verification

After applying the migration, verify:

1. **period_close_checklist table exists:**
   ```sql
   SELECT * FROM information_schema.tables 
   WHERE table_name = 'period_close_checklist';
   ```

2. **Enum types created:**
   ```sql
   SELECT typname FROM pg_type 
   WHERE typname IN ('checklistitemcode', 'checklistitemstatus');
   ```

3. **Approval fields exist (if needed):**
   ```sql
   -- Check accounting_period
   SELECT column_name FROM information_schema.columns 
   WHERE table_name = 'accounting_period' 
   AND column_name IN ('submitted_by', 'submitted_at', 'approved_by', 'approved_at', 'decision_reason', 'row_version');
   
   -- Check payroll_run
   SELECT column_name FROM information_schema.columns 
   WHERE table_name = 'payroll_run' 
   AND column_name IN ('submitted_by', 'submitted_at', 'rejected_by', 'rejected_at', 'decision_reason', 'row_version');
   ```

---

## Rollback (If Needed)

If you need to rollback the migration:

```bash
alembic downgrade -1
```

This will:
- Drop the `period_close_checklist` table
- Drop the enum types
- Remove indexes

**Warning:** This will delete all checklist data. Only use if necessary.

---

## Next Steps

1. ✅ Migration file created
2. ⏳ Apply migration to database
3. ⏳ Verify table creation
4. ⏳ Test period close checklist functionality
5. ⏳ Test approval workflows

---

**END OF MIGRATION INSTRUCTIONS**
