"""Test a single INSERT into gl_account."""
import asyncio, asyncpg, os
from dotenv import load_dotenv
load_dotenv('.env.local')

URL     = os.getenv('FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL')
BOOK_ID = '48972d9f-0f08-4f01-93ce-de078cb8bd3a'

async def main():
    print('Connecting...', flush=True)
    c = await asyncpg.connect(URL, statement_cache_size=0, timeout=10)
    print('Connected', flush=True)

    # SELECT
    cnt = await asyncio.wait_for(
        c.fetchval('SELECT count(*) FROM gl_account WHERE book_id=$1', BOOK_ID),
        timeout=5
    )
    print(f'Current count: {cnt}', flush=True)

    # INSERT with 8s timeout
    print('INSERT...', flush=True)
    try:
        r = await asyncio.wait_for(
            c.execute(
                "INSERT INTO gl_account "
                "(book_id, account_code, account_name, account_type, is_active) "
                "VALUES ($1,'9999','Test Account','ASSET',true) ON CONFLICT DO NOTHING",
                BOOK_ID
            ),
            timeout=8
        )
        print(f'INSERT OK: {r}', flush=True)
    except asyncio.TimeoutError:
        print('INSERT TIMED OUT — likely table lock from a previous transaction', flush=True)
        print('Kill all connections via Supabase dashboard and retry', flush=True)
    except Exception as e:
        print(f'INSERT ERROR: {type(e).__name__}: {e}', flush=True)

    # Delete test row
    try:
        await asyncio.wait_for(
            c.execute("DELETE FROM gl_account WHERE account_code='9999' AND book_id=$1", BOOK_ID),
            timeout=5
        )
        print('Cleanup OK', flush=True)
    except Exception:
        pass

    await c.close()
    print('Done', flush=True)

asyncio.run(main())
