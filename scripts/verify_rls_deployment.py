#!/usr/bin/env python3
"""Verify RLS deployment."""

import psycopg2

POOLER_URL = "postgresql://postgres.ififhzrbhadmtedyvzhb:Intakely%40786@aws-1-us-east-1.pooler.supabase.com:5432/postgres"

conn = psycopg2.connect(POOLER_URL, connect_timeout=15)
conn.autocommit = True
cursor = conn.cursor()

print("=" * 60)
print("RLS DEPLOYMENT VERIFICATION")
print("=" * 60)

# 1. RLS Tables
cursor.execute("""
    SELECT COUNT(*) FROM pg_tables 
    WHERE schemaname = 'public' AND rowsecurity = true
""")
print(f"\n1. RLS-enabled tables: {cursor.fetchone()[0]}")

# 2. RLS Policies
cursor.execute("""
    SELECT COUNT(*) FROM pg_policies WHERE schemaname = 'public'
""")
print(f"2. RLS policies: {cursor.fetchone()[0]}")

# 3. Immutability Triggers
cursor.execute("""
    SELECT tgname FROM pg_trigger 
    WHERE tgname LIKE '%immutability%' OR tgname LIKE '%validation%'
    ORDER BY tgname
""")
triggers = cursor.fetchall()
print(f"\n3. Immutability/validation triggers ({len(triggers)}):")
for t in triggers:
    print(f"   - {t[0]}")

# 4. Check Constraints
cursor.execute("""
    SELECT COUNT(*) FROM pg_constraint 
    WHERE contype = 'c' AND connamespace = 'public'::regnamespace
""")
print(f"\n4. Check constraints: {cursor.fetchone()[0]}")

# 5. Test RLS helper function
print("\n5. Testing RLS helper function:")
try:
    cursor.execute("SELECT app_current_tenant_id()")
    result = cursor.fetchone()
    print(f"   Function exists, returns: {result[0]} (NULL is expected without tenant set)")
except Exception as e:
    print(f"   Error: {e}")

# 6. Test immutability trigger function
print("\n6. Testing immutability functions:")
for func in ['is_journal_entry_posted', 'is_period_closed_or_locked', 'is_payroll_run_posted']:
    try:
        cursor.execute(f"SELECT {func}(NULL::uuid)")
        print(f"   - {func}(): EXISTS")
    except Exception as e:
        print(f"   - {func}(): ERROR - {e}")

# 7. Sample of RLS policies
print("\n7. Sample RLS policies:")
cursor.execute("""
    SELECT tablename, policyname 
    FROM pg_policies 
    WHERE schemaname = 'public'
    ORDER BY tablename
    LIMIT 10
""")
for row in cursor.fetchall():
    print(f"   - {row[0]}: {row[1]}")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)

cursor.close()
conn.close()
