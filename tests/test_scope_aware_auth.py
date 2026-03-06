"""
Tests for Scope-Aware Authentication System
Validates:
- JWT claims validation for internal vs tenant scopes
- Permission checking for internal users
- Permission checking for tenant users
- Mixed scope rejection
- Missing scope rejection
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4
from jose import jwt
from fastapi import HTTPException

from app.auth.jwt_claims import (
    validate_jwt_claims,
    InternalJWTClaims,
    TenantJWTClaims,
    AuthScope,
    InternalUserContext,
    TenantUserContext,
)
from app.auth.authorization import (
    get_user_context,
    require_internal_user,
    require_tenant_user,
    require_internal_permission,
    require_tenant_permission,
    Permission,
    TenantPermission,
    INTERNAL_ROLE_PERMISSIONS,
    TENANT_ROLE_PERMISSIONS,
)
from app.core.config import settings


# Test JWT payloads
def create_internal_token_payload(
    user_id: str = "user_123",
    email: str = "john@truevow.com",
    internal_role: str = "senior",
    internal_function: str = "finance",
    org_id: str = "org_abc123",
    expired: bool = False,
) -> dict:
    """Create a valid internal user JWT payload."""
    now = datetime.now(timezone.utc)
    exp_time = now - timedelta(minutes=10) if expired else now + timedelta(minutes=30)
    return {
        "iss": "https://clerk.truevow.com",
        "sub": user_id,
        "email": email,
        "scope": "internal",
        "org_id": org_id,
        "internal_role": internal_role,
        "internal_function": internal_function,
        "iat": int(now.timestamp()),
        "exp": int(exp_time.timestamp()),
    }


def create_tenant_token_payload(
    user_id: str = "user_456",
    email: str = "jane@lawfirm.com",
    tenant_id: str = "tenant_abc123",
    tenant_role: str = "admin",
    org_id: str = "org_abc123",
    expired: bool = False,
) -> dict:
    """Create a valid tenant user JWT payload."""
    now = datetime.now(timezone.utc)
    exp_time = now - timedelta(minutes=10) if expired else now + timedelta(minutes=30)
    return {
        "iss": "https://clerk.truevow.com",
        "sub": user_id,
        "email": email,
        "scope": "tenant",
        "org_id": org_id,
        "tenant_id": tenant_id,
        "tenant_role": tenant_role,
        "iat": int(now.timestamp()),
        "exp": int(exp_time.timestamp()),
    }


def create_mixed_scope_payload() -> dict:
    """Create a JWT payload with BOTH internal and tenant claims (should be rejected)."""
    now = datetime.now(timezone.utc)
    return {
        "iss": "https://clerk.truevow.com",
        "sub": "user_789",
        "email": "mixed@example.com",
        "scope": "internal",
        "org_id": "org_abc123",
        "internal_role": "senior",
        "tenant_id": "tenant_abc123",  # Mixed!
        "tenant_role": "admin",  # Mixed!
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=30)).timestamp()),
    }


def create_missing_scope_payload() -> dict:
    """Create a JWT payload without scope (should be rejected)."""
    now = datetime.now(timezone.utc)
    return {
        "iss": "https://clerk.truevow.com",
        "sub": "user_999",
        "email": "noscope@example.com",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=30)).timestamp()),
    }


class TestJWTClaimsValidation:
    """Test JWT claims validation."""

    def test_valid_internal_token_accepted(self):
        """Test valid internal token is accepted and parsed correctly."""
        payload = create_internal_token_payload()
        result = validate_jwt_claims(payload)
        
        assert isinstance(result, InternalJWTClaims)
        assert result.sub == "user_123"
        assert result.email == "john@truevow.com"
        assert result.scope == AuthScope.INTERNAL
        assert result.internal_role == "senior"
        assert result.internal_function == "finance"
        assert result.tenant_id is None
        assert result.tenant_role is None

    def test_valid_tenant_token_accepted(self):
        """Test valid tenant token is accepted and parsed correctly."""
        payload = create_tenant_token_payload()
        result = validate_jwt_claims(payload)
        
        assert isinstance(result, TenantJWTClaims)
        assert result.sub == "user_456"
        assert result.email == "jane@lawfirm.com"
        assert result.scope == AuthScope.TENANT
        assert result.tenant_id == "tenant_abc123"
        assert result.tenant_role == "admin"
        assert result.internal_role is None
        assert result.internal_function is None

    def test_mixed_scope_rejected(self):
        """Test JWT with both internal AND tenant claims is rejected."""
        payload = create_mixed_scope_payload()
        
        with pytest.raises(HTTPException) as exc_info:
            validate_jwt_claims(payload)
        
        assert exc_info.value.status_code == 401
        assert "internal scope cannot have tenant claims" in exc_info.value.detail

    def test_tenant_scope_with_internal_rejected(self):
        """Test JWT with tenant scope but internal claims is rejected."""
        now = datetime.now(timezone.utc)
        payload = {
            "iss": "https://clerk.truevow.com",
            "sub": "user_999",
            "email": "wrong@example.com",
            "scope": "tenant",
            "tenant_id": "tenant_abc123",
            "tenant_role": "admin",
            "internal_role": "senior",  # Wrong!
            "internal_function": "finance",  # Wrong!
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=30)).timestamp()),
        }
        
        with pytest.raises(HTTPException) as exc_info:
            validate_jwt_claims(payload)
        
        assert exc_info.value.status_code == 401
        assert "tenant scope cannot have internal claims" in exc_info.value.detail

    def test_missing_scope_rejected(self):
        """Test JWT without scope claim is rejected."""
        payload = create_missing_scope_payload()
        
        with pytest.raises(HTTPException) as exc_info:
            validate_jwt_claims(payload)
        
        assert exc_info.value.status_code == 401
        assert "missing scope claim" in exc_info.value.detail

    def test_unknown_scope_rejected(self):
        """Test JWT with unknown scope value is rejected."""
        now = datetime.now(timezone.utc)
        payload = {
            "iss": "https://clerk.truevow.com",
            "sub": "user_999",
            "email": "unknown@example.com",
            "scope": "unknown_scope",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=30)).timestamp()),
        }
        
        with pytest.raises(HTTPException) as exc_info:
            validate_jwt_claims(payload)
        
        assert exc_info.value.status_code == 401
        assert "unknown scope" in exc_info.value.detail

    def test_invalid_internal_role_rejected(self):
        """Test JWT with invalid internal_role is rejected."""
        payload = create_internal_token_payload(internal_role="invalid_role")
        
        with pytest.raises(HTTPException) as exc_info:
            validate_jwt_claims(payload)
        
        assert exc_info.value.status_code == 401
        assert "Invalid internal_role" in exc_info.value.detail

    def test_invalid_tenant_role_rejected(self):
        """Test JWT with invalid tenant_role is rejected."""
        payload = create_tenant_token_payload(tenant_role="invalid_role")
        
        with pytest.raises(HTTPException) as exc_info:
            validate_jwt_claims(payload)
        
        assert exc_info.value.status_code == 401
        assert "Invalid tenant_role" in exc_info.value.detail


class TestInternalRolePermissions:
    """Test internal role to permission mapping."""

    def test_junior_role_permissions(self):
        """Test junior role has correct permissions."""
        perms = INTERNAL_ROLE_PERMISSIONS.get("junior", [])
        assert Permission.READ_TASKS in perms
        assert Permission.CREATE_TASKS in perms
        assert Permission.GL_READ in perms
        # Should NOT have write permissions
        assert Permission.GL_WRITE not in perms

    def test_senior_role_permissions(self):
        """Test senior role has correct permissions."""
        perms = INTERNAL_ROLE_PERMISSIONS.get("senior", [])
        assert Permission.READ_TASKS in perms
        assert Permission.CREATE_TASKS in perms
        assert Permission.MANAGE_TASKS in perms
        assert Permission.GL_READ in perms
        assert Permission.GL_WRITE in perms

    def test_director_role_has_all_permissions(self):
        """Test director role has all permissions."""
        perms = INTERNAL_ROLE_PERMISSIONS.get("director", [])
        # Directors should have all permissions
        assert Permission.READ_TASKS in perms
        assert Permission.GL_POST in perms
        assert Permission.PAYROLL_POST in perms

    def test_executive_role_has_all_permissions(self):
        """Test executive role has all permissions."""
        perms = INTERNAL_ROLE_PERMISSIONS.get("executive", [])
        # Executives should have all permissions
        assert Permission.READ_TASKS in perms
        assert Permission.GL_POST in perms
        assert Permission.PAYROLL_POST in perms


class TestTenantRolePermissions:
    """Test tenant role to permission mapping."""

    def test_viewer_role_permissions(self):
        """Test viewer role has correct permissions."""
        perms = TENANT_ROLE_PERMISSIONS.get("viewer", [])
        assert TenantPermission.VIEW_USERS in perms
        assert TenantPermission.VIEW_CASES in perms
        assert TenantPermission.FM_VIEW in perms
        # Should NOT have write permissions
        assert TenantPermission.FM_JOURNAL_ENTRY not in perms

    def test_member_role_permissions(self):
        """Test member role has correct permissions."""
        perms = TENANT_ROLE_PERMISSIONS.get("member", [])
        assert TenantPermission.VIEW_USERS in perms
        assert TenantPermission.CREATE_CASES in perms
        assert TenantPermission.FM_VIEW in perms
        assert TenantPermission.FM_JOURNAL_ENTRY in perms
        # Should NOT have admin permissions
        assert TenantPermission.MANAGE_USERS not in perms

    def test_admin_role_has_all_permissions(self):
        """Test admin role has all permissions."""
        perms = TENANT_ROLE_PERMISSIONS.get("admin", [])
        # Admins should have all tenant permissions
        assert TenantPermission.VIEW_USERS in perms
        assert TenantPermission.MANAGE_USERS in perms
        assert TenantPermission.FM_POST in perms


class TestUserContextPermissions:
    """Test user context permission checking."""

    def test_internal_user_has_permission_true(self):
        """Test internal user with permission returns True."""
        ctx = InternalUserContext(
            user_id="user_123",
            email="john@truevow.com",
            org_id="org_abc123",
            internal_role="senior",
            internal_function="finance",
            permissions=["read:tasks", "create:tasks", "gl:write"],
        )
        
        assert ctx.is_internal() is True
        assert ctx.is_tenant() is False
        assert ctx.has_permission("gl:write") is True
        assert ctx.has_permission("gl:post") is False

    def test_internal_user_has_wildcard_permission(self):
        """Test internal user with wildcard has all permissions."""
        ctx = InternalUserContext(
            user_id="user_123",
            email="john@truevow.com",
            org_id="org_abc123",
            internal_role="director",
            internal_function="finance",
            permissions=["*"],
        )
        
        assert ctx.has_permission("gl:write") is True
        assert ctx.has_permission("gl:post") is True
        assert ctx.has_permission("any:permission") is True

    def test_tenant_user_has_permission_true(self):
        """Test tenant user with permission returns True."""
        ctx = TenantUserContext(
            user_id="user_456",
            email="jane@lawfirm.com",
            org_id="org_abc123",
            tenant_id="tenant_abc123",
            tenant_role="admin",
            permissions=["tenant:view_users", "tenant:manage_users", "fm:journal_entry"],
        )
        
        assert ctx.is_internal() is False
        assert ctx.is_tenant() is True
        assert ctx.has_permission("tenant:manage_users") is True
        assert ctx.has_permission("fm:journal_entry") is True
        assert ctx.has_permission("tenant:view_billing") is False

    def test_user_context_without_permissions_returns_false(self):
        """Test user context with None permissions returns False."""
        ctx = InternalUserContext(
            user_id="user_123",
            email="john@truevow.com",
            org_id="org_abc123",
            internal_role="junior",
            internal_function="finance",
            permissions=None,
        )
        
        assert ctx.has_permission("gl:write") is False


class TestPermissionEnums:
    """Test permission enum values."""

    def test_internal_permissions_exist(self):
        """Test all internal permissions are defined."""
        assert Permission.GL_READ.value == "gl:read"
        assert Permission.GL_WRITE.value == "gl:write"
        assert Permission.GL_POST.value == "gl:post"
        assert Permission.GL_REVERSE.value == "gl:reverse"
        assert Permission.AP_READ.value == "ap:read"
        assert Permission.AP_WRITE.value == "ap:write"
        assert Permission.AR_READ.value == "ar:read"
        assert Permission.PAYROLL_READ.value == "payroll:read"
        assert Permission.PAYROLL_WRITE.value == "payroll:write"
        assert Permission.PAYROLL_POST.value == "payroll:post"

    def test_tenant_permissions_exist(self):
        """Test all tenant permissions are defined."""
        assert TenantPermission.FM_VIEW.value == "fm:view"
        assert TenantPermission.FM_JOURNAL_ENTRY.value == "fm:journal_entry"
        assert TenantPermission.FM_APPROVE.value == "fm:approve"
        assert TenantPermission.FM_POST.value == "fm:post"
        assert TenantPermission.VIEW_USERS.value == "tenant:view_users"
        assert TenantPermission.MANAGE_USERS.value == "tenant:manage_users"


class TestAuthScopeEnum:
    """Test AuthScope enum values."""

    def test_internal_scope_value(self):
        """Test internal scope has correct value."""
        assert AuthScope.INTERNAL.value == "internal"

    def test_tenant_scope_value(self):
        """Test tenant scope has correct value."""
        assert AuthScope.TENANT.value == "tenant"
