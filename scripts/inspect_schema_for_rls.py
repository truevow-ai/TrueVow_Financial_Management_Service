#!/usr/bin/env python3
"""Dump real column names for all tables needed for RLS policy regeneration"""
import asyncio, asyncpg, os
from dotenv import load_dotenv

load_dotenv()
load_dotenv('.env.local')
url = os.getenv('FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL', '').replace('postgresql+asyncpg://', 'postgresql://')

TABLES = [
    'gl_account', 'accounting_period', 'dimension', 'dimension_value',
    'ar_invoice', 'ar_invoice_line', 'ar_payment', 'ar_allocation',
    'ap_bill', 'ap_bill_line', 'ap_payment', 'ap_allocation',
    'payroll_run', 'payroll_run_item',
    'treasury_bank_account', 'treasury_bank_transaction',
    'royalty_agreement', 'royalty_calculation',
    'reconciliation_session', 'reconciliation_match',
    'intercompany_transfer', 'journal_entry', 'journal_line', 'book',
]

async def main():
    conn = await asyncpg.connect(url, timeout=10)
    for tbl in TABLES:
        rows = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_schema='public' AND table_name=$1
            ORDER BY ordinal_position
        """, tbl)
        if rows:
            cols = [r['column_name'] for r in rows]
            print(f"\n{tbl}:")
            print(f"  {cols}")
        else:
            print(f"\n{tbl}: *** TABLE NOT FOUND ***")
    await conn.close()

asyncio.run(main())
