import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_columns():
    db_url = os.getenv("FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL")
    if not db_url:
        db_url = os.getenv("DATABASE_URL")
    
    if "+asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(db_url)
    
    # Check treasury_transfer columns
    print("\ntreasury_transfer columns:")
    cols = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'treasury_transfer'
        ORDER BY ordinal_position
    """)
    for c in cols:
        print(f"  - {c[0]} ({c[1]})")
    
    # Check reconciliation_session columns
    print("\nreconciliation_session columns:")
    cols = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'reconciliation_session'
        ORDER BY ordinal_position
    """)
    for c in cols[:10]:
        print(f"  - {c[0]} ({c[1]})")
    
    await conn.close()

asyncio.run(check_columns())
