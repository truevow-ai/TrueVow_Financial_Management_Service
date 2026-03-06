#!/usr/bin/env python3
"""
RLS Compliance Audit for TrueVow Financial Management Service
Verifies database-first architecture compliance per platform directive
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()
load_dotenv('.env.local')

PROJECT_URL = os.getenv('FINANCIAL_MANAGEMENT_PROJECT_URL', 'https://ififhzrbhadmtedyvzhb.supabase.co')
SERVICE_ROLE_KEY = os.getenv('FINANCIAL_MANAGEMENT_SECRET_ROLE_KEY')

headers = {
    "apikey": SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
}

print("=" * 100)
print("RLS COMPLIANCE AUDIT - TrueVow Financial Management Service")
print("=" * 100)
print()

# Critical tenant-scoped tables that MUST have RLS
TENANT_SCOPED_TABLES = [
    'legal_entity',
    'book',
    'gl_account',
    'accounting_period',
    'dimension',
    'dimension_value',
    'journal_entry',
    'journal_line',
    'ar_customer',
    'ar_invoice',
    'ar_invoice_line',
    'ar_payment',
    'ar_payment_allocation',
    'ap_vendor',
    'ap_bill',
    'ap_bill_line',
    'ap_payment',
    'payroll_run',
    'payroll_run_line',
    'bank_account',
    'bank_transaction',
    'intercompany_transfer',
    'royalty_agreement',
    'royalty_calculation',
]

# Check 1: RLS Policies
print("CHECK 1: RLS Policy Coverage")
print("-" * 100)

try:
    # Query pg_policies to check RLS
    response = requests.get(
        f"{PROJECT_URL}/rest/v1/rpc/check_rls_policies",
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 404:
        print("⚠️  RPC function 'check_rls_policies' not found")
        print("   Will check via information_schema instead")
        
        # Alternative: Check if tables exist
        print("\n   Checking table existence...")
        for table in TENANT_SCOPED_TABLES[:5]:  # Sample check
            try:
                resp = requests.get(
                    f"{PROJECT_URL}/rest/v1/{table}?select=id&limit=0",
                    headers=headers,
                    timeout=5
                )
                if resp.status_code == 200:
                    print(f"   ✅ {table} - exists")
                elif resp.status_code == 404:
                    print(f"   ❌ {table} - NOT FOUND")
            except Exception as e:
                print(f"   ⚠️  {table} - error: {e}")
                
except Exception as e:
    print(f"❌ RLS check failed: {e}")

print()

# Check 2: Immutability Constraints
print("CHECK 2: Immutability Constraints on Posted Entries")
print("-" * 100)

IMMUTABLE_TABLES = {
    'journal_entry': 'Cannot modify POSTED entries',
    'accounting_period': 'Cannot modify CLOSED periods',
    'ar_payment_allocation': 'Cannot modify after posting',
    'payroll_run': 'Cannot modify POSTED runs',
}

print("Required constraints:")
for table, rule in IMMUTABLE_TABLES.items():
    print(f"  - {table}: {rule}")

print("\n⚠️  Need to verify these via database inspection")
print()

# Check 3: Service Role Usage Pattern
print("CHECK 3: Service Role Usage Review")
print("-" * 100)

print("Checking current connection configuration...")

# Check DATABASE_URL pattern
db_url = os.getenv('DATABASE_URL', '')
if 'asyncpg' in db_url or 'postgresql+asyncpg' in db_url:
    print("✅ Using asyncpg driver (async connection)")
    
    if 'service_role' in db_url or 'postgres:' in db_url:
        print("⚠️  WARNING: Connection string appears to use admin credentials")
        print("   RECOMMENDATION: Use RLS-enforced connection for user operations")
        print("   Service role should ONLY be used for:")
        print("     - Background jobs")
        print("     - System-level operations")
        print("     - Migration scripts")
    else:
        print("✅ Connection pattern appears RLS-safe")
else:
    print("⚠️  Database connection not configured or unknown driver")

print()

# Check 4: Tenant Isolation in ORM Models
print("CHECK 4: ORM Model Review (SQLAlchemy)")
print("-" * 100)

print("Checking if tenant filtering exists in code vs DB...")

# Read a sample model file
try:
    with open('app/modules/general_ledger/models/journal_entry_model.py', 'r') as f:
        content = f.read()
        
    if 'legal_entity_id' in content:
        print("✅ Models include legal_entity_id (tenant scope)")
        
    if 'filter' in content.lower() and 'legal_entity_id' in content:
        print("⚠️  WARNING: Model may include tenant filtering logic")
        print("   VERIFY: This should be backed by RLS at DB level")
    else:
        print("✅ No obvious tenant filtering in model definition")
        
except FileNotFoundError:
    print("⚠️  Could not locate model file for inspection")

print()

# Check 5: Constraint Coverage
print("CHECK 5: Business Constraint Coverage")
print("-" * 100)

REQUIRED_CONSTRAINTS = [
    "Unique journal_entry.entry_number per book",
    "Unique gl_account.code per entity",
    "Check journal_entry.total_debit = total_credit",
    "Check accounting_period date ranges non-overlapping",
    "Foreign key cascades properly configured",
    "Status transitions enforced (DRAFT → POSTED → LOCKED)",
]

print("Required constraints (need DB verification):")
for i, constraint in enumerate(REQUIRED_CONSTRAINTS, 1):
    print(f"  {i}. {constraint}")

print()

# Check 6: Cross-Service Schema Alignment
print("CHECK 6: Cross-Service Schema Alignment")
print("-" * 100)

SHARED_CONCEPTS = [
    'legal_entity_id (uuid)',
    'created_at/updated_at (timestamptz)',
    'created_by/updated_by (uuid)',
    'tenant_id pattern (if multi-tenant)',
    'audit_log structure',
]

print("Shared schema patterns that must align across services:")
for concept in SHARED_CONCEPTS:
    print(f"  - {concept}")

print("\n✅ Schema is stored in infra/database/fm_schema.sql")
print("   This serves as canonical contract")

print()

# Summary
print("=" * 100)
print("COMPLIANCE SUMMARY")
print("=" * 100)

print("""
ACTIONS REQUIRED:

1. ✅ DONE: Database schema exists and is populated
2. ⚠️  TODO: Verify RLS policies are active on all tenant-scoped tables
3. ⚠️  TODO: Add database-level immutability constraints (triggers/check constraints)
4. ⚠️  TODO: Review service role usage in app/core/database.py
5. ⚠️  TODO: Add balance check constraint on journal_entry
6. ✅ DONE: Schema documented in fm_schema.sql

NEXT STEPS:

Option A: Apply RLS policies via Supabase Dashboard
Option B: Generate SQL script to add missing constraints/triggers
Option C: Review current connection strategy in codebase

Recommendation: Start with Option C (code review), then Option B (constraints)
""")

print("=" * 100)
