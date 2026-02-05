"""
Test RBAC Role Enforcement (sec_rbac_001)

Validates:
- FM_ADMIN vs ACCOUNTANT vs VIEWER vs PAYROLL_ADMIN vs AP_CLERK vs AR_CLERK permissions
- Role-based access to modules (GL, AP, AR, Payroll, Treasury)
- Action-level permissions (read, write, post, reverse, approve)
- Legacy role mapping to new RBAC roles
"""

import pytest
from app.auth.roles import ROLES
from app.auth.permissions import PERMISSION_MATRIX


def test_role_definitions_complete():
    """Test all required roles are defined"""
    required_roles = [
        "FINANCE_ADMIN",
        "ACCOUNTANT", 
        "PAYROLL_PREPARER",
        "PAYROLL_APPROVER",
        "TREASURY_CLERK",
        "TREASURY_APPROVER",
        "VIEWER",
        "SERVICE"
    ]
    
    for role in required_roles:
        assert role in ROLES, f"Role {role} not defined"
        role_def = ROLES[role]
        assert "services" in role_def
        assert "permissions" in role_def
        assert "description" in role_def


def test_finance_admin_permissions():
    """Test FINANCE_ADMIN has full access"""
    role = "FINANCE_ADMIN"
    assert role in PERMISSION_MATRIX
    
    permissions = PERMISSION_MATRIX[role]
    
    # Should have all modules
    required_modules = ["general_ledger", "ap", "ar", "payroll", "treasury", "period_close", "royalties"]
    for module in required_modules:
        assert module in permissions, f"FINANCE_ADMIN missing {module} permissions"
    
    # Should have highest level permissions
    gl_perms = permissions["general_ledger"]
    assert "read" in gl_perms
    assert "write" in gl_perms
    assert "post" in gl_perms
    assert "reverse" in gl_perms
    assert "close_period" in gl_perms
    assert "lock_period" in gl_perms
    assert "post_soft_closed" in gl_perms


def test_accountant_permissions():
    """Test ACCOUNTANT has appropriate access"""
    role = "ACCOUNTANT"
    assert role in PERMISSION_MATRIX
    
    permissions = PERMISSION_MATRIX[role]
    
    # Should have read/write access to core modules
    assert "general_ledger" in permissions
    assert "ap" in permissions
    assert "ar" in permissions
    assert "payroll" in permissions  # Read-only
    assert "treasury" in permissions  # Read-only
    
    # GL permissions - should be able to post but not close periods
    gl_perms = permissions["general_ledger"]
    assert "read" in gl_perms
    assert "write" in gl_perms
    assert "post" in gl_perms
    assert "reverse" in gl_perms
    assert "close_period" not in gl_perms  # No period closing
    assert "lock_period" not in gl_perms   # No period locking


def test_viewer_permissions():
    """Test VIEWER has read-only access"""
    role = "VIEWER"
    assert role in PERMISSION_MATRIX
    
    permissions = PERMISSION_MATRIX[role]
    
    # Should have all modules but only read access
    required_modules = ["general_ledger", "ap", "ar", "payroll", "treasury", "period_close", "royalties"]
    for module in required_modules:
        assert module in permissions, f"VIEWER missing {module}"
        assert permissions[module] == ["read"], f"VIEWER should only have read access to {module}"


def test_payroll_preparer_permissions():
    """Test PAYROLL_PREPARER can create/calculate but not post"""
    role = "PAYROLL_PREPARER"
    assert role in PERMISSION_MATRIX
    
    permissions = PERMISSION_MATRIX[role]
    
    # Limited access to most modules
    assert permissions["general_ledger"] == ["read"]
    assert permissions["ap"] == ["read"]
    assert permissions["ar"] == ["read"]
    assert permissions["treasury"] == ["read"]
    assert permissions["period_close"] == ["read"]
    assert permissions["royalties"] == ["read"]
    
    # Payroll specific permissions
    payroll_perms = permissions["payroll"]
    assert "read" in payroll_perms
    assert "write" in payroll_perms
    assert "create_run" in payroll_perms
    assert "calculate" in payroll_perms
    assert "submit_approval" in payroll_perms
    assert "post" not in payroll_perms  # Cannot post
    assert "approve" not in payroll_perms  # Cannot approve


def test_payroll_approver_permissions():
    """Test PAYROLL_APPROVER can approve and post payroll"""
    role = "PAYROLL_APPROVER"
    assert role in PERMISSION_MATRIX
    
    permissions = PERMISSION_MATRIX[role]
    
    # Read-only access to non-payroll modules
    assert permissions["general_ledger"] == ["read"]
    assert permissions["ap"] == ["read"]
    assert permissions["ar"] == ["read"]
    assert permissions["treasury"] == ["read"]
    assert permissions["period_close"] == ["read"]
    assert permissions["royalties"] == ["read"]
    
    # Payroll approval permissions
    payroll_perms = permissions["payroll"]
    assert "read" in payroll_perms
    assert "approve" in payroll_perms
    assert "reject" in payroll_perms
    assert "post" in payroll_perms
    assert "write" not in payroll_perms  # Cannot create runs


def test_treasury_clerk_permissions():
    """Test TREASURY_CLERK can import and reconcile but not approve"""
    role = "TREASURY_CLERK"
    assert role in PERMISSION_MATRIX
    
    permissions = PERMISSION_MATRIX[role]
    
    # Read-only access to non-treasury modules
    non_treasury = ["general_ledger", "ap", "ar", "payroll", "period_close", "royalties"]
    for module in non_treasury:
        assert permissions[module] == ["read"], f"TREASURY_CLERK should only read {module}"
    
    # Treasury specific permissions
    treasury_perms = permissions["treasury"]
    assert "read" in treasury_perms
    assert "write" in treasury_perms
    assert "import" in treasury_perms
    assert "reconcile" in treasury_perms
    assert "create_adjustments" in treasury_perms
    assert "submit_approval" in treasury_perms
    assert "approve_adjustments" not in treasury_perms  # Cannot approve
    assert "post_adjustments" not in treasury_perms     # Cannot post


def test_treasury_approver_permissions():
    """Test TREASURY_APPROVER can approve adjustments and close reconciliations"""
    role = "TREASURY_APPROVER"
    assert role in PERMISSION_MATRIX
    
    permissions = PERMISSION_MATRIX[role]
    
    # Read-only access to non-treasury modules
    non_treasury = ["general_ledger", "ap", "ar", "payroll", "period_close", "royalties"]
    for module in non_treasury:
        assert permissions[module] == ["read"], f"TREASURY_APPROVER should only read {module}"
    
    # Treasury approval permissions
    treasury_perms = permissions["treasury"]
    assert "read" in treasury_perms
    assert "approve_adjustments" in treasury_perms
    assert "reject_adjustments" in treasury_perms
    assert "post_adjustments" in treasury_perms
    assert "close_reconciliation" in treasury_perms
    assert "write" not in treasury_perms  # Cannot create entries
    assert "import" not in treasury_perms  # Cannot import


def test_service_account_permissions():
    """Test SERVICE account has limited write access for integration"""
    role = "SERVICE"
    assert role in PERMISSION_MATRIX
    
    permissions = PERMISSION_MATRIX[role]
    
    # Limited write access for integration
    assert "write" in permissions["general_ledger"]  # Can write GL entries
    assert "write" in permissions["ar"]              # Can write AR entries
    assert "write" in permissions["treasury"]        # Can write treasury data
    
    # Cannot post manual entries
    assert "post" not in permissions["general_ledger"]
    assert "post" not in permissions["ar"]
    assert "post" not in permissions["treasury"]


def test_legacy_role_mapping():
    """Test legacy roles map to new RBAC roles"""
    # finance_head -> FINANCE_ADMIN
    assert "finance_head" in ROLES
    finance_head = ROLES["finance_head"]
    assert finance_head["services"] == ["billing", "financial_management"]
    assert "admin" in finance_head["permissions"]
    
    # regional_finance_manager -> ACCOUNTANT
    assert "regional_finance_manager" in ROLES
    rfm = ROLES["regional_finance_manager"]
    assert rfm["services"] == ["billing", "financial_management"]
    assert rfm["permissions"] == ["read", "write"]
    assert "admin" not in rfm["permissions"]
    
    # accountant -> ACCOUNTANT
    assert "accountant" in ROLES
    acct = ROLES["accountant"]
    assert acct["services"] == ["financial_management"]
    assert acct["permissions"] == ["read", "write"]
    assert "admin" not in acct["permissions"]


def test_role_service_scoping():
    """Test roles are properly scoped to services"""
    # FM roles should only access financial_management
    fm_roles = ["ACCOUNTANT", "PAYROLL_PREPARER", "PAYROLL_APPROVER", "TREASURY_CLERK", "TREASURY_APPROVER", "VIEWER", "SERVICE"]
    
    for role in fm_roles:
        assert role in ROLES
        role_def = ROLES[role]
        assert "financial_management" in role_def["services"]
        assert "billing" not in role_def["services"] or role == "SERVICE"  # SERVICE can access both


def test_permission_granularity():
    """Test permission granularity is appropriate for each role"""
    # ADMIN roles should have override permissions
    admin_perms = PERMISSION_MATRIX["FINANCE_ADMIN"]["general_ledger"]
    assert "post_soft_closed" in admin_perms  # Override capability
    
    # Non-admin roles should not have override permissions
    accountant_perms = PERMISSION_MATRIX["ACCOUNTANT"]["general_ledger"]
    assert "post_soft_closed" not in accountant_perms
    
    viewer_perms = PERMISSION_MATRIX["VIEWER"]["general_ledger"]
    assert viewer_perms == ["read"]  # Only read access