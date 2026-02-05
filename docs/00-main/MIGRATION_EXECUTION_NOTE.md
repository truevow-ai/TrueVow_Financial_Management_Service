# Migration Execution Note

**Issue:** If you're seeing an error about the docstring being executed as SQL, you're likely trying to run the migration file directly as SQL instead of through Alembic.

## Correct Way to Run Migration

```bash
# Use Alembic to run the migration
alembic upgrade head
```

**DO NOT:**
- Copy/paste the migration file content into a SQL client
- Try to execute the Python file as SQL
- Run the migration file directly

## Why This Happens

The migration file is a **Python file** that Alembic executes. It contains:
- Python code (imports, functions)
- SQL statements wrapped in `op.execute()` calls
- Docstrings (Python comments)

If you try to run it as SQL, PostgreSQL will try to execute the Python code and docstrings as SQL, causing syntax errors.

## How Alembic Works

1. Alembic reads the Python migration file
2. Executes the `upgrade()` function
3. Each `op.execute()` call sends SQL to the database
4. The docstring and Python code are never sent to the database

## If You Need Raw SQL

If you need to see the SQL that will be executed:

```bash
# Generate SQL without executing
alembic upgrade head --sql > migration_002.sql

# Review the SQL file
cat migration_002.sql

# Then apply it manually if needed (not recommended - use Alembic)
```

## Verification

After running `alembic upgrade head`, verify the migration was applied:

```sql
-- Check Alembic version table
SELECT * FROM alembic_version;

-- Should show: 002_idempotency_source_key

-- Verify new columns exist
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'journal_entry' 
AND column_name IN ('legal_entity_id', 'source_key');

-- Verify idempotency_keys table structure
\d idempotency_keys
```
