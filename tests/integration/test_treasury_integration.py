"""
Treasury Integration Test
Tests bank accounts, transactions, and reconciliation
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

async def test_treasury_integration():
    print("=" * 80)
    print("TREASURY INTEGRATION TEST - End-to-End")
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
        # Step 1: Check bank accounts
        print("\n[STEP 1] Checking bank accounts...")
        accounts = await conn.fetch("""
            SELECT id, account_name, account_number, bank_name, currency, is_active
            FROM treasury_bank_account
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if accounts:
            print(f"[OK] Found {len(accounts)} bank accounts:")
            for acc in accounts:
                status = "Active" if acc['is_active'] else "Inactive"
                acct_num = acc['account_number'][-4:] if acc['account_number'] else "N/A"
                print(f"   - {acc['account_name']} ({acc['bank_name']}) ...{acct_num} - {acc['currency']} - {status}")
        else:
            print("[INFO] No bank accounts found in database")
        
        # Step 2: Check bank transactions
        print("\n[STEP 2] Checking bank transactions...")
        transactions = await conn.fetch("""
            SELECT 
                transaction_date,
                description,
                amount,
                transaction_type,
                is_reconciled
            FROM treasury_bank_transaction
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        if transactions:
            print(f"[OK] Found {len(transactions)} transactions:")
            for t in transactions[:5]:
                recon_status = "Reconciled" if t['is_reconciled'] else "Pending"
                print(f"   - {t['transaction_date']}: {t['description'][:30]} ${t['amount']:,.2f} ({t['transaction_type']}) - {recon_status}")
            if len(transactions) > 5:
                print(f"   ... and {len(transactions) - 5} more")
        else:
            print("[INFO] No bank transactions found in database")
        
        # Step 3: Check reconciliation sessions
        print("\n[STEP 3] Checking reconciliation sessions...")
        sessions = await conn.fetch("""
            SELECT 
                id,
                period_start,
                period_end,
                statement_ending_balance,
                status
            FROM reconciliation_session
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if sessions:
            print(f"[OK] Found {len(sessions)} reconciliation sessions:")
            for s in sessions:
                print(f"   - {s['id']}: {s['period_start']} to {s['period_end']} - Balance: ${s['statement_ending_balance']:,.2f} - {s['status']}")
        else:
            print("[INFO] No reconciliation sessions found in database")
        
        # Step 4: Check transfers (treasury_transfer table)
        print("\n[STEP 4] Checking transfers...")
        transfers = await conn.fetch("""
            SELECT 
                id,
                transfer_date,
                amount,
                currency,
                description
            FROM treasury_transfer
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if transfers:
            print(f"[OK] Found {len(transfers)} transfers:")
            for t in transfers:
                desc = t['description'][:40] if t['description'] else 'N/A'
                print(f"   - {t['id']}: ${t['amount']:,.2f} {t['currency']} - {desc}")
        else:
            print("[INFO] No transfers found in database")
        
        # Step 5: Test Backend API Endpoint
        print("\n[STEP 5] Testing Backend API...")
        async with httpx.AsyncClient() as client:
            try:
                # Test list bank accounts endpoint
                response = await client.get(
                    "http://localhost:8000/api/v1/books/17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c/treasury/bank-accounts",
                    params={"limit": 10}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"[OK] API Response: {len(data)} bank accounts returned")
                    if data:
                        print(f"   First account: {data[0].get('account_name', 'N/A')}")
                else:
                    print(f"[WARNING] API returned {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    
            except httpx.ConnectError as e:
                print(f"[WARNING] Cannot connect to backend API (is it running?)")
                print(f"   Error: {e}")
        
        # Step 6: Summary
        print("\n" + "=" * 80)
        print("TREASURY INTEGRATION TEST SUMMARY")
        print("=" * 80)
        print(f"[OK] Database: Connected successfully")
        print(f"[OK] Bank Accounts: {len(accounts)} accounts")
        print(f"[OK] Transactions: {len(transactions)} transactions")
        print(f"[OK] Reconciliation Sessions: {len(sessions)} sessions")
        print(f"[OK] Transfers: {len(transfers)} transfers")
        
        # Calculate totals
        total_balance = sum(float(acc['current_balance']) for acc in accounts) if accounts else 0
        
        print(f"\n   Total Cash Position: ${total_balance:,.2f}")
        
        print("\n[COMPLETE] Treasury Integration test complete!")
        print("\n[NEXT STEPS]:")
        print("   1. Ensure backend server is running on port 8000")
        print("   2. Test frontend Treasury pages with real data")
        print("   3. Proceed to Payroll integration testing")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_treasury_integration())
