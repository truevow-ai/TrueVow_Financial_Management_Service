#!/usr/bin/env python3
"""Check existing RLS policies and triggers before re-deployment"""
import asyncio, asyncpg, os
from dotenv import load_dotenv

load_dotenv()
load_dotenv('.env.local')
url = os.getenv('FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL', '').replace('postgresql+asyncpg://', 'postgresql://')

async def main():
    conn = await asyncpg.connect(url, timeout=10)

    rows = await conn.fetch("""
        SELECT tablename, policyname
        FROM pg_policies WHERE schemaname='public'
        ORDER BY tablename, policyname
    """)
    print("EXISTING RLS POLICIES:")
    for r in rows:
        print(f"  {r['tablename']}: {r['policyname']}")

    rows2 = await conn.fetch("""
        SELECT event_object_table, trigger_name
        FROM information_schema.triggers
        WHERE trigger_schema='public'
          AND trigger_name IN (
            'journal_entry_immutability','journal_line_immutability',
            'accounting_period_status_transition','accounting_period_no_overlap',
            'payroll_run_immutability','ar_invoice_timestamps','ap_bill_timestamps'
          )
        ORDER BY event_object_table
    """)
    print("\nIMMUTABILITY TRIGGERS (DISTINCT):")
    seen = set()
    for r in rows2:
        key = (r['event_object_table'], r['trigger_name'])
        if key not in seen:
            print(f"  {r['event_object_table']}: {r['trigger_name']}")
            seen.add(key)

    rls_rows = await conn.fetch("""
        SELECT tablename, rowsecurity
        FROM pg_tables WHERE schemaname='public'
        ORDER BY tablename
    """)
    print("\nRLS STATUS PER TABLE:")
    for r in rls_rows:
        icon = 'ON ' if r['rowsecurity'] else 'off'
        print(f"  [{icon}] {r['tablename']}")

    await conn.close()

asyncio.run(main())
