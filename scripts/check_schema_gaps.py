"""Check schema gaps — bank tables, deleted_at, constraints, RLS."""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()
load_dotenv(".env.local")


async def main():
    url = os.getenv("FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL") or os.getenv("DATABASE_URL", "")
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)

    print("=== BANK TABLES ===")
    rows = await conn.fetch(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name ILIKE '%bank%' ORDER BY table_name"
    )
    for r in rows:
        print(r["table_name"])

    print("\n=== TABLES WITH deleted_at ===")
    rows = await conn.fetch(
        "SELECT table_name FROM information_schema.columns "
        "WHERE column_name='deleted_at' AND table_schema='public' ORDER BY table_name"
    )
    for r in rows:
        print(r["table_name"])

    print("\n=== TABLES MISSING deleted_at (sample) ===")
    rows = await conn.fetch(
        "SELECT DISTINCT table_name FROM information_schema.tables "
        "WHERE table_schema='public' AND table_name NOT IN ("
        "  SELECT table_name FROM information_schema.columns "
        "  WHERE column_name='deleted_at' AND table_schema='public'"
        ") ORDER BY table_name"
    )
    for r in rows:
        print(r["table_name"])

    print("\n=== NAMED CONSTRAINTS on journal_entry ===")
    rows = await conn.fetch(
        "SELECT constraint_name, constraint_type FROM information_schema.table_constraints "
        "WHERE table_name='journal_entry' AND table_schema='public' ORDER BY constraint_name"
    )
    for r in rows:
        print(r["constraint_name"], "|", r["constraint_type"])

    print("\n=== NAMED CONSTRAINTS on gl_account ===")
    rows = await conn.fetch(
        "SELECT constraint_name, constraint_type FROM information_schema.table_constraints "
        "WHERE table_name='gl_account' AND table_schema='public' ORDER BY constraint_name"
    )
    for r in rows:
        print(r["constraint_name"], "|", r["constraint_type"])

    print("\n=== NAMED CONSTRAINTS on accounting_period ===")
    rows = await conn.fetch(
        "SELECT constraint_name, constraint_type FROM information_schema.table_constraints "
        "WHERE table_name='accounting_period' AND table_schema='public' ORDER BY constraint_name"
    )
    for r in rows:
        print(r["constraint_name"], "|", r["constraint_type"])

    print("\n=== RLS STATUS (18 tables) ===")
    tables = [
        "legal_entity", "book", "gl_account", "accounting_period",
        "dimension", "dimension_value", "journal_entry", "journal_line",
        "ar_customer", "ar_invoice", "ar_payment", "ap_vendor", "ap_bill",
        "payroll_run", "bank_account", "bank_transaction",
        "intercompany_transfer", "royalty_agreement"
    ]
    rows = await conn.fetch(
        "SELECT tablename, rowsecurity FROM pg_tables "
        "WHERE schemaname='public' ORDER BY tablename"
    )
    rls_map = {r["tablename"]: r["rowsecurity"] for r in rows}
    for t in tables:
        status = "YES" if rls_map.get(t) else ("MISSING" if t in rls_map else "NO TABLE")
        print(f"  {t}: {status}")

    print("\n=== INTERCOMPANY_TRANSFER COLUMNS ===")
    rows = await conn.fetch(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_name='intercompany_transfer' AND table_schema='public' ORDER BY ordinal_position"
    )
    for r in rows:
        print(r["column_name"], "|", r["data_type"])

    await conn.close()


asyncio.run(main())
