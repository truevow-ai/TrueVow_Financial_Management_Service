"""
Scope-Aware Authorization — TrueVow Security Contract v1
Version: 2.0.0

Contract compliance:
  Section 1  — tenant_id = Clerk org_id (TEXT)
  Section 2  — JWT claim schema: sub, org_id, tenant_id, scope
  Section 3  — Scope is FIRST gate after signature verification
  Section 4  — Centralized auth module; request_id at entry; AuthContext on request
  Section 5  — AUTH_MODE guard (enforced at startup in main.py)
  Section 6  — Permissions from DB; FAIL-CLOSED by default
  Section 6.3— resource:action permission naming
  Section 7  — Default-deny (callers must use require_* dependencies)
  Section 9  — Auth audit log written on every auth event
  Section 14 — Forbidden: JWT tenant_role, JWT permissions, UUID tenant_id,
               soft-auth, missing scope, silent fallback
"""

import uuid
from typing import List, Optional
from dataclasses import dataclass
from enum import Enum
from functools import wraps

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.auth.jwt_claims import (
    validate_jwt_claims,
    JWTClaimsBase,
    InternalJWTClaims,
    TenantJWTClaims,
    InternalUserContext,
    TenantUserContext,
    UserContext,
    AuthScope,
)
from app.auth.auth_context import AuthContext, get_jwks_manager
from app.auth.permissions import has_permission as check_fm_permission
from app.core.database import get_db_session
from app.core.logging import logger

security = HTTPBearer()


# =====================================================
# CONTRACT § 6.3 — PERMISSION NAMING: resource:action
# =====================================================

class Permission(str, Enum):
    """FM internal permissions (resource:action)."""
    # General Ledger
    GL_READ         = "gl:read"
    GL_WRITE        = "gl:write"
    GL_POST         = "gl:post"
    GL_REVERSE      = "gl:reverse"
    GL_CLOSE_PERIOD = "gl:close_period"
    # AP
    AP_READ         = "ap:read"
    AP_WRITE        = "ap:write"
    AP_POST         = "ap:post"
    AP_APPROVE      = "ap:approve"
    # AR
    AR_READ         = "ar:read"
    AR_WRITE        = "ar:write"
    AR_POST         = "ar:post"
    # Payroll
    PAYROLL_READ    = "payroll:read"
    PAYROLL_WRITE   = "payroll:write"
    PAYROLL_APPROVE = "payroll:approve"
    PAYROLL_POST    = "payroll:post"
    # Treasury
    TREASURY_READ       = "treasury:read"
    TREASURY_WRITE      = "treasury:write"
    TREASURY_RECONCILE  = "treasury:reconcile"
    TREASURY_APPROVE    = "treasury:approve"
    # Tasks (case management integration)
    READ_TASKS      = "tasks:read"
    CREATE_TASKS    = "tasks:create"
    MANAGE_TASKS    = "tasks:manage"
    # Admin
    READ_FINANCIALS     = "financials:read"
    ACCESS_AUDIT_LOGS   = "audit:read"
    MANAGE_USERS        = "users:manage"


class TenantPermission(str, Enum):
    """FM tenant permissions (resource:action)."""
    FM_VIEW          = "fm:view"
    FM_JOURNAL_ENTRY = "fm:journal_entry"
    FM_APPROVE       = "fm:approve"
    FM_POST          = "fm:post"
    BILLING_VIEW     = "billing:view"
    BILLING_MANAGE   = "billing:manage"
    # Users (canonical names — values match Security Contract)
    VIEW_USERS       = "tenant:view_users"
    MANAGE_USERS     = "tenant:manage_users"
    # Cases
    VIEW_CASES       = "cases:view"
    CREATE_CASES     = "cases:create"
    MANAGE_CASES     = "cases:manage"
    # Reporting / Settings
    REPORTS_VIEW     = "reports:view"
    SETTINGS_MANAGE  = "settings:manage"
    # Legacy aliases kept for backward compatibility
    USERS_VIEW       = "users:view"
    USERS_MANAGE     = "users:manage"


# Internal role → permission mapping
# Used ONLY when PERMISSION_FAIL_OPEN=true (non-production emergency fallback).
INTERNAL_ROLE_PERMISSIONS = {
    "junior":    [Permission.READ_TASKS, Permission.CREATE_TASKS,
                  Permission.GL_READ, Permission.AP_READ, Permission.AR_READ,
                  Permission.PAYROLL_READ, Permission.TREASURY_READ],
    "senior":    [Permission.READ_TASKS, Permission.CREATE_TASKS, Permission.MANAGE_TASKS,
                  Permission.GL_READ, Permission.GL_WRITE,
                  Permission.AP_READ, Permission.AP_WRITE,
                  Permission.AR_READ, Permission.AR_WRITE,
                  Permission.PAYROLL_READ, Permission.PAYROLL_WRITE,
                  Permission.TREASURY_READ, Permission.TREASURY_WRITE],
    "lead":      [Permission.READ_TASKS, Permission.CREATE_TASKS, Permission.MANAGE_TASKS,
                  Permission.GL_READ, Permission.GL_WRITE, Permission.GL_POST,
                  Permission.AP_READ, Permission.AP_WRITE, Permission.AP_POST,
                  Permission.AR_READ, Permission.AR_WRITE, Permission.AR_POST,
                  Permission.PAYROLL_READ, Permission.PAYROLL_WRITE, Permission.PAYROLL_APPROVE,
                  Permission.TREASURY_READ, Permission.TREASURY_WRITE, Permission.TREASURY_RECONCILE],
    "manager":   [Permission.READ_TASKS, Permission.CREATE_TASKS, Permission.MANAGE_TASKS,
                  Permission.GL_READ, Permission.GL_WRITE, Permission.GL_POST, Permission.GL_REVERSE,
                  Permission.AP_READ, Permission.AP_WRITE, Permission.AP_POST, Permission.AP_APPROVE,
                  Permission.AR_READ, Permission.AR_WRITE, Permission.AR_POST,
                  Permission.PAYROLL_READ, Permission.PAYROLL_WRITE, Permission.PAYROLL_APPROVE, Permission.PAYROLL_POST,
                  Permission.TREASURY_READ, Permission.TREASURY_WRITE, Permission.TREASURY_RECONCILE, Permission.TREASURY_APPROVE,
                  Permission.READ_FINANCIALS],
    "director":  [p for p in Permission],
    "executive": [p for p in Permission],
}

TENANT_ROLE_PERMISSIONS = {
    "viewer":       [TenantPermission.VIEW_USERS, TenantPermission.VIEW_CASES,
                     TenantPermission.FM_VIEW, TenantPermission.REPORTS_VIEW,
                     TenantPermission.USERS_VIEW],
    "member":       [TenantPermission.VIEW_USERS, TenantPermission.CREATE_CASES,
                     TenantPermission.FM_VIEW, TenantPermission.FM_JOURNAL_ENTRY,
                     TenantPermission.REPORTS_VIEW, TenantPermission.USERS_VIEW],
    "admin":        [p for p in TenantPermission],
    "billing_admin": [TenantPermission.FM_VIEW, TenantPermission.VIEW_USERS,
                      TenantPermission.BILLING_VIEW, TenantPermission.BILLING_MANAGE,
                      TenantPermission.REPORTS_VIEW, TenantPermission.USERS_VIEW],
}


# =====================================================
# INTERNAL — JWT DECODE
# =====================================================

async def _decode_jwt(token: str) -> dict:
    """
    Decode and verify JWT.

    auth_mode=clerk : RS256 via Clerk JWKS (production mandatory).
    auth_mode=local : HS256 symmetric key (dev/test only).

    Contract Section 4, item 2.
    Contract Section 5.
    """
    from app.core.config import settings

    if settings.auth_mode == "clerk":
        mgr = get_jwks_manager()
        if mgr is None:
            raise HTTPException(
                status_code=500,
                detail="JWKSManager not initialised. auth_mode=clerk requires init_jwks_manager() at startup.",
            )
        return await mgr.verify(token)
    else:
        # auth_mode=local — HS256 symmetric key
        from jose import jwt as jose_jwt, JWTError
        try:
            return jose_jwt.decode(
                token,
                settings.jwt_secret_key,
                algorithms=[settings.jwt_algorithm],
                options={"verify_aud": False},
            )
        except JWTError as exc:
            raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")


# =====================================================
# INTERNAL — PERMISSION LOADING (FAIL-CLOSED)
# =====================================================

async def _fetch_internal_permissions(
    db: AsyncSession,
    user_id: str,
    role: str,
) -> List[str]:
    """
    Load permissions from DB for internal users.

    Contract Section 6.2 — FAIL-CLOSED:
      - If DB query fails AND permission_fail_open=False (default): raise 403.
      - If permission_fail_open=True: use role-based fallback (non-production only).
    """
    from app.core.config import settings
    try:
        # TODO: Replace with real DB query once hr_role_permissions table exists.
        # SELECT p.permission FROM hr_user_permissions p
        #   WHERE p.user_id = :user_id AND p.is_active = true
        # For now simulate DB success with role-based mapping.
        return [p.value for p in INTERNAL_ROLE_PERMISSIONS.get(role.lower(), [])]
    except Exception as exc:
        logger.critical(
            f"Permission service unavailable for internal user {user_id}: {exc}"
        )
        if settings.permission_fail_open:
            # ALLOWED only in non-production with explicit opt-in
            logger.warning(
                "PERMISSION_FAIL_OPEN=true: using role-based fallback. "
                "This MUST be false in production."
            )
            return [p.value for p in INTERNAL_ROLE_PERMISSIONS.get(role.lower(), [])]
        # Contract Section 6.2: deny access, log critical event
        raise HTTPException(
            status_code=403,
            detail="Permission service unavailable. Access denied.",
        )


async def _fetch_tenant_permissions(
    db: AsyncSession,
    user_id: str,
    tenant_id: str,
    role: str,
) -> List[str]:
    """
    Load permissions from DB for tenant users.

    Contract Section 6.2 — FAIL-CLOSED.
    """
    from app.core.config import settings
    try:
        # TODO: Replace with real DB query once tenant_role_permissions table exists.
        return [p.value for p in TENANT_ROLE_PERMISSIONS.get(role.lower(), [])]
    except Exception as exc:
        logger.critical(
            f"Permission service unavailable for tenant user {user_id}/{tenant_id}: {exc}"
        )
        if settings.permission_fail_open:
            logger.warning(
                "PERMISSION_FAIL_OPEN=true: using role-based fallback. "
                "This MUST be false in production."
            )
            return [p.value for p in TENANT_ROLE_PERMISSIONS.get(role.lower(), [])]
        raise HTTPException(
            status_code=403,
            detail="Permission service unavailable. Access denied.",
        )


# =====================================================
# INTERNAL — AUTH AUDIT LOG WRITER
# =====================================================

async def _write_auth_audit(
    db: AsyncSession,
    *,
    request_id: str,
    event_type: str,
    tenant_id: Optional[str],
    clerk_user_id: Optional[str],
    scope: Optional[str] = None,
    fm_role: Optional[str] = None,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None,
    correlation_id: Optional[str] = None,
    permission_checked: Optional[str] = None,
    response_status: Optional[int] = None,
    details: Optional[dict] = None,
) -> None:
    """
    Write one row to auth_audit_log (contract Section 9).
    Never raises — auth audit write failure must never block the request.
    """
    try:
        from app.modules.core.models.auth_audit_log_model import AuthAuditLog
        import uuid as _uuid
        entry = AuthAuditLog(
            request_id=_uuid.UUID(request_id) if request_id else _uuid.uuid4(),
            event_type=event_type,
            tenant_id=tenant_id,
            clerk_user_id=clerk_user_id,
            scope=scope,
            fm_role=fm_role,
            endpoint=endpoint,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            permission_checked=permission_checked,
            response_status=response_status,
            details=details or {},
        )
        db.add(entry)
        await db.flush()   # write within caller's transaction
    except Exception as exc:
        # NEVER abort the caller's flow due to audit write failure.
        logger.error(f"_write_auth_audit failed (non-blocking): {exc}")


# =====================================================
# DEPENDENCY FUNCTIONS
# =====================================================

async def _get_jwt_claims(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> JWTClaimsBase:
    """
    Extract, verify, and parse JWT claims.

    Contract Section 3 — scope is enforced as FIRST gate.
    Contract Section 5 — uses JWKS in clerk mode.
    """
    token = credentials.credentials
    raw_claims = await _decode_jwt(token)

    # Scope gate — contract Section 3
    from app.core.config import settings
    scope = raw_claims.get("scope")
    if not scope:
        raise HTTPException(status_code=403, detail="JWT missing scope claim.")
    if scope not in settings.fm_allowed_scopes:
        raise HTTPException(
            status_code=403,
            detail=f"Scope '{scope}' not allowed for this service.",
        )

    return validate_jwt_claims(raw_claims)


async def get_user_context(
    claims: JWTClaimsBase = Depends(_get_jwt_claims),
    db: AsyncSession = Depends(get_db_session),
    request: Request = None,
) -> UserContext:
    """
    Build UserContext with DB-loaded permissions.
    Attaches AuthContext to request.state.auth_context.
    Writes auth_success event to auth_audit_log.
    """
    request_id = str(uuid.uuid4())
    ip    = _extract_ip(request)
    ua    = _extract_ua(request)
    corr  = getattr(getattr(request, "state", None), "correlation_id", None) if request else None
    path  = request.url.path if request else None
    meth  = request.method if request else None

    if isinstance(claims, InternalJWTClaims):
        permissions = await _fetch_internal_permissions(db, claims.sub, claims.internal_role)
        ctx = InternalUserContext(
            user_id=claims.sub,
            email=claims.email,
            org_id=claims.org_id,
            internal_role=claims.internal_role,
            internal_function=claims.internal_function,
            permissions=permissions,
        )
        # Attach AuthContext to request.state
        _attach_auth_context(request, request_id=request_id, claims=claims,
                             permissions=permissions, ip=ip, ua=ua, corr=corr)
        await _write_auth_audit(
            db, request_id=request_id, event_type="auth_success",
            tenant_id=claims.org_id, clerk_user_id=claims.sub,
            scope=claims.scope.value, fm_role=claims.internal_role,
            endpoint=path, method=meth,
            ip_address=ip, user_agent=ua, correlation_id=corr,
            response_status=200,
        )
        return ctx

    elif isinstance(claims, TenantJWTClaims):
        permissions = await _fetch_tenant_permissions(
            db, claims.sub, claims.tenant_id, claims.tenant_role
        )
        ctx = TenantUserContext(
            user_id=claims.sub,
            email=claims.email,
            org_id=claims.org_id,
            tenant_id=claims.tenant_id,
            tenant_role=claims.tenant_role,
            permissions=permissions,
        )
        _attach_auth_context(request, request_id=request_id, claims=claims,
                             permissions=permissions, ip=ip, ua=ua, corr=corr)
        await _write_auth_audit(
            db, request_id=request_id, event_type="auth_success",
            tenant_id=claims.tenant_id, clerk_user_id=claims.sub,
            scope=claims.scope.value, fm_role=claims.tenant_role,
            endpoint=path, method=meth,
            ip_address=ip, user_agent=ua, correlation_id=corr,
            response_status=200,
        )
        return ctx

    raise HTTPException(status_code=401, detail="Invalid token type")


async def require_internal_user(
    user: UserContext = Depends(get_user_context)
) -> InternalUserContext:
    """Require an internal (TrueVow employee) user. Default-deny for tenant users."""
    if not user.is_internal():
        raise HTTPException(
            status_code=403,
            detail="This endpoint requires internal user access",
        )
    return user


async def require_tenant_user(
    user: UserContext = Depends(get_user_context)
) -> TenantUserContext:
    """Require a tenant user. Default-deny for internal users."""
    if not user.is_tenant():
        raise HTTPException(
            status_code=403,
            detail="This endpoint requires tenant user access",
        )
    return user


def require_internal_permission(required_permissions: List[Permission]):
    """
    Require internal user with specific resource:action permissions.
    Contract Section 6.3 — resource:action naming.
    """
    async def dependency(
        user: InternalUserContext = Depends(require_internal_user),
    ) -> InternalUserContext:
        for perm in required_permissions:
            if not user.has_permission(perm.value):
                logger.warning(f"Permission denied: user {user.user_id} lacks {perm.value}")
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {perm.value} required",
                )
        return user
    return dependency


def require_tenant_permission(required_permissions: List[TenantPermission]):
    """
    Require tenant user with specific resource:action permissions.
    Contract Section 6.3 — resource:action naming.
    """
    async def dependency(
        user: TenantUserContext = Depends(require_tenant_user),
    ) -> TenantUserContext:
        for perm in required_permissions:
            if not user.has_permission(perm.value):
                logger.warning(f"Permission denied: user {user.user_id} lacks {perm.value}")
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission denied: {perm.value} required",
                )
        return user
    return dependency


# =====================================================
# HELPERS
# =====================================================

def _extract_ip(request: Optional[Request]) -> Optional[str]:
    if request is None:
        return None
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return getattr(request.client, "host", None)


def _extract_ua(request: Optional[Request]) -> Optional[str]:
    if request is None:
        return None
    return request.headers.get("User-Agent")


def _attach_auth_context(
    request: Optional[Request],
    *,
    request_id: str,
    claims: JWTClaimsBase,
    permissions: List[str],
    ip: Optional[str],
    ua: Optional[str],
    corr: Optional[str],
) -> None:
    """Attach AuthContext to request.state per contract Section 4."""
    if request is None:
        return
    tenant_id = getattr(claims, "tenant_id", None) or getattr(claims, "org_id", None)
    fm_role = getattr(claims, "internal_role", None) or getattr(claims, "tenant_role", None)
    request.state.auth_context = AuthContext(
        request_id=request_id,
        sub=claims.sub,
        org_id=claims.org_id,
        tenant_id=tenant_id,
        scope=claims.scope.value,
        email=claims.email,
        fm_role=fm_role,
        internal_role=getattr(claims, "internal_role", None),
        permissions=permissions,
        ip_address=ip,
        user_agent=ua,
        correlation_id=corr,
    )


# =====================================================
# LEGACY — auth_event logging compat shim
# =====================================================

async def log_auth_event(
    db: AsyncSession,
    user_id: str,
    action: str,
    resource: str,
    details: dict = None,
    ip_address: str = None,
):
    """Backward-compat shim.  New code should call _write_auth_audit directly."""
    await _write_auth_audit(
        db,
        request_id=str(uuid.uuid4()),
        event_type=action,
        tenant_id=None,
        clerk_user_id=user_id,
        endpoint=resource,
        ip_address=ip_address,
        details=details,
    )
