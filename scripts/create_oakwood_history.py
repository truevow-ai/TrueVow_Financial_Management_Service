import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def create_history():
    db_url = os.getenv('FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL')
    
    if not db_url:
        print("ERROR: Database URL not found")
        return
    
    conn = await asyncpg.connect(db_url)
    
    print("=" * 80)
    print("ADDING OAKWOOD LAW FIRM - HISTORICAL INVOICES")
    print("=" * 80)
    
    # Get customer
    customer = await conn.fetchrow("""
        SELECT id FROM ar_customer 
        WHERE customer_code = 'OAKWOOD-LAW'
    """)
    
    if not customer:
        print("No Oakwood Law Firm customer found")
        await conn.close()
        return
    
    customer_id = customer['id']
    
    # Create historical invoices based on SOLO 24/7 tier usage patterns
    invoices_data = [
        # Month 1: Typical usage (8 unlocks @ $99 = $792) - Fully Paid
        ('INV-OAKWOOD-002', 'ext-inv-oakwood-002', 90, 75, 'ISSUED', 792.00, 0.00),
        
        # Month 2: Low usage (6 unlocks @ $99 = $594) - Fully Paid  
        ('INV-OAKWOOD-003', 'ext-inv-oakwood-003', 60, 45, 'ISSUED', 594.00, 0.00),
        
        # Month 3: High usage (10 unlocks @ $99 = $990) - Partially Paid ($590 paid, $400 outstanding)
        ('INV-OAKWOOD-004', 'ext-inv-oakwood-004', 30, 15, 'ISSUED', 990.00, 400.00),
    ]
    
    print("\nCreating invoices:")
    for inv_data in invoices_data:
        try:
            # Calculate dates in Python
            from datetime import timedelta, date
            issue_date = date.today() - timedelta(days=inv_data[2])
            due_date = date.today() - timedelta(days=inv_data[3])
            
            await conn.execute("""
                INSERT INTO ar_invoice (
                    legal_entity_id, ar_customer_id, invoice_number, 
                    external_invoice_id, invoice_date, due_date,
                    status, total_amount, outstanding_amount, currency
                )
                VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, 'USD'
                )
                ON CONFLICT (external_invoice_id) DO NOTHING
            """, 
                '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c',  # legal_entity_id
                customer_id,
                inv_data[0],  # invoice_number
                inv_data[1],  # external_invoice_id
                issue_date,
                due_date,
                inv_data[4],  # status
                inv_data[5],  # total_amount
                inv_data[6]   # outstanding_amount
            )
            print(f"[OK] Created {inv_data[0]}: ${inv_data[5]:.2f} (Outstanding: ${inv_data[6]:.2f})")
        except Exception as e:
            print(f"[ERROR] Failed to create {inv_data[0]}: {e}")
    
    # Verification
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    
    invoices = await conn.fetch("""
        SELECT invoice_number, total_amount, outstanding_amount, invoice_date
        FROM ar_invoice
        WHERE ar_customer_id = $1
        ORDER BY invoice_date DESC
    """, customer_id)
    
    total_revenue = sum(inv['total_amount'] for inv in invoices)
    total_outstanding = sum(inv['outstanding_amount'] for inv in invoices)
    
    print(f"\nTotal Invoices: {len(invoices)}")
    print(f"Total Revenue: ${total_revenue:.2f}")
    print(f"Total Outstanding: ${total_outstanding:.2f}")
    print(f"Total Collected: ${total_revenue - total_outstanding:.2f}")
    
    await conn.close()

asyncio.run(create_history())
