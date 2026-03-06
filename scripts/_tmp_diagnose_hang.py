"""Diagnose the accounting_period SELECT hang."""
import asyncio, asyncpg, os
from dotenv import load_dotenv
load_dotenv('.env.local')

URL     = os.getenv('FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL')
BOOK_ID = '48972d9f-0f08-4f01-93ce-de078cb8bd3a'

async def main():
    c = await asyncpg.connect(URL, statement_cache_size=0, timeout=10)
    print('Connected', flush=True)

    # Check for idle-in-transaction connections
    print('Checking idle-in-transaction connections...', flush=True)
    idle = await asyncio.wait_for(c.fetch(
        "SELECT pid, state, query, wait_event_type, wait_event, "
        "       now() - xact_start AS txn_age "
        "FROM pg_stat_activity "
        "WHERE state IN ('idle in transaction', 'active') "
        "  AND pid != pg_backend_pid() "
        "ORDER BY txn_age DESC NULLS LAST"
    ), timeout=5)
    print(f'Other connections: {len(idle)}')
    for r in idle:
        print(f'  pid={r["pid"]} state={r["state"]} age={r["txn_age"]} '
              f'wait={r["wait_event_type"]}/{r["wait_event"]}')
        print(f'    query: {str(r["query"])[:80]}')

    # Test the exact query that hangs
    print('\nTesting accounting_period SELECT with 6s timeout...', flush=True)
    try:
        result = await asyncio.wait_for(
            c.fetchval(
                'SELECT id FROM accounting_period WHERE book_id=$1 AND period_name=$2',
                BOOK_ID, 'January 2025'
            ),
            timeout=6
        )
        print(f'SELECT OK: {result}', flush=True)
    except asyncio.TimeoutError:
        print('SELECT TIMED OUT — blocking lock likely held by idle-in-transaction session', flush=True)
    except Exception as e:
        print(f'SELECT ERROR: {type(e).__name__}: {e}', flush=True)

    # Try to terminate idle-in-transaction connections
    print('\nTerminating idle-in-transaction connections...', flush=True)
    try:
        killed = await asyncio.wait_for(c.fetchval(
            "SELECT count(pg_terminate_backend(pid)) "
            "FROM pg_stat_activity "
            "WHERE state = 'idle in transaction' "
            "  AND pid != pg_backend_pid()"
        ), timeout=5)
        print(f'Terminated: {killed}', flush=True)
    except Exception as e:
        print(f'Terminate error: {e}', flush=True)

    await c.close()
    print('Done', flush=True)

asyncio.run(main())
