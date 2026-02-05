# Migration and Test Summary

**Date:** January 25, 2026  
**Status:** ✅ Migrations Created | ✅ Minimum Tests Created

---

## Database Migrations

### Migration File
**File:** `database/migrations/versions/002_add_idempotency_and_source_key_safety.py`  
**Revision ID:** `002_idempotency_source_key`  
**Depends on:** `001_approval_workflow`

### What It Does

#### Part A: journal_entry Table Changes

1. ✅ **Adds `legal_entity_id` column** (UUID, FK to legal_entity)
   - Initially nullable for backfill
   - Backfilled from `book.legal_entity_id`
   - Made NOT NULL after backfill

2. ✅ **Adds `source_key` column** (VARCHAR(255), nullable)
   - Backfilled for existing posted entries: `JE:POST:{entry_id}`
   - Allows NULL for draft entries

3. ✅ **Adds unique constraint** (partial index)
   ```sql
   CREATE UNIQUE INDEX uq_journal_entry_source_key 
   ON journal_entry(legal_entity_id, book_id, source_key)
   WHERE source_key IS NOT NULL
   ```
   - Only enforces uniqueness when `source_key IS NOT NULL`
   - Allows multiple draft entries (source_key = NULL)

4. ✅ **Adds indexes for performance**
   - `ix_journal_entry_legal_entity_id`
   - `ix_journal_entry_source_key`
   - `ix_journal_entry_book_posted_at` (for reporting)

#### Part B: idempotency_keys Table Changes

1. ✅ **Drops old columns and constraints**
   - Removes `key` (renamed to `idempotency_key`)
   - Removes `route` (replaced by `endpoint_key`)
   - Removes old unique constraint `(key, route)`

2. ✅ **Adds new scope columns**
   - `legal_entity_id` (UUID, NOT NULL, FK to legal_entity)
   - `book_id` (UUID, nullable for entity-level endpoints)
   - `endpoint_key` (VARCHAR(255), NOT NULL)
   - `idempotency_key` (VARCHAR(255), NOT NULL) - renamed from `key`

3. ✅ **Adds response tracking columns**
   - `response_status` (INTEGER, NOT NULL) - HTTP status code
   - `actor_user_id` (UUID, nullable) - for audit only

4. ✅ **Adds new unique constraint**
   ```sql
   UNIQUE(legal_entity_id, book_id, endpoint_key, idempotency_key)
   ```

5. ✅ **Adds indexes for performance**
   - `ix_idempotency_keys_legal_entity_id`
   - `ix_idempotency_keys_book_id`
   - `ix_idempotency_keys_endpoint_key`
   - `ix_idempotency_keys_idempotency_key`
   - `ix_idempotency_keys_actor_user_id`

### Backfill Strategy

- **journal_entry.legal_entity_id**: Derived from `book.legal_entity_id` (deterministic)
- **journal_entry.source_key**: Set to `JE:POST:{entry_id}` for existing posted entries
- **idempotency_keys**: Old records get sentinel values (legacy records are temporary anyway)

---

## Minimum Test Suite

### Test Files Created

1. ✅ **`tests/test_idempotency_replay.py`**
   - `test_je_post_idempotency_replay_same_key_same_body` - Same key + same body → replay
   - `test_je_post_idempotency_409_different_body` - Same key + different body → 409
   - `test_source_key_duplicate_prevention` - Different idempotency keys, same source_key → constraint violation

2. ✅ **`tests/test_row_version_409.py`**
   - `test_row_version_409_ap_bill_approve` - Stale version → 409
   - `test_row_version_success_match` - Matching version → success

3. ✅ **`tests/test_reconciliation_safety.py`**
   - `test_reconciliation_close_does_not_post_adjustments` - Close does NOT create JEs
   - `test_reconciliation_close_fails_if_difference_non_zero` - Close fails if difference != 0

4. ✅ **`tests/test_endpoint_key_stability.py`**
   - `test_endpoint_key_stability_same_path_different_ids` - Same pattern → same key
   - `test_endpoint_key_stability_different_methods` - Different methods → different keys
   - `test_endpoint_key_stability_query_params_ignored` - Query params ignored

### Test Coverage

✅ **Idempotency Replay** (3 endpoints tested conceptually)
- JE post replay
- 409 on different body
- Source key duplicate prevention

✅ **Source Key Duplication Prevention**
- Different idempotency keys with same source_key → constraint violation

✅ **Row Version 409**
- AP bill approve with stale version
- Success with matching version

✅ **Reconciliation Safety**
- Close does NOT post adjustments
- Close fails if difference != 0 (unless override)

✅ **Endpoint Key Stability**
- Same path pattern → same key
- Different methods → different keys
- Query params ignored

---

## Endpoint Key Stability

### Current Implementation

The `normalize_endpoint_key()` function:
- Replaces UUIDs (36 chars) with `{id}` placeholder
- Replaces numeric IDs with `{id}` placeholder
- Removes query parameters
- Preserves path structure

**Example:**
- `POST /books/123e4567-e89b-12d3-a456-426614174000/journal-entries/789e4567-e89b-12d3-a456-426614174001/post`
- Normalizes to: `POST:/books/{id}/journal-entries/{id}/post`

### Recommendation

For production stability, consider hardcoding endpoint keys per handler:
```python
# In each route handler
ENDPOINT_KEY = "JE_POST"  # Hardcoded constant

# Instead of
endpoint_key = normalize_endpoint_key(method, path)
```

This ensures:
- No path parsing bugs
- Easier debugging
- Explicit endpoint registration

---

## Schema After Migration

### idempotency_keys Table
```sql
CREATE TABLE idempotency_keys (
    id UUID PRIMARY KEY,
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    book_id UUID REFERENCES book(id),  -- Nullable for entity-level
    endpoint_key VARCHAR(255) NOT NULL,
    idempotency_key VARCHAR(255) NOT NULL,
    request_hash VARCHAR(64) NOT NULL,
    response_status INTEGER NOT NULL,
    response_blob TEXT NOT NULL,
    actor_user_id UUID,  -- For audit only
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    UNIQUE(legal_entity_id, book_id, endpoint_key, idempotency_key)
);
```

### journal_entry Table (New Columns)
```sql
ALTER TABLE journal_entry ADD COLUMN legal_entity_id UUID NOT NULL REFERENCES legal_entity(id);
ALTER TABLE journal_entry ADD COLUMN source_key VARCHAR(255);

CREATE UNIQUE INDEX uq_journal_entry_source_key 
ON journal_entry(legal_entity_id, book_id, source_key)
WHERE source_key IS NOT NULL;
```

---

## Next Steps

1. ✅ **Review migration** - Check backfill logic for your data
2. ⏳ **Run migration** - `alembic upgrade head`
3. ⏳ **Run tests** - `pytest tests/ -v`
4. ⏳ **Fix any test failures**
5. ⏳ **Consider hardcoding endpoint keys** for production stability

---

**Status:** Ready for migration application and test execution
