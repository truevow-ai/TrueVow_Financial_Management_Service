import os
import asyncio
from dotenv import load_dotenv
import asyncpg

load_dotenv('.env.local')
url = os.environ.get('FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL', '')
print(f'Using pooler URL: {url[:80]}...')

async def main():
    try:
        conn = await asyncpg.connect(url, timeout=10)
        v = await conn.fetchval('select 1')
        print(f'ASYNC CONNECT OK: {v}')
        await conn.close()
    except Exception as e:
        print(f'ASYNC CONNECT FAIL: {type(e).__name__} {e}')

asyncio.run(main())
