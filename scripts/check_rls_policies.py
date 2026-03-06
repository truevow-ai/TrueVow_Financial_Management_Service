"""Check RLS policies and ap_payment columns."""
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

    print("=== RLS POLICIES on legal_entity ===")
    rows = await conn.fetch(
        "SELECT policyname, cmd, qual::text as qual_expr "
        "FROM pg_policies WHERE tablename='legal_entity'"
    )
    for r in rows:
        print(r["policyname"], "|", r["cmd"], "|", r["qual_expr"])

    print("\n=== AP_PAYMENT COLUMNS ===")
    rows = await conn.fetch(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='ap_payment' AND table_schema='public' ORDER BY ordinal_position"
    )
    for r in rows:
        print(r["column_name"])

    print("\n=== GL_ACCOUNT unique constraints ===")
    rows = await conn.fetch(
        "SELECT constraint_name, constraint_type FROM information_schema.table_constraints "
        "WHERE table_name='gl_account' AND constraint_type='UNIQUE' AND table_schema='public'"
    )
    for r in rows:
        print(r["constraint_name"])

    await conn.close()


asyncio.run(main())
