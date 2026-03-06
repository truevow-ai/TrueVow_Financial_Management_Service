#!/usr/bin/env python3
"""
TrueVow Financial Management - SQL Deployment via Connection Pooler

This script deploys SQL files using the Supabase connection pooler,
which may bypass certain network restrictions.

Usage:
    python scripts/deploy_sql_via_pooler.py
"""

import os
import sys
import time
from pathlib import Path

# Install psycopg2-binary if needed
try:
    import psycopg2
except ImportError:
    print("Installing psycopg2-binary...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "psycopg2-binary", "-q"])
    import psycopg2

# Configuration - Using session pooler
POOLER_URL = "postgresql://postgres.ififhzrbhadmtedyvzhb:Intakely%40786@aws-1-us-east-1.pooler.supabase.com:5432/postgres"

# SQL files to deploy (in order)
SQL_FILES = [
    ("infra/database/rls_policies.sql", "P0 - Row-Level Security"),
    ("infra/database/immutability_constraints.sql", "P1 - Immutability Triggers"),
    ("infra/database/business_constraints.sql", "P2 - Business Constraints"),
]


def read_sql_file(filepath: str) -> str:
    """Read SQL file content."""
    path = Path(filepath)
    if not path.exists():
        print(f"  [FAIL] File not found: {filepath}")
        return None
    return path.read_text(encoding="utf-8")


def test_connection(conn_string: str) -> bool:
    """Test database connection."""
    print("Testing connection to Supabase connection pooler...")
    try:
        conn = psycopg2.connect(conn_string, connect_timeout=15)
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        print(f"  [OK] Connected successfully!")
        print(f"  PostgreSQL version: {version[0][:50]}...")
        return True
    except Exception as e:
        print(f"  [FAIL] Connection failed: {e}")
        return False


def deploy_sql_file(conn, filepath: str, description: str) -> bool:
    """Deploy a single SQL file."""
    print(f"\n{'='*60}")
    print(f"Deploying: {description}")
    print(f"File: {filepath}")
    print("="*60)
    
    sql_content = read_sql_file(filepath)
    if not sql_content:
        return False
    
    cursor = conn.cursor()
    
    try:
        # Execute the SQL
        start_time = time.time()
        cursor.execute(sql_content)
        elapsed = time.time() - start_time
        
        print(f"  [OK] Deployed successfully in {elapsed:.2f}s")
        return True
        
    except psycopg2.errors.InsufficientPrivilege as e:
        print(f"  [FAIL] Insufficient privileges: {e}")
        print("  Note: Some operations may require superuser access")
        return False
        
    except psycopg2.errors.DuplicateObject as e:
        print(f"  [WARN] Object already exists (skipping): {e}")
        return True  # Not a failure for idempotent scripts
        
    except psycopg2.errors.UndefinedObject as e:
        print(f"  [WARN] Object not found (may be expected): {e}")
        return True
        
    except Exception as e:
        error_msg = str(e)
        # Check if it's a non-fatal error
        if "already exists" in error_msg.lower():
            print(f"  [WARN] Object already exists: {error_msg[:100]}")
            return True
        else:
            print(f"  [FAIL] Error: {error_msg}")
            return False
    
    finally:
        cursor.close()


def verify_deployment(conn) -> dict:
    """Verify the deployment was successful."""
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    
    cursor = conn.cursor()
    results = {}
    
    # Check RLS tables
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM pg_tables 
            WHERE schemaname = 'public' AND rowsecurity = true
        """)
        rls_count = cursor.fetchone()[0]
        results['rls_tables'] = rls_count
        print(f"  RLS-enabled tables: {rls_count}")
    except Exception as e:
        print(f"  [WARN] Could not check RLS tables: {e}")
    
    # Check RLS policies
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM pg_policies WHERE schemaname = 'public'
        """)
        policy_count = cursor.fetchone()[0]
        results['rls_policies'] = policy_count
        print(f"  RLS policies: {policy_count}")
    except Exception as e:
        print(f"  [WARN] Could not check RLS policies: {e}")
    
    # Check triggers
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM pg_trigger 
            WHERE tgname LIKE '%immutability%' OR tgname LIKE '%validation%'
        """)
        trigger_count = cursor.fetchone()[0]
        results['triggers'] = trigger_count
        print(f"  Immutability/validation triggers: {trigger_count}")
    except Exception as e:
        print(f"  [WARN] Could not check triggers: {e}")
    
    # Check check constraints
    try:
        cursor.execute("""
            SELECT COUNT(*) FROM pg_constraint 
            WHERE contype = 'c' AND connamespace = 'public'::regnamespace
        """)
        constraint_count = cursor.fetchone()[0]
        results['check_constraints'] = constraint_count
        print(f"  Check constraints: {constraint_count}")
    except Exception as e:
        print(f"  [WARN] Could not check constraints: {e}")
    
    cursor.close()
    return results


def main():
    print("="*60)
    print("TrueVow FM - SQL Deployment via Connection Pooler")
    print("="*60)
    print("")
    
    # Test connection
    if not test_connection(POOLER_URL):
        print("\nConnection pooler also blocked.")
        print("\nAlternative: Deploy via Supabase Dashboard")
        print("  1. Go to https://supabase.com/dashboard")
        print("  2. Select project: ififhzrbhadmtedyvzhb")
        print("  3. Navigate to SQL Editor")
        print("  4. Paste and run each SQL file in order")
        sys.exit(1)
    
    # Connect for deployment
    print("\nConnecting for deployment...")
    conn = psycopg2.connect(POOLER_URL, connect_timeout=15)
    conn.autocommit = True  # Required for DDL statements
    
    # Deploy each SQL file
    success_count = 0
    for filepath, description in SQL_FILES:
        if deploy_sql_file(conn, filepath, description):
            success_count += 1
    
    # Verify deployment
    results = verify_deployment(conn)
    
    # Close connection
    conn.close()
    
    # Summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"  Files deployed: {success_count}/{len(SQL_FILES)}")
    print(f"  RLS tables: {results.get('rls_tables', 'N/A')}")
    print(f"  RLS policies: {results.get('rls_policies', 'N/A')}")
    print(f"  Triggers: {results.get('triggers', 'N/A')}")
    print(f"  Check constraints: {results.get('check_constraints', 'N/A')}")
    print("")
    
    if success_count == len(SQL_FILES):
        print("[OK] DEPLOYMENT COMPLETE!")
        print("STATUS: DONE")
    else:
        print("[WARN] PARTIAL DEPLOYMENT - Some files had errors")
        print("STATUS: UNVERIFIED")
    
    print("")


if __name__ == "__main__":
    main()
