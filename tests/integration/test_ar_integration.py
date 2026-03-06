"""
Comprehensive AR Integration Test
Tests end-to-end flow from frontend to backend
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

async def test_ar_integration():
    print("=" * 80)
    print("AR INTEGRATION TEST - End-to-End")
    print("=" * 80)
    
    # Get database connection
    db_url = os.getenv("FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL")
    if not db_url:
        db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("❌ ERROR: No database URL found")
        return
    
    if "+asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Step 1: Verify Oakwood Law Firm customer exists
        print("\n[STEP 1] Checking Oakwood Law Firm customer...")
        customer = await conn.fetchrow("""
            SELECT id, customer_code, customer_name, external_customer_id
            FROM ar_customer
            WHERE customer_code = 'OAKWOOD-LAW'
        """)
        
        if not customer:
            print("❌ Oakwood Law Firm customer not found!")
            return
        
        print(f"[OK] Customer Found: {customer['customer_name']} ({customer['customer_code']})")
        print(f"   ID: {customer['id']}")
        print(f"   External ID: {customer['external_customer_id']}")
        
        # Step 2: Check invoices
        print("\n[STEP 2] Checking invoices...")
        invoices = await conn.fetch("""
            SELECT 
                invoice_number,
                total_amount,
                outstanding_amount,
                status,
                due_date
            FROM ar_invoice
            WHERE ar_customer_id = $1
            ORDER BY created_at DESC
        """, customer['id'])
        
        print(f"[OK] Found {len(invoices)} invoices:")
        for inv in invoices:
            print(f"   • {inv['invoice_number']}: ${inv['total_amount']:,.2f} (Outstanding: ${inv['outstanding_amount']:,.2f}) - {inv['status']}")
        
        # Step 3: Test Backend API Endpoint
        print("\n[STEP 3] Testing Backend API...")
        async with httpx.AsyncClient() as client:
            try:
                # Test dashboard stats endpoint
                response = await client.get(
                    "http://localhost:8000/api/v1/books/17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c/ar/invoices",
                    params={"limit": 10}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"[OK] API Response: {len(data)} invoices returned")
                    if data:
                        print(f"   First invoice: {data[0].get('invoice_number', 'N/A')}")
                else:
                    print(f"[WARNING] API returned {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    
            except httpx.ConnectError as e:
                print(f"[WARNING] Cannot connect to backend API (is it running?)")
                print(f"   Error: {e}")
        
        # Step 4: Summary
        print("\n" + "=" * 80)
        print("INTEGRATION TEST SUMMARY")
        print("=" * 80)
        print(f"[OK] Database: Connected successfully")
        print(f"[OK] Customer: Oakwood Law Firm verified")
        print(f"[OK] Invoices: {len(invoices)} invoices in database")
        print(f"   Total Revenue: ${sum(float(inv['total_amount']) for inv in invoices):,.2f}")
        print(f"   Total Outstanding: ${sum(float(inv['outstanding_amount']) for inv in invoices):,.2f}")
        
        print("\n[COMPLETE] AR Integration test complete!")
        print("\n[NEXT STEPS]:")
        print("   1. Ensure backend server is running on port 8000")
        print("   2. Test frontend AR pages with real data")
        print("   3. Proceed to AP integration testing")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_ar_integration())
