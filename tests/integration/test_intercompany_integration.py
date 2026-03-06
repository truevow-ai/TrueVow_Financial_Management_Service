"""
Intercompany Integration Test
Tests intercompany transfers, balances, and royalties
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

async def test_intercompany_integration():
    print("=" * 80)
    print("INTERCOMPANY INTEGRATION TEST - End-to-End")
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
        # Step 1: Check legal entities
        print("\n[STEP 1] Checking legal entities...")
        entities = await conn.fetch("""
            SELECT id, code, name, country, functional_currency
            FROM legal_entity
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        if entities:
            print(f"[OK] Found {len(entities)} legal entities:")
            for e in entities:
                print(f"   - {e['name']} ({e['code']}) - {e['country']} - {e['functional_currency']}")
        else:
            print("[WARNING] No legal entities found in database")
        
        # Step 2: Check intercompany transfers
        print("\n[STEP 2] Checking intercompany transfers...")
        transfers = await conn.fetch("""
            SELECT 
                id,
                from_entity_id,
                to_entity_id,
                transfer_date,
                amount,
                currency,
                transfer_type,
                status
            FROM intercompany_transfer
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        if transfers:
            print(f"[OK] Found {len(transfers)} intercompany transfers:")
            for t in transfers:
                print(f"   - {t['id']}: ${t['amount']:,.2f} {t['currency']} | {t['transfer_type']} | {t['status']}")
        else:
            print("[INFO] No intercompany transfers found in database")
        
        # Step 3: Check intercompany balances
        print("\n[STEP 3] Checking intercompany balances...")
        balances = await conn.fetch("""
            SELECT 
                id,
                from_entity_id,
                to_entity_id,
                balance_amount,
                currency,
                is_reconciled
            FROM intercompany_balance
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        if balances:
            print(f"[OK] Found {len(balances)} intercompany balances:")
            for b in balances:
                recon_status = "Reconciled" if b['is_reconciled'] else "Pending"
                print(f"   - {b['id']}: ${b['balance_amount']:,.2f} {b['currency']} - {recon_status}")
        else:
            print("[INFO] No intercompany balances found in database")
        
        # Step 4: Check royalty agreements
        print("\n[STEP 4] Checking royalty agreements...")
        royalties = await conn.fetch("""
            SELECT 
                id,
                from_entity_id AS licensor_entity_id,
                to_entity_id   AS licensee_entity_id,
                agreement_name,
                rate           AS royalty_rate,
                basis          AS calculation_base,
                is_active
            FROM royalty_agreement
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if royalties:
            print(f"[OK] Found {len(royalties)} royalty agreements:")
            for r in royalties:
                status = "Active" if r['is_active'] else "Inactive"
                print(f"   - {r['agreement_name']}: {r['royalty_rate']}% on {r['calculation_base']} - {status}")
        else:
            print("[INFO] No royalty agreements found in database")
        
        # Step 5: Test Backend API Endpoint
        print("\n[STEP 5] Testing Backend API...")
        async with httpx.AsyncClient() as client:
            try:
                # Test list intercompany transfers endpoint
                response = await client.get(
                    "http://localhost:8000/api/v1/intercompany/transfers",
                    params={"limit": 10}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"[OK] API Response: {len(data)} transfers returned")
                    if data:
                        print(f"   First transfer: {data[0].get('reference_number', 'N/A')}")
                else:
                    print(f"[WARNING] API returned {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    
            except httpx.ConnectError as e:
                print(f"[WARNING] Cannot connect to backend API (is it running?)")
                print(f"   Error: {e}")
        
        # Step 6: Summary
        print("\n" + "=" * 80)
        print("INTERCOMPANY INTEGRATION TEST SUMMARY")
        print("=" * 80)
        print(f"[OK] Database: Connected successfully")
        print(f"[OK] Legal Entities: {len(entities)} entities")
        print(f"[OK] Intercompany Transfers: {len(transfers)} transfers")
        print(f"[OK] Intercompany Balances: {len(balances)} balances")
        print(f"[OK] Royalty Agreements: {len(royalties)} agreements")
        
        # Calculate totals
        total_transfer_volume = sum(float(t['amount']) for t in transfers) if transfers else 0
        total_outstanding = sum(float(b['balance_amount']) for b in balances) if balances else 0
        
        print(f"\n   Total Transfer Volume: ${total_transfer_volume:,.2f}")
        print(f"   Total Outstanding Balances: ${total_outstanding:,.2f}")
        
        print("\n[COMPLETE] Intercompany Integration test complete!")
        print("\n[NEXT STEPS]:")
        print("   1. Ensure backend server is running on port 8000")
        print("   2. Test frontend Intercompany pages with real data")
        print("   3. Proceed to Reporting & Analytics testing")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_intercompany_integration())
