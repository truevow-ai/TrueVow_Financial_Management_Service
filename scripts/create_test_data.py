"""
Database test data insertion script
Connects to Supabase PostgreSQL and creates test data for dashboard stats
"""
import asyncio
import asyncpg
import os
from pathlib import Path
from dotenv import load_dotenv

# Load from .env.local in project root
env_path = Path(__file__).parent.parent / '.env.local'
load_dotenv(env_path)

async def create_test_data():
    # Get database URL from environment - try pooler first as it's more reliable
    db_url = os.getenv('FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL')
    
    if not db_url:
        print("SESSION_POOLER_URL not found, trying DATABASE_URL")
        db_url = os.getenv('FINANCIAL_MANAGEMENT_DATABASE_URL')
    
    if not db_url:
        print("No database URL found in .env.local")
        return
    
    print("Using database connection")
    print("   Connection string length:", len(db_url), "chars")
    
    try:
        # Connect to database
        conn = await asyncpg.connect(db_url)
        print("Connected successfully!")
        
        # Step 1: Get active legal entity
        entity = await conn.fetchrow("""
            SELECT id, name, functional_currency 
            FROM legal_entity 
            WHERE is_active = true 
            ORDER BY created_at DESC LIMIT 1
        """)
        
        if not entity:
            print("No active legal entities found")
            await conn.close()
            return
        
        entity_id = entity['id']
        currency = entity['functional_currency']
        print("Using legal entity:", entity['name'], f"({entity_id})")
        
        # Step 2: Create or get book
        book = await conn.fetchrow("""
            SELECT id FROM book 
            WHERE legal_entity_id = $1 
            ORDER BY created_at DESC LIMIT 1
        """, entity_id)
        
        if not book:
            await conn.execute("""
                INSERT INTO book (legal_entity_id, book_type, name, is_active)
                VALUES ($1, 'ACCRUAL', 'Main Book', true)
            """, entity_id)
            book = await conn.fetchrow("""
                SELECT id FROM book 
                WHERE legal_entity_id = $1 
                ORDER BY created_at DESC LIMIT 1
            """, entity_id)
        
        book_id = book['id']
        print("Using book:", book_id)
        
        # Step 3: Check accounting_period structure
        columns = await conn.fetch("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'accounting_period' 
            ORDER BY ordinal_position
        """)
        
        has_period_start = any(c['column_name'] == 'period_start' for c in columns)
        has_start_date = any(c['column_name'] == 'start_date' for c in columns)
        
        period_column = 'period_start' if has_period_start else ('start_date' if has_start_date else None)
        end_column = 'period_end' if has_period_start else ('end_date' if has_start_date else None)
        
        if not period_column:
            print("Could not find period date columns")
            await conn.close()
            return
        
        # Create period
        await conn.execute(f"""
            INSERT INTO accounting_period (book_id, {period_column}, {end_column}, period_name, status)
            VALUES ($1, DATE_TRUNC('month', CURRENT_DATE), 
                    (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' - INTERVAL '1 day')::date,
                    'Current Month', 'OPEN')
            ON CONFLICT DO NOTHING
        """, book_id)
        
        period = await conn.fetchrow(f"""
            SELECT id FROM accounting_period 
            WHERE book_id = $1 
            ORDER BY created_at DESC LIMIT 1
        """, book_id)
        
        period_id = period['id']
        print("Created accounting period:", period_id)
        
        # Step 4: Create GL accounts
        accounts_data = [
            ('1010', 'Cash - Operating Account', 'ASSET'),
            ('1200', 'Accounts Receivable', 'ASSET'),
            ('2000', 'Accounts Payable', 'LIABILITY'),
            ('4100', 'Service Revenue', 'REVENUE'),
            ('5100', 'Operating Expenses', 'EXPENSE')
        ]
        
        for code, name, acc_type in accounts_data:
            await conn.execute("""
                INSERT INTO gl_account (book_id, account_code, account_name, account_type, is_active)
                VALUES ($1, $2, $3, $4, true)
                ON CONFLICT DO NOTHING
            """, book_id, code, name, acc_type)
        
        print("Created GL accounts")
        
        # Get account IDs
        cash_acc = await conn.fetchval("SELECT id FROM gl_account WHERE account_code = '1010' AND book_id = $1", book_id)
        ar_acc = await conn.fetchval("SELECT id FROM gl_account WHERE account_code = '1200' AND book_id = $1", book_id)
        ap_acc = await conn.fetchval("SELECT id FROM gl_account WHERE account_code = '2000' AND book_id = $1", book_id)
        rev_acc = await conn.fetchval("SELECT id FROM gl_account WHERE account_code = '4100' AND book_id = $1", book_id)
        exp_acc = await conn.fetchval("SELECT id FROM gl_account WHERE account_code = '5100' AND book_id = $1", book_id)
        
        print("   Cash:", cash_acc, ", AR:", ar_acc, ", AP:", ap_acc, ", Revenue:", rev_acc, ", Expense:", exp_acc)
        
        # Step 5: Check journal_entry structure
        je_columns = await conn.fetch("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'journal_entry' 
            ORDER BY ordinal_position
        """)
        
        has_legal_entity = any(c['column_name'] == 'legal_entity_id' for c in je_columns)
        
        # Create journal entry (with or without legal_entity_id based on schema)
        if has_legal_entity:
            await conn.execute("""
                INSERT INTO journal_entry (book_id, period_id, legal_entity_id, entry_date, description, status, entry_number)
                VALUES ($1, $2, $3, CURRENT_DATE - INTERVAL '30 days', 'Test opening balances', 'POSTED', 'JE-TEST-001')
                ON CONFLICT DO NOTHING
            """, book_id, period_id, entity_id)
        else:
            await conn.execute("""
                INSERT INTO journal_entry (book_id, period_id, entry_date, description, status, entry_number)
                VALUES ($1, $2, CURRENT_DATE - INTERVAL '30 days', 'Test opening balances', 'POSTED', 'JE-TEST-001')
                ON CONFLICT DO NOTHING
            """, book_id, period_id)
        
        je = await conn.fetchrow("""
            SELECT id FROM journal_entry 
            WHERE book_id = $1 AND period_id = $2
            ORDER BY created_at DESC LIMIT 1
        """, book_id, period_id)
        
        if je:
            je_id = je['id']
            print("Created journal entry:", je_id)
            
            # Create journal lines (check if they exist first)
            existing_lines = await conn.fetchval("SELECT COUNT(*) FROM journal_line WHERE journal_entry_id = $1", je_id)
            
            if existing_lines == 0:
                await conn.execute("""
                    INSERT INTO journal_line (journal_entry_id, book_id, gl_account_id, line_number, debit_tc, credit_tc, currency)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, je_id, book_id, cash_acc, 1, 50000.00, 0, currency)
                
                await conn.execute("""
                    INSERT INTO journal_line (journal_entry_id, book_id, gl_account_id, line_number, debit_tc, credit_tc, currency)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, je_id, book_id, rev_acc, 2, 0, 85000.00, currency)
                
                await conn.execute("""
                    INSERT INTO journal_line (journal_entry_id, book_id, gl_account_id, line_number, debit_tc, credit_tc, currency)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, je_id, book_id, exp_acc, 3, 35000.00, 0, currency)
                
                await conn.execute("""
                    INSERT INTO journal_line (journal_entry_id, book_id, gl_account_id, line_number, debit_tc, credit_tc, currency)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, je_id, book_id, ar_acc, 4, 15000.00, 0, currency)
                
                await conn.execute("""
                    INSERT INTO journal_line (journal_entry_id, book_id, gl_account_id, line_number, debit_tc, credit_tc, currency)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, je_id, book_id, ap_acc, 5, 0, 20000.00, currency)
                
                print("Created journal lines")
            else:
                print("Journal lines already exist:", existing_lines, "lines")
        
        # Step 6: Create AR customer - minimal required columns only
        try:
            # Check ar_customer structure first
            customer_cols = await conn.fetch("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'ar_customer' 
                ORDER BY ordinal_position
            """)
            
            has_external_id = any(c['column_name'] == 'external_customer_id' for c in customer_cols)
            has_customer_name = any(c['column_name'] == 'customer_name' for c in customer_cols)
            
            # Use the actual Clerk user ID and tenant ID from your setup
            clerk_user_id = 'user_3AAyZIRG4YnytBM6TiL3DsRGQjJ'
            tenant_id = 'e2362e1c-759a-402d-9b38-2eab1ae8ad3f'
            
            if has_external_id and has_customer_name:
                customer = await conn.fetchrow("""
                    INSERT INTO ar_customer (legal_entity_id, customer_code, external_customer_id, customer_name)
                    VALUES ($1, 'OAKWOOD-LAW', $2, 'Oakwood Law Firm')
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """, entity_id, tenant_id)
            elif has_external_id:
                customer = await conn.fetchrow("""
                    INSERT INTO ar_customer (legal_entity_id, customer_code, external_customer_id)
                    VALUES ($1, 'OAKWOOD-LAW', $2)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """, entity_id, tenant_id)
            elif has_customer_name:
                customer = await conn.fetchrow("""
                    INSERT INTO ar_customer (legal_entity_id, customer_code, customer_name)
                    VALUES ($1, 'OAKWOOD-LAW', 'Oakwood Law Firm')
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """, entity_id)
            else:
                customer = await conn.fetchrow("""
                    INSERT INTO ar_customer (legal_entity_id, customer_code)
                    VALUES ($1, 'OAKWOOD-LAW')
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """, entity_id)
        except Exception as e:
            print("Could not create customer:", e)
            customer = None
        
        if customer:
            customer_id = customer['id']
            print("Created customer: Oakwood Law Firm (ID:", customer_id, ")")
        else:
            # Try to get existing customer
            customer = await conn.fetchrow("""
                SELECT id FROM ar_customer 
                WHERE legal_entity_id = $1 AND customer_code = 'OAKWOOD-LAW'
                ORDER BY created_at DESC LIMIT 1
            """, entity_id)
            if customer:
                customer_id = customer['id']
                print("Using existing customer: Oakwood Law Firm (ID:", customer_id, ")")
        
        if customer:
            # Check ar_invoice structure
            invoice_cols = await conn.fetch("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'ar_invoice' 
                ORDER BY ordinal_position
            """)
            
            has_ar_customer_id = any(c['column_name'] == 'ar_customer_id' for c in invoice_cols)
            
            # Build the insert based on available columns
            if has_ar_customer_id:
                await conn.execute("""
                    INSERT INTO ar_invoice (
                        legal_entity_id, ar_customer_id, invoice_number, external_invoice_id, invoice_date, due_date, 
                        status, total_amount, outstanding_amount, currency
                    )
                    VALUES (
                        $1, $2, 'INV-OAKWOOD-001', 'ext-inv-oakwood-001',
                        CURRENT_DATE - INTERVAL '60 days',
                        CURRENT_DATE - INTERVAL '15 days',
                        'ISSUED', 5000.00, 5000.00, $3
                    )
                    ON CONFLICT DO NOTHING
                """, entity_id, customer_id, currency)
            elif has_external_customer_id:
                await conn.execute("""
                    INSERT INTO ar_invoice (
                        legal_entity_id, customer_id, invoice_number, issue_date, due_date, 
                        status, total_amount, outstanding_amount, currency
                    )
                    VALUES (
                        $1, $2, 'INV-TEST-001',
                        CURRENT_DATE - INTERVAL '60 days',
                        CURRENT_DATE - INTERVAL '15 days',
                        'ISSUED', 5000.00, 5000.00, $3
                    )
                    ON CONFLICT DO NOTHING
                """, entity_id, customer_id, currency)
            elif has_external_customer_id:
                await conn.execute("""
                    INSERT INTO ar_invoice (
                        legal_entity_id, external_customer_id, invoice_number, issue_date, due_date, 
                        status, total_amount, outstanding_amount, currency
                    )
                    VALUES (
                        $1, $2, 'INV-TEST-001',
                        CURRENT_DATE - INTERVAL '60 days',
                        CURRENT_DATE - INTERVAL '15 days',
                        'ISSUED', 5000.00, 5000.00, $3
                    )
                    ON CONFLICT DO NOTHING
                """, entity_id, 'ext-cust-001', currency)
            else:
                print("Could not determine customer reference column for ar_invoice")
            
            print("Created overdue AR invoice")
        
        # Step 7: Create AP vendor - minimal required columns only
        try:
            # Check ap_vendor structure first
            vendor_cols = await conn.fetch("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'ap_vendor' 
                ORDER BY ordinal_position
            """)
            
            has_vendor_name = any(c['column_name'] == 'vendor_name' for c in vendor_cols)
            has_default_currency = any(c['column_name'] == 'default_currency' for c in vendor_cols)
            
            if has_vendor_name and has_default_currency:
                vendor = await conn.fetchrow("""
                    INSERT INTO ap_vendor (legal_entity_id, vendor_code, vendor_name, default_currency)
                    VALUES ($1, 'LEGAL-SUPPLY', 'Legal Supplies & Services LLC', $2)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """, entity_id, currency)
            elif has_vendor_name:
                vendor = await conn.fetchrow("""
                    INSERT INTO ap_vendor (legal_entity_id, vendor_code, vendor_name)
                    VALUES ($1, 'LEGAL-SUPPLY', 'Legal Supplies & Services LLC')
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """, entity_id)
            elif has_default_currency:
                vendor = await conn.fetchrow("""
                    INSERT INTO ap_vendor (legal_entity_id, vendor_code, default_currency)
                    VALUES ($1, 'LEGAL-SUPPLY', $2)
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """, entity_id, currency)
            else:
                vendor = await conn.fetchrow("""
                    INSERT INTO ap_vendor (legal_entity_id, vendor_code)
                    VALUES ($1, 'LEGAL-SUPPLY')
                    ON CONFLICT DO NOTHING
                    RETURNING id
                """, entity_id)
        except Exception as e:
            print("Could not create vendor:", e)
            vendor = None
        
        if vendor:
            vendor_id = vendor['id']
            print("Created vendor: Legal Supplies & Services (ID:", vendor_id, ")")
        else:
            # Try to get existing vendor
            vendor = await conn.fetchrow("""
                SELECT id FROM ap_vendor 
                WHERE legal_entity_id = $1 AND vendor_code = 'LEGAL-SUPPLY'
                ORDER BY created_at DESC LIMIT 1
            """, entity_id)
            if vendor:
                vendor_id = vendor['id']
                print("Using existing vendor: Legal Supplies & Services (ID:", vendor_id, ")")
            
            # Check ap_bill structure for vendor reference
            bill_cols = await conn.fetch("""
                SELECT column_name FROM information_schema.columns 
                WHERE table_name = 'ap_bill' 
                ORDER BY ordinal_position
            """)
            
            has_vendor_id = any(c['column_name'] == 'ap_vendor_id' for c in bill_cols)
            
            if has_vendor_id:
                await conn.execute("""
                    INSERT INTO ap_bill (
                        legal_entity_id, book_id, ap_vendor_id, bill_number, bill_date, due_date,
                        status, total_amount, outstanding_amount, currency
                    )
                    VALUES (
                        $1, $2, $3, 'BILL-LEGAL-001',
                        CURRENT_DATE - INTERVAL '10 days',
                        CURRENT_DATE + INTERVAL '5 days',
                        'approved', 7500.00, 7500.00, $4
                    )
                    ON CONFLICT DO NOTHING
                """, entity_id, book_id, vendor_id, currency)
            else:
                print("Could not find ap_vendor_id column in ap_bill")
            
            print("Created upcoming AP bill")
        
        # Final verification
        print("\nVerification:")
        counts = await conn.fetch("""
            SELECT 'legal_entity' as table_name, COUNT(*) as count FROM legal_entity WHERE is_active = true
            UNION ALL SELECT 'gl_account', COUNT(*) FROM gl_account
            UNION ALL SELECT 'journal_entry', COUNT(*) FROM journal_entry
            UNION ALL SELECT 'journal_line', COUNT(*) FROM journal_line
            UNION ALL SELECT 'ar_invoice', COUNT(*) FROM ar_invoice
            UNION ALL SELECT 'ap_bill', COUNT(*) FROM ap_bill
        """)
        
        for row in counts:
            print("  ", row['table_name'], ":", row['count'])
        
        await conn.close()
        print("\nTest data creation complete!")
        
    except Exception as e:
        print("\nError:", e)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_test_data())
