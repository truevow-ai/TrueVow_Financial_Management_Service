"""
Role and Permission Definitions for Financial Management Service
RBAC + Selective Approvals Implementation
"""

# Role definitions (RBAC roles for FM/Treasury)
ROLES = {
    "FINANCE_ADMIN": {
        "services": ["billing", "financial_management"],
        "permissions": ["read", "write", "admin"],
        "description": "Finance admin with full access to all FM operations, can override approvals"
    },
    "ACCOUNTANT": {
        "services": ["financial_management"],
        "permissions": ["read", "write"],
        "description": "Accountant can create/post JEs and AP, run revrec, but cannot close periods"
    },
    "PAYROLL_PREPARER": {
        "services": ["financial_management"],
        "permissions": ["read", "write"],
        "description": "Payroll preparer can create/calculate payroll runs, cannot post/pay"
    },
    "PAYROLL_APPROVER": {
        "services": ["financial_management"],
        "permissions": ["read", "write"],
        "description": "Payroll approver can approve/post payroll runs"
    },
    "TREASURY_CLERK": {
        "services": ["financial_management"],
        "permissions": ["read", "write"],
        "description": "Treasury clerk can import bank tx, create matches, cannot create adjustments"
    },
    "TREASURY_APPROVER": {
        "services": ["financial_management"],
        "permissions": ["read", "write"],
        "description": "Treasury approver can approve reconciliation adjustments and close reconciliations"
    },
    "VIEWER": {
        "services": ["financial_management"],
        "permissions": ["read"],
        "description": "Read-only access to financial data"
    },
    "SERVICE": {
        "services": ["financial_management"],
        "permissions": ["read", "write"],
        "description": "Service account for integration pulls only, cannot post manual entries"
    },
    # Legacy roles (for backward compatibility)
    "finance_head": {
        "services": ["billing", "financial_management"],
        "permissions": ["read", "write", "admin"],
        "description": "Finance head with full access to both services (maps to FINANCE_ADMIN)"
    },
    "regional_finance_manager": {
        "services": ["billing", "financial_management"],
        "permissions": ["read", "write"],
        "description": "Regional finance manager with access to both services (maps to ACCOUNTANT)"
    },
    "accountant": {
        "services": ["financial_management"],
        "permissions": ["read", "write"],
        "description": "Accountant with access to financial management only (maps to ACCOUNTANT)"
    },
    "admin": {
        "services": ["billing"],
        "permissions": ["read", "write", "admin"],
        "description": "Admin with access to billing service only"
    },
    "billing_team": {
        "services": ["billing"],
        "permissions": ["read", "write"],
        "description": "Billing team with access to billing service only"
    },
    "customer_success_manager": {
        "services": ["billing"],
        "permissions": ["read", "write"],
        "description": "Customer Success Manager with access to billing for customer/tenant onboarding and management"
    }
}

# Permission levels
PERMISSIONS = {
    "read": {
        "level": 1,
        "description": "Read-only access"
    },
    "write": {
        "level": 2,
        "description": "Read and write access"
    },
    "admin": {
        "level": 3,
        "description": "Full administrative access"
    }
}


def get_role_services(role: str) -> list:
    """Get services accessible by role"""
    return ROLES.get(role, {}).get("services", [])


def get_role_permissions(role: str) -> list:
    """Get permissions for role"""
    return ROLES.get(role, {}).get("permissions", [])


def can_access_service(role: str, service: str) -> bool:
    """Check if role can access service"""
    services = get_role_services(role)
    return service in services


def has_permission(role: str, permission: str) -> bool:
    """Check if role has permission"""
    permissions = get_role_permissions(role)
    return permission in permissions or "admin" in permissions

