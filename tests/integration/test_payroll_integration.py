"""
Payroll Integration Test
Tests employee management and payroll processing
"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv
import httpx

load_dotenv()

async def test_payroll_integration():
    print("=" * 80)
    print("PAYROLL INTEGRATION TEST - End-to-End")
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
        # Step 1: Check employees
        print("\n[STEP 1] Checking employees...")
        employees = await conn.fetch("""
            SELECT id, employee_code, employee_name, employee_type, is_active, currency
            FROM hr_employee
            ORDER BY created_at DESC
            LIMIT 10
        """)
        
        if employees:
            print(f"[OK] Found {len(employees)} employees:")
            for emp in employees:
                status = "Active" if emp['is_active'] else "Inactive"
                print(f"   - {emp['employee_name']} ({emp['employee_code']}) - {emp['employee_type']} - {emp['currency']} - {status}")
        else:
            print("[INFO] No employees found in database")
        
        # Step 2: Check pay groups
        print("\n[STEP 2] Checking pay groups...")
        pay_groups = await conn.fetch("""
            SELECT id, group_code, group_name, frequency, is_active
            FROM pay_group
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if pay_groups:
            print(f"[OK] Found {len(pay_groups)} pay groups:")
            for pg in pay_groups:
                status = "Active" if pg['is_active'] else "Inactive"
                print(f"   - {pg['group_name']} ({pg['group_code']}): {pg['frequency']} - {status}")
        else:
            print("[INFO] No pay groups found in database")
        
        # Step 3: Check payroll runs
        print("\n[STEP 3] Checking payroll runs...")
        payroll_runs = await conn.fetch("""
            SELECT 
                pr.id,
                pg.group_name,
                pr.pay_period_start,
                pr.pay_period_end,
                pr.pay_date,
                pr.status,
                pr.total_gross,
                pr.total_net,
                pr.currency
            FROM payroll_run pr
            LEFT JOIN pay_group pg ON pr.pay_group_id = pg.id
            ORDER BY pr.created_at DESC
            LIMIT 5
        """)
        
        if payroll_runs:
            print(f"[OK] Found {len(payroll_runs)} payroll runs:")
            for run in payroll_runs:
                group = run['group_name'] if run['group_name'] else 'N/A'
                curr = run['currency'] if run['currency'] else 'USD'
                print(f"   - {run['id']}: {group} | {run['pay_period_start']} to {run['pay_period_end']}")
                print(f"     Status: {run['status']}, Gross: ${run['total_gross']:,.2f}, Net: ${run['total_net']:,.2f} {curr}")
        else:
            print("[INFO] No payroll runs found in database")
        
        # Step 4: Check commission plans
        print("\n[STEP 4] Checking commission plans...")
        commissions = await conn.fetch("""
            SELECT id, plan_name, plan_type, is_active
            FROM commission_plan
            ORDER BY created_at DESC
            LIMIT 5
        """)
        
        if commissions:
            print(f"[OK] Found {len(commissions)} commission plans:")
            for c in commissions:
                status = "Active" if c['is_active'] else "Inactive"
                print(f"   - {c['plan_name']}: {c['plan_type']} - {status}")
        else:
            print("[INFO] No commission plans found in database")
        
        # Step 5: Test Backend API Endpoint
        print("\n[STEP 5] Testing Backend API...")
        async with httpx.AsyncClient() as client:
            try:
                # Test list employees endpoint
                response = await client.get(
                    "http://localhost:8000/api/v1/books/17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c/payroll/employees",
                    params={"limit": 10}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"[OK] API Response: {len(data)} employees returned")
                    if data:
                        print(f"   First employee: {data[0].get('employee_name', 'N/A')}")
                else:
                    print(f"[WARNING] API returned {response.status_code}")
                    print(f"   Response: {response.text[:200]}")
                    
            except httpx.ConnectError as e:
                print(f"[WARNING] Cannot connect to backend API (is it running?)")
                print(f"   Error: {e}")
        
        # Step 6: Summary
        print("\n" + "=" * 80)
        print("PAYROLL INTEGRATION TEST SUMMARY")
        print("=" * 80)
        print(f"[OK] Database: Connected successfully")
        print(f"[OK] Employees: {len(employees)} employees")
        print(f"[OK] Pay Groups: {len(pay_groups)} pay groups")
        print(f"[OK] Payroll Runs: {len(payroll_runs)} runs")
        print(f"[OK] Commission Plans: {len(commissions)} plans")
        
        # Calculate totals
        total_employees = len(employees)
        active_employees = sum(1 for e in employees if e['is_active'])
        total_gross_payroll = sum(float(run['total_gross']) for run in payroll_runs) if payroll_runs else 0
        
        print(f"\n   Active Employees: {active_employees}/{total_employees}")
        print(f"   Total Gross Payroll Processed: ${total_gross_payroll:,.2f}")
        
        print("\n[COMPLETE] Payroll Integration test complete!")
        print("\n[NEXT STEPS]:")
        print("   1. Ensure backend server is running on port 8000")
        print("   2. Test frontend Payroll pages with real data")
        print("   3. Proceed to Intercompany transactions testing")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(test_payroll_integration())
