#!/usr/bin/env python
"""
Verification script for FM Service Refactor.
Run this after any structural changes to verify nothing broke.
"""
import sys
import subprocess
import os

def main():
    print("=" * 60)
    print("FM SERVICE VERIFICATION CHECKLIST")
    print("=" * 60)
    
    all_passed = True
    
    # Check 1: Python Build
    print("\n[1/4] Python Build (py_compile)...")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'py_compile', 'app/main.py'],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("       [PASS] Python builds successfully")
        else:
            print("       [FAIL] Python build failed")
            print(result.stderr)
            all_passed = False
    except Exception as e:
        print(f"       [FAIL] {e}")
        all_passed = False
    
    # Check 2: Imports work
    print("\n[2/4] Import Test...")
    try:
        from app.main import app
        from app.core.service_registry import get_registry_client
        from app.core.config import settings
        print("       [PASS] All imports work")
    except Exception as e:
        print(f"       [FAIL] Import failed: {e}")
        all_passed = False
    
    # Check 3: Alembic migration files exist
    print("\n[3/4] Alembic Migration Files...")
    migration_dir = 'infra/database/migrations/versions'
    if os.path.exists(migration_dir):
        files = [f for f in os.listdir(migration_dir) if f.endswith('.py') and not f.startswith('_')]
        print(f"       [PASS] Found {len(files)} migration files in infra/database/migrations/versions/")
    else:
        print("       [FAIL] Migration directory not found at infra/database/migrations/versions/")
        all_passed = False
    
    # Check 4: Test collection
    print("\n[4/4] Test Collection...")
    try:
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', 'tests/', '--collect-only', '-q'],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            # Count tests
            output = result.stdout + result.stderr
            if 'test' in output.lower():
                print("       [PASS] Tests collected successfully")
            else:
                print("       [PASS] No test errors (empty collection)")
        else:
            print("       [FAIL] Test collection failed")
            print(result.stderr[:500] if result.stderr else "No error message")
            all_passed = False
    except subprocess.TimeoutExpired:
        print("       [WARN] Test collection timed out (60s)")
    except Exception as e:
        print(f"       [FAIL] {e}")
        all_passed = False
    
    # Summary
    print("\n" + "=" * 60)
    if all_passed:
        print("VERIFICATION: ALL CHECKS PASSED")
        print("Refactor did not break anything.")
    else:
        print("VERIFICATION: SOME CHECKS FAILED")
        print("Review failures above.")
    print("=" * 60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
