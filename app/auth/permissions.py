"""
RBAC Permission Matrix for Financial Management Service
Defines what each role can do for each module/action
"""
from typing import Dict, List

# Permission matrix: {role: {module: [actions]}}
PERMISSION_MATRIX: Dict[str, Dict[str, List[str]]] = {
    "FINANCE_ADMIN": {
        "general_ledger": ["read", "write", "post", "reverse", "close_period", "lock_period", "post_soft_closed"],
        "ap": ["read", "write", "post", "reverse", "override"],
        "ar": ["read", "write", "post", "reverse", "override"],
        "payroll": ["read", "write", "create_run", "calculate", "approve", "post", "reverse", "override"],
        "treasury": ["read", "write", "import", "reconcile", "approve_adjustments", "close_reconciliation", "override"],
        "period_close": ["read", "request_close", "approve_close", "lock"],
        "royalties": ["read", "write", "generate", "approve", "post", "override"],
    },
    "ACCOUNTANT": {
        "general_ledger": ["read", "write", "post", "reverse"],
        "ap": ["read", "write", "post", "reverse"],
        "ar": ["read", "write", "post", "reverse"],
        "payroll": ["read"],
        "treasury": ["read"],
        "period_close": ["read", "request_close"],
        "royalties": ["read", "write", "generate"],
    },
    "PAYROLL_PREPARER": {
        "general_ledger": ["read"],
        "ap": ["read"],
        "ar": ["read"],
        "payroll": ["read", "write", "create_run", "calculate", "submit_approval"],
        "treasury": ["read"],
        "period_close": ["read"],
        "royalties": ["read"],
    },
    "PAYROLL_APPROVER": {
        "general_ledger": ["read"],
        "ap": ["read"],
        "ar": ["read"],
        "payroll": ["read", "approve", "reject", "post"],
        "treasury": ["read"],
        "period_close": ["read"],
        "royalties": ["read"],
    },
    "TREASURY_CLERK": {
        "general_ledger": ["read"],
        "ap": ["read"],
        "ar": ["read"],
        "payroll": ["read"],
        "treasury": ["read", "write", "import", "reconcile", "create_adjustments", "submit_approval"],
        "period_close": ["read"],
        "royalties": ["read"],
    },
    "TREASURY_APPROVER": {
        "general_ledger": ["read"],
        "ap": ["read"],
        "ar": ["read"],
        "payroll": ["read"],
        "treasury": ["read", "approve_adjustments", "reject_adjustments", "post_adjustments", "close_reconciliation"],
        "period_close": ["read"],
        "royalties": ["read"],
    },
    "VIEWER": {
        "general_ledger": ["read"],
        "ap": ["read"],
        "ar": ["read"],
        "payroll": ["read"],
        "treasury": ["read"],
        "period_close": ["read"],
        "royalties": ["read"],
    },
    "SERVICE": {
        "general_ledger": ["read", "write"],
        "ap": ["read"],
        "ar": ["read", "write"],
        "payroll": ["read"],
        "treasury": ["read", "write"],
        "period_close": ["read"],
        "royalties": ["read"],
    },
}


def has_permission(role: str, module: str, action: str) -> bool:
    """Check if a role has permission for a module action."""
    role_mapping = {
        "finance_head": "FINANCE_ADMIN",
        "accountant": "ACCOUNTANT",
        "regional_finance_manager": "ACCOUNTANT",
    }
    role = role_mapping.get(role, role)
    
    if role == "FINANCE_ADMIN":
        return True
    
    role_perms = PERMISSION_MATRIX.get(role, {})
    module_perms = role_perms.get(module, [])
    
    if "admin" in module_perms:
        return True
    
    return action in module_perms


def can_approve(role: str, object_type: str) -> bool:
    """Check if role can approve a specific object type."""
    if object_type == "PAYROLL_RUN":
        return has_permission(role, "payroll", "approve")
    elif object_type == "REC_ADJUSTMENT_BATCH":
        return has_permission(role, "treasury", "approve_adjustments")
    elif object_type == "PERIOD_CLOSE":
        return has_permission(role, "period_close", "approve_close")
    elif object_type == "ROYALTY_RUN":
        return has_permission(role, "royalties", "approve")
    return False


def can_post(role: str, object_type: str) -> bool:
    """Check if role can post a specific object type."""
    if object_type == "PAYROLL_RUN":
        return has_permission(role, "payroll", "post")
    elif object_type == "REC_ADJUSTMENT_BATCH":
        return has_permission(role, "treasury", "post_adjustments")
    elif object_type == "ROYALTY_RUN":
        return has_permission(role, "royalties", "post")
    return False
