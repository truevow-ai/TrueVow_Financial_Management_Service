"""Debug accounting_period insert hang."""
import asyncio, asyncpg, os
from datetime import date
from dotenv import load_dotenv
load_dotenv('.env.local')

URL     = os.getenv('FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL')
BOOK_ID = '48972d9f-0f08-4f01-93ce-de078cb8bd3a'

async def main():
    c = await asyncpg.connect(URL, timeout=15, command_timeout=10)
    print('Connected')

    # How many periods already exist?
    cnt = await c.fetchval('SELECT count(*) FROM accounting_period WHERE book_id=$1', BOOK_ID)
    print(f'Existing periods: {cnt}')
    if cnt > 0:
        rows = await c.fetch(
            'SELECT period_name, status FROM accounting_period WHERE book_id=$1 ORDER BY start_date',
            BOOK_ID
        )
        for r in rows:
            print(f'  {r["period_name"]:<15} {r["status"]}')

    # Check for locks on accounting_period
    locks = await c.fetch("""
        SELECT pid, mode, granted
        FROM pg_locks l
        JOIN pg_class c ON c.oid = l.relation
        WHERE c.relname = 'accounting_period' AND NOT granted
    """)
    print(f'\nBlocking locks on accounting_period: {len(locks)}')
    for r in locks:
        print(f'  pid={r["pid"]} mode={r["mode"]} granted={r["granted"]}')

    # Try a single INSERT with explicit error catch
    print('\nTrying INSERT for January 2025...')
    try:
        result = await c.execute(
            'INSERT INTO accounting_period (book_id, start_date, end_date, period_name, status) '
            "VALUES ($1, '2025-01-01', '2025-01-31', 'January 2025', 'CLOSED') "
            'ON CONFLICT DO NOTHING',
            BOOK_ID
        )
        print(f'INSERT result: {result}')
    except Exception as e:
        print(f'INSERT error: {type(e).__name__}: {e}')

    # Check triggers
    triggers = await c.fetch(
        "SELECT trigger_name, event_manipulation, action_timing "
        "FROM information_schema.triggers "
        "WHERE event_object_table = 'accounting_period'"
    )
    print(f'\nTriggers on accounting_period: {len(triggers)}')
    for r in triggers:
        print(f'  {r["trigger_name"]} {r["event_manipulation"]} {r["action_timing"]}')

    await c.close()
    print('Done')

asyncio.run(main())
