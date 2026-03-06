#!/usr/bin/env python3
"""Check PostgreSQL roles and RLS bypass capability"""
import asyncio, asyncpg, os
from dotenv import load_dotenv

load_dotenv()
load_dotenv('.env.local')
url = os.getenv('FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL', '').replace('postgresql+asyncpg://', 'postgresql://')

async def main():
    conn = await asyncpg.connect(url, timeout=10)

    r = await conn.fetchrow("SELECT current_user, rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")
    print(f"Current user : {r['current_user']}")
    print(f"superuser    : {r['rolsuper']}")
    print(f"BYPASSRLS    : {r['rolbypassrls']}")

    print("\nSupabase roles:")
    rows = await conn.fetch("""
        SELECT rolname, rolsuper, rolbypassrls
        FROM pg_roles
        WHERE rolname IN ('postgres','authenticated','anon','service_role','authenticator')
        ORDER BY rolname
    """)
    for row in rows:
        print(f"  {row['rolname']:<20} super={row['rolsuper']}  bypassrls={row['rolbypassrls']}")

    print("\nGrants on legal_entity:")
    grants = await conn.fetch("""
        SELECT grantee, privilege_type
        FROM information_schema.table_privileges
        WHERE table_name = 'legal_entity' AND table_schema = 'public'
        ORDER BY grantee, privilege_type
    """)
    for g in grants:
        print(f"  {g['grantee']:<20} {g['privilege_type']}")

    await conn.close()

asyncio.run(main())
