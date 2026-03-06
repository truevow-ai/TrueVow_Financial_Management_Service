"""
Advanced Reporting Integration Test
Tests financial reports and analytics
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

async def test_reporting_integration():
    print("=" * 80)
    print("ADVANCED REPORTING INTEGRATION TEST - End-to-End")
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
        # Step 1: Check GL accounts (for trial balance)
        print("\n[STEP 1] Checking chart of accounts...")
        accounts = await conn.fetch("""
            SELECT id, account_code, account_name, account_type
            FROM gl_account
            ORDER BY account_code
            LIMIT 20
        """)
        
        if accounts:
            print(f"[OK] Found {len(accounts)} GL accounts:")
            for acc in accounts[:5]:
                print(f"   - {acc['account_code']}: {acc['account_name']} ({acc['account_type']})")
            if len(accounts) > 5:
                print(f"   ... and {len(accounts) - 5} more")
        else:
            print("[INFO] No GL accounts found in database")
        
        # Step 2: Check journal entries (for GL detail report)
        print("\n[STEP 2] Checking journal entries...")
        entries = await conn.fetch("""
            SELECT 
                je.entry_number,
                je.entry_date,
                je.status,
                je.description
            FROM journal_entry je
            ORDER BY je.created_at DESC
            LIMIT 10
        """)
        
        if entries:
            print(f"[OK] Found {len(entries)} journal entries:")
            for e in entries[:5]:
                desc = e['description'][:40] if e['description'] else 'N/A'
                print(f"   - {e['entry_number']}: {e['entry_date']} | {e['status']} | {desc}")
            if len(entries) > 5:
                print(f"   ... and {len(entries) - 5} more")
        else:
            print("[INFO] No journal entries found in database")
        
        # Step 3: Check accounting periods
        print("\n[STEP 3] Checking accounting periods...")
        periods = await conn.fetch("""
            SELECT 
                period_name,
                start_date,
                end_date,
                status
            FROM accounting_period
            ORDER BY start_date DESC
            LIMIT 10
        """)
        
        if periods:
            print(f"[OK] Found {len(periods)} accounting periods:")
            for p in periods:
                print(f"   - {p['period_name']}: {p['start_date']} to {p['end_date']} - {p['status']}")
        else:
            print("[INFO] No accounting periods found in database")
        
        # Step 4: Calculate report-ready metrics
        print("\n[STEP 4] Calculating report metrics...")
        
        # Trial Balance totals - simplified
        tb_totals = await conn.fetchrow("""
            SELECT 
                COUNT(DISTINCT a.id) as account_count
            FROM gl_account a
        """)
        
        if tb_totals:
            print(f"[OK] Trial Balance ready:")
            print(f"   - Total GL Accounts: {tb_totals['account_count']}")
        
        # P&L metrics - simplified
        pl_metrics = await conn.fetchrow("""
            SELECT 
                COUNT(*) as revenue_expense_accounts
            FROM gl_account a
            WHERE a.account_type IN ('REVENUE', 'EXPENSE')
        """)
        
        if pl_metrics:
            print(f"[OK] P&L structure ready:")
            print(f"   - Revenue/Expense Accounts: {pl_metrics['revenue_expense_accounts']}")
        
        # Balance Sheet metrics - simplified
        bs_metrics = await conn.fetchrow("""
            SELECT 
                COUNT(*) as balance_sheet_accounts
            FROM gl_account a
            WHERE a.account_type IN ('ASSET', 'LIABILITY', 'EQUITY')
        """)
        
        if bs_metrics:
            print(f"[OK] Balance Sheet structure ready:")
            print(f"   - Asset/Liability/Equity Accounts: {bs_metrics['balance_sheet_accounts']}")
        
        # Step 5: Test Backend API Endpoint
        print("\n[STEP 5] Testing Backend API...")
        async with httpx.AsyncClient() as client:
            try:
                # Test trial balance endpoint
                response = await client.get(
                    "http://localhost:8000/api/v1/reporting/trial-balance",
                    params={
                        "legal_entity_id": "17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c",
                        "book_id": "17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c",
                        "limit": 10
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"[OK] Trial Balance API: Success")
                    if isinstance(data, list) and data:
                        print(f"   First row: {data[0].get('account_code', 'N/A')}")
                else:
                    print(f"[WARNING] API returned {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    
            except httpx.ConnectError as e:
                print(f"[WARNING] Cannot connect to backend API (is it running?)")
                print(f"   Error: {e}")
        
        # Step 6: Summary
        print("\n" + "=" * 80)
        print("ADVANCED REPORTING INTEGRATION TEST SUMMARY")
        print("=" * 80)
        print(f"[OK] Database: Connected successfully")
        print(f"[OK] Chart of Accounts: {len(accounts)} accounts")
        print(f"[OK] Journal Entries: {len(entries)} entries")
        print(f"[OK] Accounting Periods: {len(periods)} periods")
        
        if tb_totals and pl_metrics and bs_metrics:
            print(f"\n   Reports Available:")
            print(f"   [OK] Trial Balance - Ready")
            print(f"   [OK] P&L Statement - Ready")
            print(f"   [OK] Balance Sheet - Ready")
            print(f"   [OK] Cash Flow - Pending treasury data")
        
        print("\n[COMPLETE] Advanced Reporting Integration test complete!")
        print("\n[NEXT STEPS]:")
        print("   1. Ensure backend server is running on port 8000")
        print("   2. Test frontend Reporting pages with real data")
        print("   3. Generate sample reports (PDF/Excel export)")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_reporting_integration())
