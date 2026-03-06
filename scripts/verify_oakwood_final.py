"""Verify Oakwood invoices and write results to file"""
import asyncio
import asyncpg
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

async def verify_and_log():
    # Try pooler URL first (recommended for async connections)
    db_url = os.getenv("FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL")
    if not db_url:
        db_url = os.getenv("DATABASE_URL") or os.getenv("FINANCIAL_MANAGEMENT_DATABASE_URL")
    
    if not db_url:
        with open("logs/verification.log", "w") as f:
            f.write("ERROR: No database URL found in environment variables\n")
        print("ERROR: No database URL found")
        return
    
    # Convert for asyncpg if needed
    if "+asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    
    print(f"Connecting to: {db_url[:60]}...")
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Get customer
        customer = await conn.fetchrow("""
            SELECT id, customer_code, customer_name, external_customer_id
            FROM ar_customer
            WHERE external_customer_id = 'e2362e1c-759a-402d-9b38-2eab1ae8ad3f'
        """)
        
        lines = []
        lines.append(f"Verification Report - {datetime.now().isoformat()}")
        lines.append("=" * 80)
        
        if not customer:
            lines.append("❌ Customer NOT FOUND")
            with open("logs/verification.log", "w") as f:
                f.write("\n".join(lines))
            print("\n".join(lines))
            return
        
        lines.append(f"\n✅ Customer Found:")
        lines.append(f"   Name: {customer['customer_name']}")
        lines.append(f"   Code: {customer['customer_code']}")
        lines.append(f"   ID: {customer['id']}")
        lines.append(f"   External ID: {customer['external_customer_id']}")
        
        # Get invoices
        invoices = await conn.fetch("""
            SELECT 
                invoice_number,
                total_amount,
                outstanding_amount,
                status,
                due_date,
                created_at
            FROM ar_invoice
            WHERE legal_entity_id = $1
            ORDER BY created_at DESC
        """, customer['id'])
        
        lines.append(f"\n📄 Invoices Found: {len(invoices)}")
        lines.append("-" * 80)
        
        total_revenue = 0
        total_outstanding = 0
        overdue_count = 0
        
        from datetime import date
        
        for inv in invoices:
            amount = float(inv['total_amount'])
            outstanding = float(inv['outstanding_amount'])
            total_revenue += amount
            total_outstanding += outstanding
            
            # Calculate if overdue
            is_overdue = inv['status'] == 'ISSUED' and inv['due_date'] and inv['due_date'] < date.today() and outstanding > 0
            if is_overdue:
                days_overdue = (date.today() - inv['due_date']).days
                overdue_count += 1
            else:
                days_overdue = None
            
            status_marker = "⚠️ OVERDUE" if is_overdue else "✅"
            lines.append(f"\n{status_marker} {inv['invoice_number']}")
            lines.append(f"   Amount: ${amount:,.2f}")
            lines.append(f"   Outstanding: ${outstanding:,.2f}")
            lines.append(f"   Status: {inv['status']}")
            lines.append(f"   Due Date: {inv['due_date']}")
            if is_overdue:
                lines.append(f"   Days Overdue: {days_overdue}")
            lines.append(f"   Created: {inv['created_at']}")
        
        lines.append("\n" + "=" * 80)
        lines.append(f"💰 SUMMARY:")
        lines.append(f"   Total Invoices: {len(invoices)}")
        lines.append(f"   Total Revenue: ${total_revenue:,.2f}")
        lines.append(f"   Total Outstanding: ${total_outstanding:,.2f}")
        lines.append(f"   Total Paid: ${(total_revenue - total_outstanding):,.2f}")
        lines.append(f"   Overdue Count: {overdue_count}")
        
        # Write to log file
        with open("logs/verification.log", "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        # Also print to console
        print("\n".join(lines))
        
        # Test dashboard API
        lines.append("\n" + "=" * 80)
        lines.append("🧪 Dashboard API Test:")
        
        import httpx
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "http://localhost:8000/api/v1/dashboard/stats",
                    params={"legal_entity_id": str(customer['id'])}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    lines.append(f"   ✅ Status: 200 OK")
                    lines.append(f"   Overdue Invoices: {data.get('overdue_invoices', 'N/A')}")
                    lines.append(f"   Upcoming Payments: {data.get('upcoming_payments', 'N/A')}")
                    lines.append(f"   Pending Approvals: {data.get('pending_approvals', 'N/A')}")
                    
                    # Verify overdue count matches
                    if data.get('overdue_invoices') == overdue_count:
                        lines.append(f"   ✅ Overdue count MATCHES ({overdue_count})")
                    else:
                        lines.append(f"   ⚠️ Overdue count MISMATCH: API={data.get('overdue_invoices')}, DB={overdue_count}")
                else:
                    lines.append(f"   ❌ Status: {response.status_code}")
                    lines.append(f"   Response: {response.text[:200]}")
            except Exception as e:
                lines.append(f"   ❌ Error: {str(e)}")
        
        # Update log
        with open("logs/verification.log", "w") as f:
            f.write("\n".join(lines))
        
        print("\n".join(lines[-10:]))
        print(f"\n✅ Full report saved to: logs/verification.log")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(verify_and_log())
