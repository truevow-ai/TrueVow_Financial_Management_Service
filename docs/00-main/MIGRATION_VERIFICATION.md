# Migration Verification - Ready for Production Review

**Date:** January 25, 2026  
**Status:** ✅ Migration Created | ✅ Tests Created

---

## Migration File

**Filename:** `database/migrations/versions/002_add_idempotency_and_source_key_safety.py`  
**Revision ID:** `002_idempotency_source_key`  
**Depends on:** `001_approval_workflow`

---

## Idempotency Table Schema After Migration

```sql
CREATE TABLE idempotency_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Scope fields (included in uniqueness)
    legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
    book_id UUID REFERENCES book(id),  -- Nullable for entity-level endpoints
    endpoint_key VARCHAR(255) NOT NULL,
    idempotency_key VARCHAR(255) NOT NULL,  -- Renamed from 'key'
    
    -- Request/Response tracking
    request_hash VARCHAR(64) NOT NULL,
    response_status INTEGER NOT NULL,  -- HTTP status code
    response_blob TEXT NOT NULL,  -- JSON response
    
    -- Audit (not in uniqueness)
    actor_user_id UUID,  -- For audit/trace only
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    
    -- Unique constraint
    UNIQUE(legal_entity_id, book_id, endpoint_key, idempotency_key)
);

-- Indexes for performance
CREATE INDEX ix_idempotency_keys_legal_entity_id ON idempotency_keys(legal_entity_id);
CREATE INDEX ix_idempotency_keys_book_id ON idempotency_keys(book_id);
CREATE INDEX ix_idempotency_keys_endpoint_key ON idempotency_keys(endpoint_key);
CREATE INDEX ix_idempotency_keys_idempotency_key ON idempotency_keys(idempotency_key);
CREATE INDEX ix_idempotency_keys_actor_user_id ON idempotency_keys(actor_user_id);
CREATE INDEX ix_idempotency_keys_created_at ON idempotency_keys(created_at);
```

---

## Unique Index Definition for source_key

```sql
-- Partial unique index (only enforces uniqueness when source_key IS NOT NULL)
CREATE UNIQUE INDEX uq_journal_entry_source_key 
ON journal_entry(legal_entity_id, book_id, source_key)
WHERE source_key IS NOT NULL;
```

**Why partial index?**
- Allows multiple draft entries (source_key = NULL)
- Only enforces uniqueness for posted entries (source_key IS NOT NULL)
- Prevents duplicate postings while allowing draft flexibility

---

## journal_entry Table Changes

### New Columns
```sql
ALTER TABLE journal_entry 
ADD COLUMN legal_entity_id UUID NOT NULL REFERENCES legal_entity(id),
ADD COLUMN source_key VARCHAR(255);
```

### Backfill Strategy

1. **legal_entity_id**: Backfilled from `book.legal_entity_id`
   ```sql
   UPDATE journal_entry je
   SET legal_entity_id = b.legal_entity_id
   FROM book b
   WHERE je.book_id = b.id
   AND je.legal_entity_id IS NULL;
   ```

2. **source_key**: Backfilled for existing posted entries
   ```sql
   UPDATE journal_entry
   SET source_key = 'JE:POST:' || id::text
   WHERE status = 'POSTED'
   AND source_key IS NULL
   AND posted_at IS NOT NULL;
   ```

### Additional Indexes
```sql
CREATE INDEX ix_journal_entry_legal_entity_id ON journal_entry(legal_entity_id);
CREATE INDEX ix_journal_entry_source_key ON journal_entry(source_key);
CREATE INDEX ix_journal_entry_book_posted_at ON journal_entry(book_id, posted_at);
```

---

## Migration Safety Checks

### ✅ Backfill Safety
- `legal_entity_id`: Deterministic (from book relationship)
- `source_key`: Only set for posted entries (drafts remain NULL)
- Old `idempotency_keys`: Use sentinel values (legacy records are temporary)

### ✅ Constraint Safety
- Partial unique index allows NULLs for drafts
- Foreign key ensures `legal_entity_id` references valid entity
- Unique constraint prevents duplicate postings

### ✅ Performance
- All lookup columns indexed
- Composite indexes for common queries
- Partial index reduces index size

---

## Test Coverage

### ✅ Idempotency Replay Tests
- Same key + same body → replay response
- Same key + different body → 409 conflict
- New key → creates side effect once

### ✅ Source Key Duplication Prevention
- Different idempotency keys with same source_key → constraint violation
- Only one JE exists per source_key

### ✅ Row Version 409
- Stale version → 409 conflict
- Matching version → success

### ✅ Reconciliation Safety
- Close does NOT post adjustments
- Close fails if difference != 0 (unless override)

### ✅ Endpoint Key Stability
- Same path pattern → same key
- Different methods → different keys
- Query params ignored

---

## Endpoint Key Stability Note

**Current Implementation:** Path normalization with UUID/numeric replacement  
**Recommendation:** Consider hardcoding endpoint keys per handler for production stability

Example:
```python
# In route handler
ENDPOINT_KEY = "JE_POST"  # Hardcoded constant
```

This ensures:
- No path parsing bugs
- Easier debugging
- Explicit endpoint registration

---

## Ready for Review

✅ Migration file created  
✅ Backfill logic implemented  
✅ Unique constraints defined  
✅ Indexes added  
✅ Tests created  
✅ Documentation complete

**Next Step:** Review migration file and run `alembic upgrade head` on development database first.
