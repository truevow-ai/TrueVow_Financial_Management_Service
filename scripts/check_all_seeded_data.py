from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres.ififhzrbhadmtedyvzhb:Intakely%40786@aws-1-us-east-1.pooler.supabase.com:6543/postgres')
conn = engine.connect()

print("=== SEEDED DATA VERIFICATION ===\n")

# Legal Entity
result = conn.execute(text("SELECT code, name, country, functional_currency FROM legal_entity ORDER BY code"))
entities = result.fetchall()
print(f"1. LEGAL_ENTITY ({len(entities)} rows):")
for row in entities:
    print(f"   {row[0]}: {row[1]} ({row[2]}, {row[3]})")

# Book
result = conn.execute(text("""
    SELECT b.book_type, le.code, le.name 
    FROM book b 
    JOIN legal_entity le ON b.legal_entity_id = le.id 
    ORDER BY le.code, b.book_type
"""))
books = result.fetchall()
print(f"\n2. BOOK ({len(books)} rows):")
for row in books:
    print(f"   {row[1]} - {row[0]}")

# Dimension
result = conn.execute(text("SELECT code, name FROM dimension ORDER BY code"))
dims = result.fetchall()
print(f"\n3. DIMENSION ({len(dims)} rows):")
for row in dims:
    print(f"   {row[0]}: {row[1]}")

# Dimension Value
result = conn.execute(text("""
    SELECT d.code, COUNT(*) as value_count
    FROM dimension d
    LEFT JOIN dimension_value dv ON d.id = dv.dimension_id
    GROUP BY d.code
    ORDER BY d.code
"""))
dim_values = result.fetchall()
print(f"\n4. DIMENSION_VALUE (by dimension):")
for row in dim_values:
    print(f"   {row[0]}: {row[1]} values")

# Accounting Period
result = conn.execute(text("SELECT COUNT(*) FROM accounting_period"))
period_count = result.scalar()
print(f"\n5. ACCOUNTING_PERIOD ({period_count} rows)")

# GL Account
result = conn.execute(text("SELECT COUNT(*) FROM gl_account"))
coa_count = result.scalar()
print(f"\n6. GL_ACCOUNT ({coa_count} rows)")

# AR Customer
result = conn.execute(text("SELECT COUNT(*) FROM ar_customer"))
ar_count = result.scalar()
print(f"\n7. AR_CUSTOMER ({ar_count} rows)")

# AP Vendor
result = conn.execute(text("SELECT COUNT(*) FROM ap_vendor"))
ap_count = result.scalar()
print(f"\n8. AP_VENDOR ({ap_count} rows)")

# HR Employee
result = conn.execute(text("SELECT COUNT(*) FROM hr_employee"))
emp_count = result.scalar()
print(f"\n9. HR_EMPLOYEE ({emp_count} rows)")

# Journal Entry
result = conn.execute(text("SELECT COUNT(*) FROM journal_entry"))
je_count = result.scalar()
print(f"\n10. JOURNAL_ENTRY ({je_count} rows)")

# Check for other empty critical tables
empty_tables = []
critical_tables = [
    'gl_account_mapping',
    'ar_invoice',
    'ap_bill',
    'payroll_run',
    'revenue_schedule',
    'commission_plan',
    'bonus_plan',
    'affiliate_partner',
    'treasury_bank_account',
    'reconciliation_session'
]

for table in critical_tables:
    result = conn.execute(text(f"SELECT COUNT(*) FROM {table}"))
    count = result.scalar()
    if count == 0:
        empty_tables.append(table)

print(f"\n=== EMPTY CRITICAL TABLES ({len(empty_tables)}) ===")
for table in empty_tables:
    print(f"   - {table}")

conn.close()

print("\n=== SUMMARY ===")
print(f"Only 4 tables seeded: legal_entity, book, dimension, dimension_value")
print(f"Missing seed data: CoA, periods, employees, vendors, customers, etc.")
