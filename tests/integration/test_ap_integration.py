"""
AP Integration Test
Tests Accounts Payable end-to-end flow
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

async def test_ap_integration():
    print("=" * 80)
    print("AP INTEGRATION TEST - End-to-End")
    print("=" * 80)
    
    # Get database connection
    db_url = os.getenv("FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL")
    if not db_url:
        db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        print("[ERROR] No database URL found")
        return
    
    if "+asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Step 1: Check vendors
        print("\n[STEP 1] Checking AP vendors...")
        vendors = await conn.fetch("""
            SELECT id, vendor_code, vendor_name, is_active
            FROM ap_vendor
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if vendors:
            print(f"[OK] Found {len(vendors)} vendors:")
            for v in vendors:
                status = "Active" if v['is_active'] else "Inactive"
                print(f"   - {v['vendor_name']} ({v['vendor_code']}) - {status}")
        else:
            print("[WARNING] No vendors found in database")
        
        # Step 2: Check bills
        print("\n[STEP 2] Checking AP bills...")
        bills = await conn.fetch("""
            SELECT 
                bill_number,
                ap_vendor_id,
                total_amount,
                outstanding_amount,
                status,
                due_date
            FROM ap_bill
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        if bills:
            print(f"[OK] Found {len(bills)} bills:")
            for bill in bills:
                print(f"   - {bill['bill_number']}: ${bill['total_amount']:,.2f} (Outstanding: ${bill['outstanding_amount']:,.2f}) - {bill['status']}")
        else:
            print("[INFO] No bills found in database")
        
        # Step 3: Check payments
        print("\n[STEP 3] Checking AP payments...")
        payments = await conn.fetch("""
            SELECT 
                payment_number,
                ap_vendor_id,
                payment_amount AS total_amount,
                payment_date
            FROM ap_payment
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        if payments:
            print(f"[OK] Found {len(payments)} payments:")
            for p in payments:
                print(f"   - {p['payment_number']}: ${p['total_amount']:,.2f} on {p['payment_date']}")
        else:
            print("[INFO] No payments found in database")
        
        # Step 4: Test Backend API Endpoint
        print("\n[STEP 4] Testing Backend API...")
        async with httpx.AsyncClient() as client:
            try:
                # Test list bills endpoint
                response = await client.get(
                    "http://localhost:8000/api/v1/books/17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c/ap/bills",
                    params={"limit": 10}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"[OK] API Response: {len(data)} bills returned")
                    if data:
                        print(f"   First bill: {data[0].get('bill_number', 'N/A')}")
                else:
                    print(f"[WARNING] API returned {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    
            except httpx.ConnectError as e:
                print(f"[WARNING] Cannot connect to backend API (is it running?)")
                print(f"   Error: {e}")
        
        # Step 5: Summary
        print("\n" + "=" * 80)
        print("AP INTEGRATION TEST SUMMARY")
        print("=" * 80)
        print(f"[OK] Database: Connected successfully")
        print(f"[OK] Vendors: {len(vendors)} vendors in database")
        print(f"[OK] Bills: {len(bills)} bills in database")
        print(f"[OK] Payments: {len(payments)} payments in database")
        
        # Calculate totals
        total_billed = sum(float(bill['total_amount']) for bill in bills)
        total_outstanding = sum(float(bill['outstanding_amount']) for bill in bills)
        total_paid = sum(float(p['total_amount']) for p in payments)
        
        print(f"   Total Billed: ${total_billed:,.2f}")
        print(f"   Total Outstanding: ${total_outstanding:,.2f}")
        print(f"   Total Paid: ${total_paid:,.2f}")
        
        print("\n[COMPLETE] AP Integration test complete!")
        print("\n[NEXT STEPS]:")
        print("   1. Ensure backend server is running on port 8000")
        print("   2. Test frontend AP pages with real data")
        print("   3. Proceed to Treasury integration testing")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_ap_integration())
