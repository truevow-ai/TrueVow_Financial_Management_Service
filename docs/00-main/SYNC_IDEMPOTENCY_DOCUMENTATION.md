# Sync Endpoint Idempotency Documentation

**Date:** January 27, 2026  
**Status:** ✅ Complete

---

## Overview

Sync endpoints (`BILLING_SYNC` and `TREASURY_SYNC`) use **API-level idempotency** via the `Idempotency-Key` header mechanism, not `source_key` on journal entries.

**Why:** Sync operations are side-effect-y (create/update records) but do not create journal entries. Therefore, idempotency belongs at the API request layer, not at the posting layer.

---

## Idempotency Mechanism

### Client Responsibility
- **Required:** Client must provide `Idempotency-Key` header
- **Format:** Client-generated unique identifier (UUID recommended)
- **Scope:** Same key + same payload = cached response replay

### Server Implementation
1. **Idempotency Record:** Stored in `idempotency_keys` table
   - Scoped by: `(legal_entity_id, book_id, endpoint_key, idempotency_key)`
   - State: `PENDING` → `COMPLETED` / `FAILED`
   - Response: Stored in `response_blob` for replay

2. **Batch Tracking:** Sync batch created for audit/correlation
   - Batch created **before** sync work begins
   - Batch ID stored in `idempotency_keys.metadata_json`
   - Batch status: `PROCESSING` → `COMPLETED` / `FAILED`

3. **Metadata Correlation:**
   ```json
   {
     "batch_id": "550e8400-e29b-41d4-a716-446655440000",
     "batch_number": "BS-20260127-120000-0001",
     "cursor_start": "cursor_123",
     "cursor_end": "cursor_456"
   }
   ```

---

## Endpoints

### Billing Sync
- **Endpoint:** `POST /books/{book_id}/integrations/billing/sync`
- **Endpoint Key:** `BILLING_SYNC`
- **Batch Table:** `billing_sync_batch`
- **Metadata:** `{batch_id, batch_number, cursor_start, cursor_end}`

### Treasury Sync
- **Endpoint:** `POST /books/{book_id}/integrations/treasury/sync`
- **Endpoint Key:** `TREASURY_SYNC`
- **Batch Table:** `treasury_sync_batch`
- **Metadata:** `{batch_id, batch_number, cursor_start, cursor_end}`

---

## Idempotency Behavior

### First Request (New Key)
1. Client sends request with `Idempotency-Key: abc-123`
2. Server creates `PENDING` idempotency record
3. Server creates sync batch (status: `PROCESSING`)
4. Server stores `batch_id` in `metadata_json`
5. Server executes sync work
6. Server updates batch to `COMPLETED`
7. Server updates idempotency record to `COMPLETED` with response
8. Server updates `metadata_json` with `cursor_end`
9. Server returns response

### Replay Request (Same Key)
1. Client sends request with `Idempotency-Key: abc-123`
2. Server finds existing `COMPLETED` record
3. Server replays stored response (no sync work executed)
4. Server returns cached response

### Concurrent Request (Same Key)
1. Two clients send request with `Idempotency-Key: abc-123` simultaneously
2. First request creates `PENDING` record
3. Second request sees `PENDING` record
4. Second request returns `425 Too Early` with `Retry-After` header
5. Second client retries after delay
6. Second request sees `COMPLETED` record and replays response

---

## Batch vs Idempotency

| Aspect | Batch | Idempotency Record |
|--------|-------|-------------------|
| **Purpose** | Audit/logging | Request replay |
| **Uniqueness** | `batch_number` unique | `(entity, book, endpoint, key)` unique |
| **State** | `PROCESSING` → `COMPLETED` | `PENDING` → `COMPLETED` |
| **Correlation** | Stored in `metadata_json` | Links batch to request |

---

## Key Points

1. ✅ **Batch is for audit only** - Not used for idempotency enforcement
2. ✅ **Idempotency is header-based** - Client provides `Idempotency-Key`
3. ✅ **Metadata provides correlation** - `batch_id` stored in `metadata_json` for audit/debug
4. ✅ **No source_key** - Sync operations don't create journal entries, so no `source_key` field

---

## Migration Notes

- Migration `005_add_idempotency_metadata` adds `metadata_json` column
- Existing idempotency records will have `NULL` metadata (acceptable)
- New sync requests will store batch correlation data

---

**Status:** ✅ Documented and implemented
