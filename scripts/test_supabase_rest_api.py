#!/usr/bin/env python3
"""
Test Supabase REST API Connection
This bypasses PostgreSQL port 5432 and uses HTTPS (port 443) instead.
"""
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
load_dotenv('.env.local')

# Supabase Financial Management credentials
PROJECT_URL = os.getenv('FINANCIAL_MANAGEMENT_PROJECT_URL', 'https://ififhzrbhadmtedyvzhb.supabase.co')
ANON_KEY = os.getenv('FINANCIAL_MANAGEMENT_ANON_KEY')
SERVICE_ROLE_KEY = os.getenv('FINANCIAL_MANAGEMENT_SECRET_ROLE_KEY')

print("=" * 80)
print("SUPABASE REST API CONNECTION TEST")
print("=" * 80)
print(f"Project URL: {PROJECT_URL}")
print(f"Using Service Role Key: {SERVICE_ROLE_KEY[:20]}..." if SERVICE_ROLE_KEY else "No service role key")
print()

# Test 1: Check if we can reach Supabase REST API
print("TEST 1: Basic connectivity to Supabase REST API")
print("-" * 80)
try:
    response = requests.get(f"{PROJECT_URL}/rest/v1/", timeout=10)
    print(f"✅ REST API reachable: {response.status_code}")
    print(f"Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("\nThis means HTTPS (port 443) is also blocked on your network.")
    exit(1)

print()

# Test 2: List tables using REST API
print("TEST 2: Query existing tables")
print("-" * 80)
headers = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
}

try:
    # Try to query information_schema.tables
    response = requests.get(
        f"{PROJECT_URL}/rest/v1/",
        headers=headers,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text[:500]}")
    
    if response.status_code == 200:
        print("✅ Successfully authenticated with Supabase REST API!")
    else:
        print(f"⚠️ Got response but status code: {response.status_code}")
        
except Exception as e:
    print(f"❌ Query failed: {e}")

print()

# Test 3: Try to query a specific table (legal_entity)
print("TEST 3: Check if legal_entity table exists")
print("-" * 80)
try:
    response = requests.get(
        f"{PROJECT_URL}/rest/v1/legal_entity?select=*&limit=1",
        headers=headers,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ legal_entity table exists! Found {len(data)} records")
        if data:
            print(f"Sample record: {data[0]}")
    elif response.status_code == 404:
        print("⚠️ legal_entity table does not exist yet (migrations not run)")
    else:
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"❌ Query failed: {e}")

print()

# Test 4: Check alembic_version table
print("TEST 4: Check if alembic_version table exists (migration status)")
print("-" * 80)
try:
    response = requests.get(
        f"{PROJECT_URL}/rest/v1/alembic_version?select=*",
        headers=headers,
        timeout=10
    )
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        if data:
            print(f"✅ Migrations have been run! Current version: {data[0].get('version_num')}")
        else:
            print("⚠️ alembic_version table exists but is empty (no migrations run yet)")
    elif response.status_code == 404:
        print("⚠️ alembic_version table does not exist (migrations never run)")
    else:
        print(f"Response: {response.text[:500]}")
        
except Exception as e:
    print(f"❌ Query failed: {e}")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print("If all tests passed, REST API is working!")
print("We can use Supabase REST API to:")
print("  - Check table existence")
print("  - Query data")
print("  - Insert/update/delete records")
print()
print("However, to run Alembic migrations, we still need PostgreSQL access.")
print("Alternative: Generate SQL migration scripts and apply via Supabase Dashboard.")
print("=" * 80)
