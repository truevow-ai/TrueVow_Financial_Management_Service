"""Idempotency Infrastructure for Request Replay"""
import hashlib
import json
import re
from typing import Optional, Dict, Any, Tuple
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
from uuid import UUID
from fastapi import Header, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.modules.core.models.idempotency_model import IdempotencyKey, IdempotencyState
from app.core.endpoint_safety import is_safe_to_retry_failed, get_lock_ttl_seconds
import logging

logger = logging.getLogger(__name__)

# Configuration
MAX_RESPONSE_BLOB_SIZE = 100000  # 100KB max response size


def to_canonical_jsonable(x: Any) -> Any:
    """
    Convert any Python object to a JSON-serializable canonical form.
    
    Handles:
    - Decimal -> string (no scientific notation)
    - datetime/date -> ISO-8601 string (timezone-aware, UTC for naive)
    - UUID -> string
    - Pydantic models -> dict (canonical)
    - dict -> sorted keys
    - list/tuple/set -> list
    - bytes -> UTF-8 decoded string
    """
    if x is None or isinstance(x, (str, int, bool, float)):
        return x
    
    if isinstance(x, Decimal):
        # Format as fixed-point string, no scientific notation
        return format(x, 'f')
    
    if isinstance(x, datetime):
        # Ensure timezone-aware: convert naive to UTC
        if x.tzinfo is None:
            # Finance systems should not accept ambiguous timestamps
            # But for backward compatibility, assume UTC
            # Log warning to detect upstream bugs
            logger.warning(
                "Naive datetime normalized to UTC in idempotency hashing. "
                "This may indicate missing timezone in request data.",
                extra={"datetime_value": str(x)}
            )
            x = x.replace(tzinfo=timezone.utc)
        return x.isoformat()
    
    if isinstance(x, date):
        return x.isoformat()
    
    if isinstance(x, UUID):
        return str(x)
    
    if isinstance(x, bytes):
        return x.decode('utf-8')
    
    if isinstance(x, dict):
        # Sort keys for canonical ordering
        return {str(k): to_canonical_jsonable(v) for k, v in sorted(x.items(), key=lambda kv: str(kv[0]))}
    
    if isinstance(x, (list, tuple, set)):
        # Preserve order for lists/tuples
        return [to_canonical_jsonable(v) for v in x]
    
    # Pydantic v2
    if hasattr(x, "model_dump"):
        return to_canonical_jsonable(x.model_dump(mode="json", by_alias=True, exclude_none=True))
    
    # Pydantic v1 fallback
    if hasattr(x, "dict"):
        return to_canonical_jsonable(x.dict(by_alias=True, exclude_none=True))
    
    # Last resort: stringify (log in production if this happens)
    return str(x)


def canonicalize_json(data: Any) -> str:
    """Canonicalize JSON for stable hashing using canonical encoder"""
    canonical_data = to_canonical_jsonable(data)
    return json.dumps(canonical_data, separators=(',', ':'), ensure_ascii=False)


def compute_request_hash(body: Any) -> str:
    """Compute SHA-256 hash of request body using canonical encoding"""
    canonical = canonicalize_json(body)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


_UUID_PATTERN = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)


def normalize_endpoint_key(method: str, path: str) -> str:
    """Normalize endpoint to a stable key (e.g., 'POST:/books/{id}/journal-entries/{id}/post')"""
    parts = path.split('?')[0].split('/')
    normalized = []
    for part in parts:
        if part and (_UUID_PATTERN.match(part) or part.isdigit()):
            normalized.append('{id}')
        else:
            normalized.append(part or "")
    return f"{method}:{'/'.join(normalized)}"


async def get_idempotency_key_header(
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> Optional[str]:
    """Extract idempotency key from header"""
    return idempotency_key


async def check_and_store_idempotency(
    db: AsyncSession,
    idempotency_key: str,
    legal_entity_id: UUID,
    book_id: Optional[UUID],
    endpoint_key: str,
    request_body: Any,
    actor_user_id: Optional[UUID],
    handler_func,
    *args,
    **kwargs
) -> Tuple[int, Dict[str, Any]]:
    """
    Check idempotency key and either replay stored response or execute handler.
    
    Returns:
        Tuple of (status_code, response_dict)
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
        
        # Hash matches - replay stored response
        import json
        response_data = json.loads(existing.response_blob)
        return existing.response_status, response_data
    
    # Key doesn't exist - execute handler
    try:
        response = await handler_func(*args, **kwargs)
        
        # Serialize response
        if hasattr(response, 'dict'):
            response_dict = response.dict()
        elif hasattr(response, '__dict__'):
            response_dict = {k: v for k, v in response.__dict__.items() if not k.startswith('_')}
        elif isinstance(response, dict):
            response_dict = response
        else:
            # Try to convert to dict
            response_dict = {"result": str(response)}
        
        response_status = status.HTTP_200_OK  # Default, can be overridden if needed
        response_blob = json.dumps(response_dict)
        
        # Store idempotency key
        idempotency_record = IdempotencyKey(
            legal_entity_id=legal_entity_id,
            book_id=book_id,
            endpoint_key=endpoint_key,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            response_status=response_status,
            response_blob=response_blob,
            actor_user_id=actor_user_id
        )
        db.add(idempotency_record)
        await db.commit()
        
        return response_status, response_dict
        
    except Exception as e:
        # Don't store failed requests
        raise


async def require_idempotency_key(
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key")
) -> str:
    """Dependency that requires Idempotency-Key header"""
    if not idempotency_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required for this endpoint"
        )
    return idempotency_key


async def apply_idempotency(
    db: AsyncSession,
    idempotency_key: str,
    legal_entity_id: UUID,
    book_id: UUID,  # NOT NULL - all MVP endpoints have book_id
    endpoint_key: str,  # Hardcoded constant (e.g., "JE_POST") - DO NOT use normalize_endpoint_key
    request_body: Any,
    actor_user_id: Optional[UUID],
    handler_func,
    metadata: Optional[dict] = None,  # Optional metadata for correlation (e.g., batch_id, cursor_start)
    *handler_args,
    **handler_kwargs
) -> Tuple[int, Any]:
    """
    Apply idempotency check and either replay stored response or execute handler.
    
    Race condition prevention:
    1. Try to insert PENDING row (reserves key)
    2. If unique violation, check existing state:
       - COMPLETED: Replay response
       - PENDING: Return 425 Too Early (request in progress)
       - Different hash: Return 409 Conflict
    3. Execute handler
    4. Update row to COMPLETED with response
    5. On exception: Update to FAILED with error response
    
    Args:
        endpoint_key: Hardcoded constant from app.core.endpoint_keys (e.g., "JE_POST")
                     DO NOT pass normalized path - use constants for stability.
    
    Returns:
        Tuple of (status_code, response_data)
    """
    import json
    
    # Compute request hash using canonical encoder
    request_hash = compute_request_hash(request_body)
    
    # Step 1: Try to reserve the key by inserting PENDING row
    idempotency_record = None
    is_retry = False
    now = datetime.now(timezone.utc)
    
    # Serialize metadata if provided
    metadata_json_str = None
    if metadata:
        metadata_json_str = json.dumps(metadata, separators=(',', ':'), ensure_ascii=False)
    
    try:
        idempotency_record = IdempotencyKey(
            legal_entity_id=legal_entity_id,
            book_id=book_id,
            endpoint_key=endpoint_key,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            state=IdempotencyState.PENDING,
            response_status=None,  # NULL for PENDING
            response_blob=None,  # NULL for PENDING
            metadata_json=metadata_json_str,  # Store correlation metadata
            actor_user_id=actor_user_id,
            locked_at=now
        )
        db.add(idempotency_record)
        await db.commit()  # COMMIT after reservation so concurrent requests see it
    except IntegrityError:
        # Key already exists - fetch and check state
        await db.rollback()
        
        stmt = select(IdempotencyKey).where(
            IdempotencyKey.legal_entity_id == legal_entity_id,
            IdempotencyKey.book_id == book_id,
            IdempotencyKey.endpoint_key == endpoint_key,
            IdempotencyKey.idempotency_key == idempotency_key
        )
        result = await db.execute(stmt)
        existing = result.scalar_one()
        
        # Check request hash
        if existing.request_hash != request_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Idempotency key '{idempotency_key}' already used with different request payload. "
                       "Key reuse with different request is not allowed."
            )
        
        # Hash matches - check state
        if existing.state == IdempotencyState.COMPLETED:
            # Replay stored response
            response_data = json.loads(existing.response_blob)
            # If metadata exists (e.g., batch_id), include it in response for correlation
            # Note: This is optional - metadata is primarily for audit/debug
            return existing.response_status, response_data
        
        elif existing.state == IdempotencyState.PENDING:
            # Check if lock is stale (expired) using endpoint-specific TTL
            ttl_seconds = get_lock_ttl_seconds(endpoint_key)
            lock_age = (now - existing.locked_at).total_seconds()
            
            if lock_age > ttl_seconds:
                # Stale lock - treat as FAILED and allow takeover
                # Log for monitoring
                logger.warning(
                    f"Stale PENDING lock detected for endpoint {endpoint_key}. "
                    f"Lock age: {lock_age:.1f}s, TTL: {ttl_seconds}s. "
                    f"Transitioning to FAILED to allow retry.",
                    extra={
                        "endpoint_key": endpoint_key,
                        "lock_age_seconds": lock_age,
                        "ttl_seconds": ttl_seconds,
                        "idempotency_key": idempotency_key
                    }
                )
                existing.state = IdempotencyState.FAILED
                existing.response_status = status.HTTP_500_INTERNAL_SERVER_ERROR
                existing.response_blob = json.dumps({
                    "error": "Previous request timed out (stale_lock_ttl_exceeded)",
                    "status_code": 500,
                    "lock_age_seconds": lock_age,
                    "ttl_seconds": ttl_seconds
                }, separators=(',', ':'))
                await db.commit()
                # Fall through to FAILED handling below
            
            if existing.state == IdempotencyState.PENDING:
                # Lock is still valid - return 409 Conflict with IDEMPOTENCY_IN_PROGRESS code
                # Using 409 for maximum client compatibility (425 not universally handled)
                # Calculate retry delay based on remaining TTL
                remaining_ttl = max(1, int(ttl_seconds - lock_age))
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": "Idempotency key is currently being processed",
                        "code": "IDEMPOTENCY_IN_PROGRESS",
                        "message": f"Idempotency key '{idempotency_key}' is currently being processed. Please retry after a short delay."
                    },
                    headers={"Retry-After": str(remaining_ttl)}
                )
        
        elif existing.state == IdempotencyState.FAILED:
            # Previous attempt failed - check if safe to retry
            if not is_safe_to_retry_failed(endpoint_key):
                # Not safe to auto-retry - require explicit retry header
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Previous request with idempotency key '{idempotency_key}' failed. "
                           "This endpoint may have partial side effects. "
                           "To retry, include 'Retry-Idempotency: true' header."
                )
            
            # Safe to retry - update to PENDING
            existing.state = IdempotencyState.PENDING
            existing.locked_at = now
            existing.request_hash = request_hash  # Update hash in case request changed
            existing.response_status = None
            existing.response_blob = None
            await db.commit()
            # Continue to handler execution below
            idempotency_record = existing
            is_retry = True
    
    # Step 2: Execute handler (key is now reserved as PENDING)
    # idempotency_record is guaranteed to exist here (either newly inserted or retried FAILED)
    try:
        response = await handler_func(*handler_args, **handler_kwargs)
        
        # Step 3: Serialize response using canonical encoder
        # Handle tuple responses (status, data)
        if isinstance(response, tuple) and len(response) == 2:
            response_status, response_data = response
            response_dict = to_canonical_jsonable(response_data)
        else:
            response_status = status.HTTP_200_OK  # Default
            response_dict = to_canonical_jsonable(response)
        
        # Handle 204 No Content
        if response_status == status.HTTP_204_NO_CONTENT:
            response_dict = {}
        
        # Store as canonical JSON (already canonical from to_canonical_jsonable)
        response_blob = json.dumps(response_dict, separators=(',', ':'), ensure_ascii=False)
        
        # Cap response size to prevent table bloat
        if len(response_blob) > MAX_RESPONSE_BLOB_SIZE:
            # Store summary instead of full response
            response_summary = {
                "truncated": True,
                "original_size": len(response_blob),
                "summary": "Response too large to store. Check endpoint logs for full response."
            }
            response_blob = json.dumps(response_summary, separators=(',', ':'), ensure_ascii=False)
        
        # Step 4: Update to COMPLETED (separate transaction)
        # Note: idempotency_record may be from a different session after commit
        # Re-fetch to ensure we're updating the correct record
        stmt = select(IdempotencyKey).where(
            IdempotencyKey.legal_entity_id == legal_entity_id,
            IdempotencyKey.book_id == book_id,
            IdempotencyKey.endpoint_key == endpoint_key,
            IdempotencyKey.idempotency_key == idempotency_key
        )
        result = await db.execute(stmt)
        record_to_update = result.scalar_one()
        
        record_to_update.state = IdempotencyState.COMPLETED
        record_to_update.response_status = response_status
        record_to_update.response_blob = response_blob
        # Preserve metadata_json if it was set on creation
        if metadata_json_str:
            record_to_update.metadata_json = metadata_json_str
        
        await db.commit()  # COMMIT after completion update
        
        return response_status, response_dict
        
    except HTTPException as e:
        # HTTPException from handler - store as FAILED
        error_response = {
            "error": e.detail,
            "status_code": e.status_code
        }
        response_blob = json.dumps(error_response, separators=(',', ':'), ensure_ascii=False)
        
        # Re-fetch record to update (may be from different session)
        stmt = select(IdempotencyKey).where(
            IdempotencyKey.legal_entity_id == legal_entity_id,
            IdempotencyKey.book_id == book_id,
            IdempotencyKey.endpoint_key == endpoint_key,
            IdempotencyKey.idempotency_key == idempotency_key
        )
        result = await db.execute(stmt)
        record_to_update = result.scalar_one()
        
        record_to_update.state = IdempotencyState.FAILED
        record_to_update.response_status = e.status_code
        record_to_update.response_blob = response_blob
        
        await db.commit()  # COMMIT after failure update
        raise
        
    except Exception as e:
        # Other exceptions - store as FAILED with 500
        error_response = {
            "error": str(e),
            "status_code": 500
        }
        response_blob = json.dumps(error_response, separators=(',', ':'), ensure_ascii=False)
        
        # Re-fetch record to update (may be from different session)
        stmt = select(IdempotencyKey).where(
            IdempotencyKey.legal_entity_id == legal_entity_id,
            IdempotencyKey.book_id == book_id,
            IdempotencyKey.endpoint_key == endpoint_key,
            IdempotencyKey.idempotency_key == idempotency_key
        )
        result = await db.execute(stmt)
        record_to_update = result.scalar_one()
        
        record_to_update.state = IdempotencyState.FAILED
        record_to_update.response_status = status.HTTP_500_INTERNAL_SERVER_ERROR
        record_to_update.response_blob = response_blob
        
        await db.commit()  # COMMIT after failure update
        raise
