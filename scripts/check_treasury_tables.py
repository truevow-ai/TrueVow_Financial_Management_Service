import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def check_tables():
    db_url = os.getenv("FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL")
    if not db_url:
        db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("[ERROR] No database URL found")
        return
    
    if "+asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)
    
    tables = await conn.fetch("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND (table_name LIKE '%bank%' OR table_name LIKE '%treasury%' OR table_name LIKE '%recon%')
        ORDER BY table_name
    """)
    
    print("Treasury-related tables found:")
    for t in tables:
        print(f"  - {t[0]}")
    
    await conn.close()

asyncio.run(check_tables())
