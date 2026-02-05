# Idempotency Code Review - Exact Implementation

**Date:** January 25, 2026  
**Status:** Ready for Edge Case Review

---

## Exact Code for Review

### 1. IdempotencyKey Model

```python
# app/modules/core/models/idempotency_model.py
"""Idempotency Key Model"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import func
import uuid
from app.core.database import Base


class IdempotencyKey(Base):
    """Idempotency key model for write API idempotency"""
    __tablename__ = "idempotency_keys"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Scope fields (included in uniqueness)
    legal_entity_id = Column(UUID(as_uuid=True), ForeignKey("legal_entity.id"), nullable=False, index=True)
    book_id = Column(UUID(as_uuid=True), ForeignKey("book.id"), nullable=False, index=True)  # NOT NULL
    endpoint_key = Column(String(255), nullable=False, index=True)  # Hardcoded constant
    idempotency_key = Column(String(255), nullable=False, index=True)  # Idempotency-Key header value
    
    # Request/Response tracking
    request_hash = Column(String(64), nullable=False)  # Hash of request body (canonical JSON)
    response_status = Column(Integer, nullable=False)  # HTTP status code
    response_blob = Column(Text, nullable=False)  # Stored response (JSON)
    
    # Audit (not in uniqueness)
    actor_user_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # For audit/trace only
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    __table_args__ = (
        {"comment": "Idempotency keys for write API idempotency - scoped by entity, book, endpoint"},
        {"unique": True, "columns": ["legal_entity_id", "book_id", "endpoint_key", "idempotency_key"]}
    )
    
    def __repr__(self):
        return f"<IdempotencyKey(entity={self.legal_entity_id}, book={self.book_id}, endpoint={self.endpoint_key}, key={self.idempotency_key})>"
```

### 2. apply_idempotency Helper Function

```python
# app/core/idempotency.py (complete function)
async def apply_idempotency(
    db: AsyncSession,
    idempotency_key: str,
    legal_entity_id: UUID,
    book_id: UUID,  # NOT NULL - all MVP endpoints have book_id
    endpoint_key: str,  # Hardcoded constant (e.g., "JE_POST") - DO NOT use normalize_endpoint_key
    request_body: Any,
    actor_user_id: Optional[UUID],
    handler_func,
    *handler_args,
    **handler_kwargs
) -> Tuple[int, Any]:
    """
    Apply idempotency check and either replay stored response or execute handler.
    
    Args:
        endpoint_key: Hardcoded constant from app.core.endpoint_keys (e.g., "JE_POST")
                     DO NOT pass normalized path - use constants for stability.
    
    Returns:
        Tuple of (status_code, response_data)
    """
    
    # Compute request hash
    request_hash = compute_request_hash(request_body)
    
    # Check for existing idempotency key
    stmt = select(IdempotencyKey).where(
        IdempotencyKey.legal_entity_id == legal_entity_id,
        IdempotencyKey.book_id == book_id,
        IdempotencyKey.endpoint_key == endpoint_key,
        IdempotencyKey.idempotency_key == idempotency_key
    )
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    
    if existing:
        # Key exists - check if hash matches
        if existing.request_hash != request_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Idempotency key '{idempotency_key}' already used with different request payload. "
                       "Key reuse with different request is not allowed."
            )
        
        # Hash matches - replay stored response (exact status and body)
        import json
        response_data = json.loads(existing.response_blob)
        return existing.response_status, response_data
    
    # Key doesn't exist - execute handler
    try:
        response = await handler_func(*handler_args, **handler_kwargs)
        
        # Serialize response
        if hasattr(response, 'model_dump'):
            response_dict = response.model_dump()
        elif hasattr(response, 'dict'):
            response_dict = response.dict()
        elif hasattr(response, '__dict__'):
            response_dict = {k: v for k, v in response.__dict__.items() if not k.startswith('_')}
        elif isinstance(response, dict):
            response_dict = response
        else:
            # Try to convert to dict
            response_dict = {"result": str(response)}
        
        # Response status defaults to 200 OK
        # Note: If handler raises HTTPException, it will be re-raised and not stored
        response_status = status.HTTP_200_OK
        
        response_blob = json.dumps(response_dict, default=str)
        
        # Store idempotency key (within transaction)
        idempotency_record = IdempotencyKey(
            legal_entity_id=legal_entity_id,
            book_id=book_id,  # NOT NULL
            endpoint_key=endpoint_key,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response_status=response_status,
            response_blob=response_blob,
            actor_user_id=actor_user_id
        )
        db.add(idempotency_record)
        await db.commit()
        
        return response_status, response
        
    except Exception as e:
        # Don't store failed requests - re-raise
        raise
```

### 3. Request Hashing Functions

```python
# app/core/idempotency.py
def canonicalize_json(data: Any) -> str:
    """Canonicalize JSON for stable hashing"""
    return json.dumps(data, sort_keys=True, separators=(',', ':'))


def compute_request_hash(body: Any) -> str:
    """Compute SHA-256 hash of request body"""
    canonical = canonicalize_json(body)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()
```

---

## Edge Cases to Review

### 1. Request Hashing
- ✅ Canonical JSON (sorted keys, no whitespace)
- ✅ SHA-256 for collision resistance
- ⚠️ **Question:** How does it handle nested objects, lists, dates, decimals?
  - Uses `json.dumps()` with `default=str` for non-serializable types
  - Dates/decimals will be stringified - is this stable?

### 2. Response Serialization
- ✅ Uses `json.dumps(response_dict, default=str)`
- ⚠️ **Question:** What if response contains non-serializable types?
  - `default=str` handles most cases
  - But what about complex objects, UUIDs, dates?
  - Should we use Pydantic's `model_dump_json()` for better serialization?

### 3. Transaction Boundaries
- ✅ Check happens BEFORE handler
- ✅ Storage happens AFTER handler succeeds
- ✅ Failed handlers don't store
- ⚠️ **Question:** What if handler succeeds but commit fails?
  - Current: Exception re-raised, no storage (correct)
  - But what if there's a race condition between check and storage?

### 4. Response Status Code
- ⚠️ **Current:** Always defaults to 200 OK
- **Question:** What if handler needs to return 201 Created, 202 Accepted, etc.?
  - Options:
    1. Allow handler to return `(status, data)` tuple
    2. Inspect response for status field
    3. Capture from HTTPException (but those aren't stored)
  - **Recommendation:** Allow `(status, data)` tuple return

### 5. Concurrent Requests
- ⚠️ **Question:** What if two requests with same key arrive simultaneously?
  - Both check → both see "not exists" → both execute handler
  - Second one will fail on unique constraint violation
  - **Is this acceptable?** Or should we use database-level locking?

---

## Migration Safety

### Old idempotency_keys Handling
- ✅ Deletes old unscoped records (they're temporary anyway)
- ✅ Makes book_id NOT NULL after cleanup
- ✅ Unique constraint prevents NULL issues

### journal_entry Backfill
- ✅ legal_entity_id: Deterministic (from book)
- ✅ source_key: Only for posted entries (drafts remain NULL)
- ✅ Partial unique index allows NULLs

---

## Known Issues

### Bank Account book_id
- ⚠️ `BankAccount` model doesn't have `book_id` field
- Settlement routes get book_id from CASH book for entity (workaround)
- **Action Needed:** Add `book_id` to `BankAccount` model or verify approach

---

## Ready for Final Review

Please review the exact code above and point out any remaining edge cases, especially:
1. Request hashing edge cases (nested objects, dates, decimals)
2. Response serialization edge cases
3. Transaction boundary race conditions
4. Response status code handling
5. Concurrent request handling
