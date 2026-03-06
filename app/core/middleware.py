"""Core middleware for correlation IDs, request tracking, and audit context."""
import uuid
from fastapi import Request, Response
from starlette.types import ASGIApp
from app.core.logging import logger

try:
    from jose import jwt as _jose_jwt
    _JOSE_AVAILABLE = True
except ImportError:  # pragma: no cover
    _JOSE_AVAILABLE = False


async def correlation_id_middleware(request: Request, call_next):
    """Middleware to add correlation ID to requests (function-based)"""
    # Get or create correlation ID
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    
    # Add to request state
    request.state.correlation_id = correlation_id
    
    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.url.path,
        }
    )
    
    # Process request
    response: Response = await call_next(request)
    
    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response


async def audit_context_middleware(request: Request, call_next):
    """Best-effort: extract user_id and role from Bearer JWT for DB audit GUC injection.

    This middleware does NOT perform security validation — route-level
    Depends(get_current_user) still enforces authentication.

    The extracted values are stashed on request.state and later read by
    get_db_session() which injects them as PostgreSQL GUCs:

        SET LOCAL app.current_user_id   = '<id>';
        SET LOCAL app.current_user_role = '<role>';
        SET LOCAL app.correlation_id    = '<uuid>';

    The fn_row_audit_log() trigger reads these GUCs so every row written
    to any audited table carries the actor's identity.

    If no valid Bearer token is present (public routes, health checks,
    background tasks) both state attributes are set to None and the
    audit GUCs will be NULL — the trigger still fires and records the
    row with a NULL actor.
    """
    request.state.user_id   = None
    request.state.user_role = None

    if _JOSE_AVAILABLE:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                # get_unverified_claims does NOT verify the signature —
                # that is intentional here.  Auth is already enforced by
                # route-level dependencies; we only need the claims for
                # metadata / audit purposes.
                claims = _jose_jwt.get_unverified_claims(auth_header[7:])
                # Clerk tokens use 'sub' as the user identifier
                request.state.user_id = (
                    claims.get("sub")
                    or claims.get("user_id")
                    or claims.get("userId")
                )
                request.state.user_role = (
                    claims.get("fm_role")
                    or claims.get("role")
                    or claims.get("public_metadata", {}).get("fm_role")
                )
            except Exception:
                # Invalid / malformed token — silently ignore.
                # The route's auth dependency will reject it if needed.
                pass

    return await call_next(request)
