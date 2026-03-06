import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_payroll_tables():
    db_url = os.getenv("FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL")
    if not db_url:
        db_url = os.getenv("DATABASE_URL")
    
    if "+asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(db_url)
    
    # Check pay_group columns
    print("\npay_group columns:")
    cols = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'pay_group'
        ORDER BY ordinal_position
    """)
    for c in cols:
        print(f"  - {c[0]} ({c[1]})")
    
    # Check payroll_run columns
    print("\npayroll_run columns:")
    cols = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'payroll_run'
        ORDER BY ordinal_position
    """)
    for c in cols[:15]:
        print(f"  - {c[0]} ({c[1]})")
    
    # Check commission_plan columns
    print("\ncommission_plan columns:")
    cols = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = 'commission_plan'
        ORDER BY ordinal_position
    """)
    for c in cols[:10]:
        print(f"  - {c[0]} ({c[1]})")
    
    await conn.close()

asyncio.run(check_payroll_tables())
