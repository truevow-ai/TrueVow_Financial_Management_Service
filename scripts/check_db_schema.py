#!/usr/bin/env python3
"""Quick check of database schema."""

import psycopg2

POOLER_URL = "postgresql://postgres.ififhzrbhadmtedyvzhb:Intakely%40786@aws-1-us-east-1.pooler.supabase.com:5432/postgres"

conn = psycopg2.connect(POOLER_URL, connect_timeout=15)
conn.autocommit = True
cursor = conn.cursor()

# Check accounting_period columns
print("=== accounting_period columns ===")
cursor.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'accounting_period'
    ORDER BY ordinal_position
""")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]}")

# Check if table exists
print("\n=== Tables count ===")
cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
print(f"  Total tables: {cursor.fetchone()[0]}")

cursor.close()
conn.close()
