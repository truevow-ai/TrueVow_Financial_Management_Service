import asyncio, asyncpg, os
from dotenv import load_dotenv
load_dotenv('.env.local')
URL = os.getenv('FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL')

async def go():
    c = await asyncpg.connect(URL)
    cols = await c.fetch(
        "SELECT column_name, data_type, is_nullable "
        "FROM information_schema.columns "
        "WHERE table_name='accounting_period' ORDER BY ordinal_position"
    )
    print('accounting_period columns:')
    for r in cols:
        print(f'  {r["column_name"]:<30} {r["data_type"]:<20} nullable={r["is_nullable"]}')
    cons = await c.fetch(
        "SELECT constraint_name, constraint_type "
        "FROM information_schema.table_constraints "
        "WHERE table_name='accounting_period'"
    )
    print('constraints:')
    for r in cons:
        print(f'  {r["constraint_name"]:<50} {r["constraint_type"]}')

    # Also check a few ar_invoice and ap_bill columns
    for tbl in ('ar_invoice', 'ap_bill', 'ap_vendor'):
        cols2 = await c.fetch(
            "SELECT column_name FROM information_schema.columns "
            f"WHERE table_name='{tbl}' ORDER BY ordinal_position"
        )
        print(f'\n{tbl} columns: {[r["column_name"] for r in cols2]}')

    await c.close()

asyncio.run(go())
