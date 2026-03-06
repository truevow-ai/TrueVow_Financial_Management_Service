"""Minimal debug — step through seed operations one by one."""
import asyncio, asyncpg, os
from dotenv import load_dotenv
load_dotenv('.env.local')

URL = os.getenv('FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL')
ENTITY_ID = '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c'
BOOK_ID   = '48972d9f-0f08-4f01-93ce-de078cb8bd3a'  # ACCRUAL book

async def main():
    conn = await asyncpg.connect(URL, timeout=10)
    print('Connected')

    # Check existing GL accounts on this book
    cnt = await conn.fetchval('SELECT count(*) FROM gl_account WHERE book_id=$1', BOOK_ID)
    print(f'Existing GL accounts on ACCRUAL book: {cnt}')

    # Check existing GL accounts on Main Book
    main_book = await conn.fetchrow(
        "SELECT id FROM book WHERE legal_entity_id=$1 AND name LIKE '%Main%'", ENTITY_ID
    )
    if main_book:
        cnt2 = await conn.fetchval('SELECT count(*) FROM gl_account WHERE book_id=$1', main_book['id'])
        print(f'Existing GL accounts on Main Book: {cnt2}')

    # Try one gl_account insert with explicit error
    try:
        await conn.execute(
            'INSERT INTO gl_account (book_id, account_code, account_name, account_type, is_active) '
            'VALUES ($1, $2, $3, $4, true)',
            BOOK_ID, '1000', 'Cash - Operating Account', 'ASSET'
        )
        print('Inserted 1000 OK')
    except Exception as e:
        print(f'Insert 1000 ERROR: {e}')

    try:
        await conn.execute(
            'INSERT INTO gl_account (book_id, account_code, account_name, account_type, is_active) '
            'VALUES ($1, $2, $3, $4, true) ON CONFLICT DO NOTHING',
            BOOK_ID, '1000', 'Cash - Operating Account', 'ASSET'
        )
        print('Insert 1000 with ON CONFLICT DO NOTHING: OK')
    except Exception as e:
        print(f'Insert 1000 ON CONFLICT ERROR: {e}')

    cnt = await conn.fetchval('SELECT count(*) FROM gl_account WHERE book_id=$1', BOOK_ID)
    print(f'GL accounts after: {cnt}')

    # Check ap_vendor unique constraint
    print('\nChecking ap_vendor constraints...')
    cons = await conn.fetch(
        "SELECT constraint_name, constraint_type FROM information_schema.table_constraints "
        "WHERE table_name='ap_vendor'"
    )
    for r in cons:
        print(f'  {r["constraint_name"]} ({r["constraint_type"]})')

    # Check ar_invoice status check constraint
    chk = await conn.fetch(
        "SELECT constraint_name, check_clause FROM information_schema.check_constraints "
        "WHERE constraint_name LIKE 'ar_invoice%status%' OR constraint_name LIKE '%ar_inv%status%'"
    )
    print('\nar_invoice status constraints:')
    for r in chk:
        print(f'  {r["constraint_name"]}: {r["check_clause"]}')

    # Check ap_bill status
    chk2 = await conn.fetch(
        "SELECT constraint_name, check_clause FROM information_schema.check_constraints "
        "WHERE constraint_name LIKE 'ap_bill%status%' OR constraint_name LIKE '%ap_bil%status%'"
    )
    print('\nap_bill status constraints:')
    for r in chk2:
        print(f'  {r["constraint_name"]}: {r["check_clause"]}')

    await conn.close()

asyncio.run(main())
