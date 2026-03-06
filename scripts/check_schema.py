import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv('.env.local')

async def check_schema():
    db_url = os.getenv('FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL')
    conn = await asyncpg.connect(db_url)
    
    print("AR Invoice columns:")
    cols = await conn.fetch("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'ar_invoice' 
        ORDER BY ordinal_position
    """)
    for c in cols:
        print(f"  - {c['column_name']}")
    
    print("\nAP Bill columns:")
    cols = await conn.fetch("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'ap_bill' 
        ORDER BY ordinal_position
    """)
    for c in cols:
        print(f"  - {c['column_name']}")
    
    await conn.close()

asyncio.run(check_schema())
