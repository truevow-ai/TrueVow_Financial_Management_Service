"""Check legal entities and fix Oakwood data"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    db_url = os.getenv("FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL")
    if not db_url:
        db_url = os.getenv("DATABASE_URL") or os.getenv("FINANCIAL_MANAGEMENT_DATABASE_URL")
    
    if not db_url:
        print("No database URL found")
        return
    
    if "+asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Get all legal entities
        entities = await conn.fetch("SELECT id, name FROM legal_entity ORDER BY created_at DESC LIMIT 5")
        
        print("Legal Entities:")
        for ent in entities:
            print(f"  - {ent['name']} (ID: {ent['id']})")
        
        # Check Oakwood customer
        oakwood = await conn.fetchrow("""
            SELECT id, customer_code, customer_name, external_customer_id, legal_entity_id
            FROM ar_customer
            WHERE external_customer_id = 'e2362e1c-759a-402d-9b38-2eab1ae8ad3f'
        """)
        
        if oakwood:
            print(f"\nOakwood Law Firm Customer:")
            print(f"  ID: {oakwood['id']}")
            print(f"  Code: {oakwood['customer_code']}")
            print(f"  Name: {oakwood['customer_name']}")
            print(f"  External ID: {oakwood['external_customer_id']}")
            print(f"  Legal Entity ID: {oakwood['legal_entity_id']}")
            
            # Check invoices for this customer
            invoices = await conn.fetch("""
                SELECT invoice_number, total_amount, outstanding_amount, status, due_date
                FROM ar_invoice
                WHERE ar_customer_id = $1
                ORDER BY created_at DESC
            """, oakwood['id'])
            
            print(f"\nInvoices: {len(invoices)}")
            for inv in invoices:
                print(f"  {inv['invoice_number']}: ${inv['total_amount']:,.2f} (Outstanding: ${inv['outstanding_amount']:,.2f}) - {inv['status']}")
        else:
            print("\n❌ Oakwood Law Firm customer not found!")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
