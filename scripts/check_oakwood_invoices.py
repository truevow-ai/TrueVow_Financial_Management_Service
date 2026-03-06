"""
Verify Oakwood Law Firm invoice data in database
Checks all invoices created for tenant ID e2362e1c-759a-402d-9b38-2eab1ae8ad3f
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def verify_invoices():
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL") or os.getenv("FINANCIAL_MANAGEMENT_DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not found in .env")
        return
    
    # Convert to pooler URL if needed
    if "supabase.co" in database_url and "/postgres?" in database_url:
        db_url = database_url.replace("/postgres?", "/pooler/postgres?")
    else:
        db_url = database_url
    
    print(f"🔍 Verifying Oakwood Law Firm invoices...")
    print(f"Database: {db_url[:50]}...")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Get customer info
        customer = await conn.fetchrow("""
            SELECT id, customer_code, external_customer_id, customer_name
            FROM ar_customer
            WHERE external_customer_id = 'e2362e1c-759a-402d-9b38-2eab1ae8ad3f'
        """)
        
        if not customer:
            print("❌ No customer found with Clerk tenant ID: e2362e1c-759a-402d-9b38-2eab1ae8ad3f")
            return
        
        print(f"\n✅ Customer Found:")
        print(f"   ID: {customer['id']}")
        print(f"   Code: {customer['customer_code']}")
        print(f"   Name: {customer['customer_name']}")
        print(f"   External ID: {customer['external_customer_id']}")
        
        # Get all invoices
        invoices = await conn.fetch("""
            SELECT 
                invoice_number,
                external_invoice_id,
                days_overdue,
                days_outstanding,
                status,
                total_amount,
                outstanding_amount,
                created_at
            FROM ar_invoice
            WHERE legal_entity_id = $1
            ORDER BY created_at DESC
        """, customer['id'])
        
        print(f"\n📄 Invoices Found: {len(invoices)}")
        print("=" * 100)
        
        total_revenue = 0
        total_outstanding = 0
        
        for inv in invoices:
            print(f"\nInvoice: {inv['invoice_number']}")
            print(f"  External ID: {inv['external_invoice_id']}")
            print(f"  Status: {inv['status']}")
            print(f"  Amount: ${inv['total_amount']:,.2f}")
            print(f"  Outstanding: ${inv['outstanding_amount']:,.2f}")
            print(f"  Days Overdue: {inv['days_overdue']}")
            print(f"  Days Outstanding: {inv['days_outstanding']}")
            print(f"  Created: {inv['created_at']}")
            
            total_revenue += float(inv['total_amount'])
            total_outstanding += float(inv['outstanding_amount'])
        
        print("\n" + "=" * 100)
        print(f"💰 Summary:")
        print(f"   Total Revenue: ${total_revenue:,.2f}")
        print(f"   Total Outstanding: ${total_outstanding:,.2f}")
        print(f"   Total Paid: ${(total_revenue - total_outstanding):,.2f}")
        
        # Test dashboard API
        print("\n" + "=" * 100)
        print("🧪 Testing Dashboard API...")
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/api/v1/dashboard/stats")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ API Response (200 OK)")
                print(f"   Overdue Invoices: {data.get('overdue_invoices', 'N/A')}")
                print(f"   Upcoming Payments: {data.get('upcoming_payments', 'N/A')}")
                print(f"   Total Revenue: ${data.get('total_revenue', 'N/A')}")
                print(f"   Accounts Receivable: ${data.get('accounts_receivable', 'N/A')}")
            else:
                print(f"   ❌ API Error: {response.status_code}")
                print(f"   Response: {response.text}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(verify_invoices())
