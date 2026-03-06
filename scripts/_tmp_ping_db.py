"""Quick connectivity test for all available DB URLs."""
import asyncio, asyncpg, os
from dotenv import load_dotenv
load_dotenv('.env.local')

SESSION_URL = os.getenv('FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL')
TX_URL      = os.getenv('FINANCIAL_MANAGEMENT_DATABASE_TRANSACTION_POOLER_URL')

async def test_url(label, url):
    if not url:
        print(f'  {label}: URL not set')
        return False
    display = url[:60]
    try:
        c = await asyncio.wait_for(
            asyncpg.connect(url, statement_cache_size=0),
            timeout=8
        )
        v = await asyncio.wait_for(c.fetchval('SELECT 1'), timeout=5)
        await c.close()
        print(f'  {label}: OK (SELECT 1 = {v})')
        return True
    except asyncio.TimeoutError:
        print(f'  {label}: TIMEOUT (>{8}s)')
        return False
    except Exception as e:
        print(f'  {label}: ERROR {type(e).__name__}: {e}')
        return False

async def main():
    print('Testing DB connectivity...')
    s = await test_url('Session pooler  (5432)', SESSION_URL)
    t = await test_url('Transaction pooler (6543)', TX_URL)
    if s:
        print('\nSession pooler is available — use it for seed')
    elif t:
        print('\nTransaction pooler is available — use it for seed (needs BEGIN/COMMIT)')
    else:
        print('\nBoth poolers unavailable — wait and retry')

asyncio.run(main())
