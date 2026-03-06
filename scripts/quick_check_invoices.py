"""Simple invoice check for Oakwood Law Firm"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("No DATABASE_URL found")
        return
    
    # Convert to sync driver for asyncpg
    db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    print(f"Connecting to database...")
    conn = await asyncpg.connect(db_url)
    
    try:
        # Check customer
        customer = await conn.fetchrow("""
            SELECT id, customer_code, customer_name, external_customer_id
            FROM ar_customer
            WHERE external_customer_id = 'e2362e1c-759a-402d-9b38-2eab1ae8ad3f'
        """)
        
        if customer:
            print(f"\n✅ Customer: {customer['customer_name']} ({customer['customer_code']})")
            print(f"   ID: {customer['id']}")
            
            # Check invoices
            invoices = await conn.fetch("""
                SELECT invoice_number, total_amount, outstanding_amount, status
                FROM ar_invoice
                WHERE legal_entity_id = $1
                ORDER BY created_at DESC
            """, customer['id'])
            
            print(f"\n📄 Invoices: {len(invoices)}")
            total = 0
            outstanding = 0
            
            for inv in invoices:
                print(f"   {inv['invoice_number']}: ${inv['total_amount']:,.2f} (Outstanding: ${inv['outstanding_amount']:,.2f}) - {inv['status']}")
                total += float(inv['total_amount'])
                outstanding += float(inv['outstanding_amount'])
            
            print(f"\n💰 Total Revenue: ${total:,.2f}")
            print(f"💰 Total Outstanding: ${outstanding:,.2f}")
        else:
            print("❌ Customer not found")
            
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
