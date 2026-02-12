#!/usr/bin/env python3
"""
Row Version 409 Audit Script
Scans routes, schemas, and services to verify row_version implementation

Usage:
    python scripts/audit_row_version.py > docs/01-main/ROW_VERSION_PROOF_TABLE_AUTO.md
"""
import sys
import re
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Endpoints to audit
ENDPOINTS = [
    # Payroll
    ("POST", "/books/{book_id}/payroll/runs/{run_id}/submit-approval", "payroll", "submit-approval", "PayrollRunSubmitApprovalRequest", "PayrollApprovalService", "submit_for_approval"),
    ("POST", "/books/{book_id}/payroll/runs/{run_id}/approve", "payroll", "approve", "PayrollRunApproveRequest", "PayrollApprovalService", "approve"),
    ("POST", "/books/{book_id}/payroll/runs/{run_id}/reject", "payroll", "reject", "PayrollRunRejectRequest", "PayrollApprovalService", "reject"),
    ("POST", "/books/{book_id}/payroll/runs/{run_id}/post", "payroll", "post", "PayrollRunPostRequest", "PayrollRunService", "post_run"),
    # AP Bills
    ("POST", "/books/{book_id}/ap/bills/{bill_id}/submit-approval", "ap", "submit-approval", "APBillSubmitApprovalRequest", "APBillApprovalService", "submit_for_approval"),
    ("POST", "/books/{book_id}/ap/bills/{bill_id}/approve", "ap", "approve", "APBillApproveRequest", "APBillApprovalService", "approve"),
    ("POST", "/books/{book_id}/ap/bills/{bill_id}/reject", "ap", "reject", "APBillRejectRequest", "APBillApprovalService", "reject"),
    ("POST", "/books/{book_id}/ap/bills/{bill_id}/post", "ap", "post", "APBillPostRequest", "APBillPostingService", "post_bill"),
    # Reconciliation
    ("POST", "/books/{book_id}/reconciliations/{rec_id}/adjustments/submit-approval", "reconciliation", "submit-approval", "ReconciliationAdjustmentSubmitRequest", "ReconciliationApprovalService", "submit_for_approval"),
    ("POST", "/books/{book_id}/reconciliations/{rec_id}/adjustments/approve", "reconciliation", "approve", "ReconciliationAdjustmentApproveRequest", "ReconciliationApprovalService", "approve"),
    ("POST", "/books/{book_id}/reconciliations/{rec_id}/adjustments/reject", "reconciliation", "reject", "ReconciliationAdjustmentRejectRequest", "ReconciliationApprovalService", "reject"),
    ("POST", "/books/{book_id}/reconciliations/{rec_id}/adjustments/post", "reconciliation", "post", "ReconciliationAdjustmentPostRequest", "ReconciliationAdjustmentPostingService", "post_adjustment_batch"),
    # Period
    ("POST", "/books/{book_id}/periods/{period_id}/submit-close", "period", "submit-close", "PeriodCloseSubmitRequest", "PeriodCloseApprovalService", "submit_close"),
    ("POST", "/books/{book_id}/periods/{period_id}/approve-close", "period", "approve-close", "PeriodCloseApproveRequest", "PeriodCloseApprovalService", "approve_close"),
    # Royalties
    ("POST", "/books/{book_id}/intercompany/royalties/runs/{run_id}/submit-approval", "royalty", "submit-approval", "RoyaltyRunSubmitApprovalRequest", "RoyaltyApprovalService", "submit_for_approval"),
    ("POST", "/books/{book_id}/intercompany/royalties/runs/{run_id}/approve", "royalty", "approve", "RoyaltyRunApproveRequest", "RoyaltyApprovalService", "approve"),
    ("POST", "/books/{book_id}/intercompany/royalties/runs/{run_id}/reject", "royalty", "reject", "RoyaltyRunRejectRequest", "RoyaltyApprovalService", "reject"),
]


def find_schema_file(module: str) -> Optional[Path]:
    """Find schema file for module"""
    schema_paths = {
        "payroll": "app/modules/payroll/schemas/payroll_run_schemas.py",
        "ap": "app/modules/ap/schemas/ap_bill_schemas.py",
        "reconciliation": "app/modules/general_ledger/schemas/reconciliation_schemas.py",
        "period": "app/modules/general_ledger/schemas/period_schemas.py",
        "royalty": "app/modules/intercompany/schemas/intercompany_schemas.py",
    }
    path = project_root / schema_paths.get(module)
    return path if path.exists() else None


def find_route_file(module: str) -> Optional[Path]:
    """Find route file for module"""
    route_paths = {
        "payroll": "app/modules/payroll/api/routes/payroll_run_routes.py",
        "ap": "app/modules/ap/api/routes/ap_bill_routes.py",
        "reconciliation": "app/modules/general_ledger/api/routes/reconciliation_routes.py",
        "period": "app/modules/general_ledger/api/routes/period_routes.py",
        "royalty": "app/modules/intercompany/api/routes/royalty_routes.py",
    }
    path = project_root / route_paths.get(module)
    return path if path.exists() else None


def find_service_file(module: str, service_class: str) -> Optional[Path]:
    """Find service file"""
    service_paths = {
        "PayrollApprovalService": "app/modules/payroll/services/payroll_approval_service.py",
        "PayrollRunService": "app/modules/payroll/services/payroll_run_service.py",
        "APBillApprovalService": "app/modules/ap/services/ap_bill_approval_service.py",
        "APBillPostingService": "app/modules/ap/services/ap_bill_posting_service.py",
        "ReconciliationApprovalService": "app/modules/general_ledger/services/reconciliation_approval_service.py",
        "ReconciliationAdjustmentPostingService": "app/modules/general_ledger/services/reconciliation_adjustment_posting_service.py",
        "PeriodCloseApprovalService": "app/modules/general_ledger/services/period_close_approval_service.py",
        "RoyaltyApprovalService": "app/modules/intercompany/services/royalty_approval_service.py",
    }
    path = project_root / service_paths.get(service_class)
    return path if path.exists() else None


def check_schema_has_row_version(schema_file: Path, schema_name: str) -> Tuple[bool, Optional[int]]:
    """Check if schema has row_version field"""
    if not schema_file.exists():
        return False, None
    
    content = schema_file.read_text()
    
    # Find schema class
    pattern = rf"class {schema_name}\(BaseModel\):.*?(?=class |\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return False, None
    
    schema_content = match.group(0)
    
    # Check for row_version: int
    if re.search(r"row_version\s*:\s*int", schema_content):
        # Find line number
        lines = content[:match.start()].split('\n')
        line_num = len(lines)
        # Find row_version line within schema
        schema_lines = schema_content.split('\n')
        for i, line in enumerate(schema_lines):
            if re.search(r"row_version\s*:\s*int", line):
                return True, line_num + i + 1
    
    return False, None


def check_route_passes_row_version(route_file: Path, action: str) -> Tuple[bool, Optional[int]]:
    """Check if route passes row_version to service"""
    if not route_file.exists():
        return False, None
    
    content = route_file.read_text()
    
    # Find route handler (look for action in function name or route decorator)
    # Pattern: async def {action}_... or @router.post(...) with action in path
    pattern = rf"async def .*{action}.*?row_version.*?request\.row_version"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        line_num = content[:match.start()].count('\n') + 1
        return True, line_num
    
    # Also check for explicit row_version=request.row_version
    if re.search(rf"row_version\s*=\s*request\.row_version", content):
        # Find line number
        for i, line in enumerate(content.split('\n'), 1):
            if re.search(rf"row_version\s*=\s*request\.row_version", line):
                return True, i
    
    return False, None


def check_service_validates_row_version(service_file: Path, method_name: str) -> Tuple[bool, Optional[int], str]:
    """Check if service validates row_version"""
    if not service_file.exists():
        return False, None, "file not found"
    
    content = service_file.read_text()
    
    # Find method
    pattern = rf"async def {method_name}\(.*?\):.*?(?=async def |def |\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if not match:
        return False, None, "method not found"
    
    method_content = match.group(0)
    
    # Check for check_row_version() call
    if re.search(r"check_row_version\(", method_content):
        line_num = content[:match.start()].count('\n') + 1
        for i, line in enumerate(method_content.split('\n'), 1):
            if "check_row_version(" in line:
                return True, line_num + i, "check_row_version()"
    
    # Check for inline validation
    if re.search(r"row_version.*!=.*row_version|if.*row_version.*!=|HTTPException.*409", method_content):
        line_num = content[:match.start()].count('\n') + 1
        for i, line in enumerate(method_content.split('\n'), 1):
            if re.search(r"row_version.*!=|HTTPException.*409|status_code.*409", line):
                return True, line_num + i, "inline check"
    
    return False, None, "no validation found"


def audit_endpoint(endpoint: Tuple) -> Dict:
    """Audit a single endpoint"""
    method, path, module, action, schema_name, service_class, method_name = endpoint
    
    schema_file = find_schema_file(module)
    route_file = find_route_file(module)
    service_file = find_service_file(module, service_class)
    
    schema_has, schema_line = check_schema_has_row_version(schema_file, schema_name) if schema_file else (False, None)
    route_passes, route_line = check_route_passes_row_version(route_file, action) if route_file else (False, None)
    service_validates, service_line, validation_type = check_service_validates_row_version(service_file, method_name) if service_file else (False, None, "file not found")
    
    status = "✅ COMPLETE" if (schema_has and route_passes and service_validates) else "❌ MISSING"
    
    return {
        "method": method,
        "path": path,
        "module": module,
        "action": action,
        "schema_name": schema_name,
        "service_class": service_class,
        "method_name": method_name,
        "schema_file": str(schema_file) if schema_file else "NOT FOUND",
        "schema_has": schema_has,
        "schema_line": schema_line,
        "route_file": str(route_file) if route_file else "NOT FOUND",
        "route_passes": route_passes,
        "route_line": route_line,
        "service_file": str(service_file) if service_file else "NOT FOUND",
        "service_validates": service_validates,
        "service_line": service_line,
        "validation_type": validation_type,
        "status": status
    }


def main():
    """Main audit function"""
    results = []
    
    for endpoint in ENDPOINTS:
        result = audit_endpoint(endpoint)
        results.append(result)
    
    # Generate markdown table
    print("# Row Version 409 Audit - Auto-Generated")
    print()
    print("**Date:** Auto-generated from code scan")
    print("**Purpose:** Automated verification of row_version implementation")
    print()
    print("---")
    print()
    print("## Endpoint Audit Results")
    print()
    print("| Method | Path | Schema | Route | Service | Status |")
    print("|--------|------|--------|------|---------|--------|")
    
    complete_count = 0
    missing_count = 0
    
    for r in results:
        schema_status = "[OK]" if r["schema_has"] else "[MISSING]"
        route_status = "[OK]" if r["route_passes"] else "[MISSING]"
        service_status = "[OK]" if r["service_validates"] else "[MISSING]"
        
        if r["status"] == "✅ COMPLETE":
            status_display = "[COMPLETE]"
        else:
            status_display = "[MISSING]"
        
        if r["status"] == "✅ COMPLETE":
            complete_count += 1
        else:
            missing_count += 1
        
        print(f"| {r['method']} | `{r['path']}` | {schema_status} | {route_status} | {service_status} | {status_display} |")
    
    print()
    print("## Detailed Results")
    print()
    
    for r in results:
        print(f"### {r['method']} {r['path']}")
        print()
        print(f"- **Schema:** `{r['schema_name']}`")
        if r["schema_file"] != "NOT FOUND":
            print(f"  - File: `{r['schema_file']}`")
            if r["schema_has"]:
                print(f"  - Status: [OK] Has `row_version: int` at line {r['schema_line']}")
            else:
                print(f"  - Status: [MISSING] Missing `row_version: int`")
        else:
            print(f"  - Status: [MISSING] Schema file not found")
        
        print(f"- **Route:** `{r['action']}`")
        if r["route_file"] != "NOT FOUND":
            print(f"  - File: `{r['route_file']}`")
            if r["route_passes"]:
                print(f"  - Status: [OK] Passes `row_version=request.row_version` at line {r['route_line']}")
            else:
                print(f"  - Status: [MISSING] Does not pass row_version")
        else:
            print(f"  - Status: [MISSING] Route file not found")
        
        print(f"- **Service:** `{r['service_class']}.{r['method_name']}()`")
        if r["service_file"] != "NOT FOUND":
            print(f"  - File: `{r['service_file']}`")
            if r["service_validates"]:
                print(f"  - Status: [OK] Validates row_version at line {r['service_line']} ({r['validation_type']})")
            else:
                print(f"  - Status: [MISSING] No row_version validation found")
        else:
            print(f"  - Status: [MISSING] Service file not found")
        
        print()
    
    print("## Summary")
    print()
    print(f"- **Total Endpoints:** {len(results)}")
    print(f"- **Complete:** {complete_count} ✅")
    print(f"- **Missing:** {missing_count} ❌")
    print()
    
    if missing_count == 0:
        print("**Status:** [COMPLETE] ALL ENDPOINTS COMPLETE")
    else:
        print(f"**Status:** [INCOMPLETE] {missing_count} ENDPOINTS NEED FIXES")


if __name__ == "__main__":
    main()
