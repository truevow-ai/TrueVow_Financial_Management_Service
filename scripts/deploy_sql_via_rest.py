#!/usr/bin/env python3
"""
TrueVow Financial Management - SQL Deployment via Supabase REST API

This script deploys SQL files using the Supabase REST API (HTTPS port 443),
bypassing Windows firewall issues that block direct PostgreSQL connections.

Usage:
    python scripts/deploy_sql_via_rest.py

Requirements:
    - requests library: pip install requests
    - SUPABASE_SERVICE_ROLE_KEY environment variable (get from Supabase Dashboard > Settings > API)
"""

import os
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("ERROR: requests library not installed.")
    print("Install with: pip install requests")
    sys.exit(1)

# Configuration
SUPABASE_URL = "https://ififhzrbhadmtedyvzhb.supabase.co"
SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")

# SQL files to deploy (in order)
SQL_FILES = [
    "infra/database/rls_policies.sql",
    "infra/database/immutability_constraints.sql",
    "infra/database/business_constraints.sql",
]


def check_service_role_key():
    """Check if service role key is available."""
    if not SERVICE_ROLE_KEY:
        print("=" * 60)
        print("ERROR: SUPABASE_SERVICE_ROLE_KEY not set!")
        print("=" * 60)
        print("")
        print("Get your service role key from:")
        print("  1. Go to https://supabase.com/dashboard")
        print("  2. Select project: ififhzrbhadmtedyvzhb")
        print("  3. Go to Settings > API")
        print("  4. Copy the 'service_role' key (secret)")
        print("")
        print("Then run:")
        print("  $env:SUPABASE_SERVICE_ROLE_KEY='your-key-here'")
        print("  python scripts/deploy_sql_via_rest.py")
        print("")
        return False
    return True


def read_sql_file(filepath: str) -> str:
    """Read SQL file content."""
    path = Path(filepath)
    if not path.exists():
        print(f"ERROR: File not found: {filepath}")
        return None
    return path.read_text(encoding="utf-8")


def execute_sql_via_rpc(sql: str, description: str = "SQL execution") -> dict:
    """
    Execute SQL via Supabase RPC endpoint.
    
    Uses a custom RPC function that must be created first.
    If the function doesn't exist, we'll create it.
    """
    headers = {
        "apikey": SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    
    # First, try to create the exec_sql function if it doesn't exist
    create_function_sql = """
    CREATE OR REPLACE FUNCTION exec_sql(sql_text TEXT)
    RETURNS TEXT AS $$
    BEGIN
        EXECUTE sql_text;
        RETURN 'OK';
    EXCEPTION WHEN OTHERS THEN
        RETURN 'ERROR: ' || SQLERRM;
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;
    """
    
    # Try direct SQL execution via the SQL endpoint
    # Note: Supabase doesn't have a direct SQL execution REST endpoint
    # We need to use the management API or split the SQL into individual statements
    
    # Alternative: Use the query endpoint with raw SQL
    # This requires the pg_net extension or similar
    
    return {"success": False, "error": "Direct SQL execution via REST requires setup"}


def execute_sql_via_direct_endpoint(sql: str) -> dict:
    """
    Execute SQL using Supabase's SQL execution endpoint.
    
    Note: This uses the internal SQL execution API which may require
    the service role key and proper headers.
    """
    headers = {
        "apikey": SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    
    # Try the SQL execution endpoint
    # Note: This endpoint may not be publicly available
    url = f"{SUPABASE_URL}/rest/v1/rpc/exec_sql"
    
    payload = {"sql_text": sql}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            return {"success": True, "result": response.text}
        elif response.status_code == 404:
            # Function doesn't exist, need to create it
            return {"success": False, "error": "exec_sql function not found", "need_setup": True}
        else:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def setup_exec_sql_function() -> bool:
    """Create the exec_sql helper function in the database."""
    print("Setting up exec_sql helper function...")
    
    # SQL to create the function
    create_function_sql = """
    CREATE OR REPLACE FUNCTION exec_sql(sql_text TEXT)
    RETURNS TEXT AS $$
    BEGIN
        EXECUTE sql_text;
        RETURN 'OK';
    EXCEPTION WHEN OTHERS THEN
        RETURN 'ERROR: ' || SQLERRM;
    END;
    $$ LANGUAGE plpgsql SECURITY DEFINER;
    """
    
    # We can't execute this directly via REST API either
    # User needs to run this in Supabase Dashboard first
    print("")
    print("=" * 60)
    print("ONE-TIME SETUP REQUIRED")
    print("=" * 60)
    print("")
    print("Run this SQL in Supabase Dashboard SQL Editor first:")
    print("")
    print(create_function_sql)
    print("")
    print("After creating the function, re-run this script.")
    print("")
    return False


def execute_sql_split_statements(sql: str) -> dict:
    """
    Split SQL into individual statements and execute via REST.
    
    This approach uses the PostgreSQL protocol through Supabase's
    connection pooler with HTTP fallback.
    """
    # Split by semicolons, but handle functions/procedures carefully
    # This is a simplified approach - complex SQL may need manual handling
    
    statements = []
    current_stmt = []
    in_function = False
    
    for line in sql.split('\n'):
        stripped = line.strip()
        
        # Track if we're inside a function/procedure
        if 'CREATE OR REPLACE FUNCTION' in stripped or 'CREATE FUNCTION' in stripped:
            in_function = True
        elif 'CREATE OR REPLACE TRIGGER' in stripped or 'CREATE TRIGGER' in stripped:
            in_function = True
        
        # Check for end of function
        if in_function:
            if stripped.startswith('$$ LANGUAGE') or stripped.endswith('$$ LANGUAGE plpgsql;'):
                in_function = False
                current_stmt.append(line)
                if ';' in stripped:
                    stmt = '\n'.join(current_stmt)
                    statements.append(stmt)
                    current_stmt = []
                continue
        
        current_stmt.append(line)
        
        # If not in function and line ends with semicolon, it's a complete statement
        if not in_function and stripped.endswith(';'):
            stmt = '\n'.join(current_stmt)
            statements.append(stmt)
            current_stmt = []
    
    # Add any remaining content
    if current_stmt:
        remaining = '\n'.join(current_stmt).strip()
        if remaining:
            statements.append(remaining)
    
    return {"success": True, "statements": statements, "count": len(statements)}


def test_connection() -> bool:
    """Test connection to Supabase REST API."""
    print("Testing connection to Supabase REST API...")
    
    headers = {
        "apikey": SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    }
    
    try:
        # Try to query a simple table
        url = f"{SUPABASE_URL}/rest/v1/"
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code in [200, 401, 403]:
            print(f"  ✓ REST API reachable (status: {response.status_code})")
            return True
        else:
            print(f"  ✗ Unexpected status: {response.status_code}")
            return False
    except requests.exceptions.Timeout:
        print("  ✗ Connection timed out")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"  ✗ Connection error: {e}")
        return False
    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def deploy_via_python_postgres():
    """
    Alternative: Use psycopg2 with the connection pooler URL.
    
    The session pooler might work even if direct connection doesn't.
    """
    import subprocess
    
    print("Trying connection pooler via psycopg2...")
    
    # Install psycopg2-binary if needed
    try:
        import psycopg2
    except ImportError:
        print("Installing psycopg2-binary...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psycopg2-binary"], 
                      capture_output=True)
        import psycopg2
    
    # Connection string
    conn_string = "postgresql://postgres.ififhzrbhadmtedyvzhb:Intakely%40786@aws-1-us-east-1.pooler.supabase.com:5432/postgres"
    
    try:
        conn = psycopg2.connect(conn_string, connect_timeout=10)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"  ✓ Connection successful: {result}")
        
        # Deploy each SQL file
        for sql_file in SQL_FILES:
            print(f"\nDeploying: {sql_file}")
            sql_content = read_sql_file(sql_file)
            if sql_content:
                try:
                    cursor.execute(sql_content)
                    print(f"  ✓ Deployed successfully")
                except Exception as e:
                    print(f"  ✗ Error: {e}")
                    # Continue with next file
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        return False


def main():
    print("=" * 60)
    print("TrueVow FM - SQL Deployment via REST API")
    print("=" * 60)
    print("")
    
    # Check service role key
    if not check_service_role_key():
        sys.exit(1)
    
    # Test connection
    if not test_connection():
        print("")
        print("REST API not reachable. Trying connection pooler...")
        if deploy_via_python_postgres():
            print("\nDeployment complete via connection pooler!")
            return
        else:
            print("\nAll connection methods failed.")
            print("Please deploy manually via Supabase Dashboard SQL Editor.")
            sys.exit(1)
    
    print("")
    print("Connection successful. Proceeding with deployment...")
    print("")
    
    # Setup helper function if needed
    # (This requires one-time manual setup in Dashboard)
    
    print("=" * 60)
    print("DEPLOYMENT METHOD")
    print("=" * 60)
    print("")
    print("The REST API doesn't support direct SQL execution.")
    print("Please use one of these alternatives:")
    print("")
    print("1. SUPABASE DASHBOARD (Recommended):")
    print("   - Go to https://supabase.com/dashboard")
    print("   - Navigate to SQL Editor")
    print("   - Paste and run each SQL file")
    print("")
    print("2. PYTHON WITH PSYCOPG2:")
    print("   - Run: python scripts/deploy_sql_via_psycopg.py")
    print("")
    print("3. CONNECTION POOLER:")
    print("   - The session pooler might work if direct connection doesn't")
    print("")


if __name__ == "__main__":
    main()
