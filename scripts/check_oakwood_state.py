#!/usr/bin/env python3
"""Check current state of Oakwood Law Firm data in the DB."""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()
load_dotenv('.env.local')

URL = os.getenv('FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL', '').replace(
    'postgresql+asyncpg://', 'postgresql://'
)

async def main():
    conn = await asyncpg.connect(URL)

    print('=== Legal Entities ===')
    rows = await conn.fetch('SELECT id, code, name FROM legal_entity ORDER BY code')
    for r in rows:
        print(f'  {r["code"]:<15}  {r["id"]}  {r["name"]}')

    print()
    print('=== AR Customers ===')
    rows = await conn.fetch(
        'SELECT id, customer_code, customer_name, legal_entity_id, external_customer_id '
        'FROM ar_customer ORDER BY customer_code'
    )
    for r in rows:
        print(f'  {r["customer_code"]:<20}  le={r["legal_entity_id"]}  ext={r["external_customer_id"]}  name={r["customer_name"]}')

    print()
    print('=== AR Invoice counts per entity ===')
    rows = await conn.fetch(
        'SELECT le.code, le.id, count(ai.id) as cnt '
        'FROM legal_entity le LEFT JOIN ar_invoice ai ON ai.legal_entity_id = le.id '
        'GROUP BY le.id, le.code ORDER BY le.code'
    )
    for r in rows:
        print(f'  {r["code"]:<15}  {r["id"]}  invoices={r["cnt"]}')

    print()
    print('=== Books per entity ===')
    rows = await conn.fetch(
        'SELECT le.code, b.name, b.id FROM book b '
        'JOIN legal_entity le ON le.id = b.legal_entity_id ORDER BY le.code'
    )
    for r in rows:
        print(f'  {r["code"]:<15}  {r["name"]}')

    print()
    print('=== GL Accounts per book (count) ===')
    rows = await conn.fetch(
        'SELECT b.name, count(g.id) as cnt FROM gl_account g '
        'JOIN book b ON b.id = g.book_id GROUP BY b.name ORDER BY b.name'
    )
    for r in rows:
        print(f'  {r["name"]:<40}  gl_accounts={r["cnt"]}')

    await conn.close()

asyncio.run(main())
