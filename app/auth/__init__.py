"""
Financial Management Authentication
Integrates with centralized auth service
"""

from .middleware import verify_fm_access, get_current_user, check_fm_permission
from .authorization import (
    get_user_context,
    require_internal_user,
    require_tenant_user,
    require_internal_permission,
    require_tenant_permission,
    InternalUserContext,
    TenantUserContext,
    UserContext,
    Permission,
    TenantPermission,
)

__all__ = [
    # Legacy (for backward compatibility)
    "verify_fm_access",
    "get_current_user",
    "check_fm_permission",
    # New scope-aware auth
    "get_user_context",
    "require_internal_user",
    "require_tenant_user",
    "require_internal_permission",
    "require_tenant_permission",
    "InternalUserContext",
    "TenantUserContext",
    "UserContext",
    "Permission",
    "TenantPermission",
]

