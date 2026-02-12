from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres.ififhzrbhadmtedyvzhb:Intakely%40786@aws-1-us-east-1.pooler.supabase.com:6543/postgres')
conn = engine.connect()

# List all tables
result = conn.execute(text("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema='public' 
    ORDER BY table_name
"""))
tables = [r[0] for r in result.fetchall()]

print(f"Total tables: {len(tables)}\n")
print("All tables:")
for t in tables:
    print(f"  - {t}")

# Check for CS onboarding tables
cs_tables = [t for t in tables if 'cs_' in t or 'onboarding' in t]
print(f"\nCS/Onboarding tables found: {len(cs_tables)}")
if cs_tables:
    for t in cs_tables:
        print(f"  - {t}")

# Check for FM tables
fm_core = ['legal_entity', 'book', 'dimension', 'gl_account', 'accounting_period', 'journal_entry', 'journal_line']
missing_fm = [t for t in fm_core if t not in tables]
print(f"\nCore FM tables present: {len([t for t in fm_core if t in tables])}/{len(fm_core)}")
if missing_fm:
    print("Missing FM tables:")
    for t in missing_fm:
        print(f"  - {t}")

conn.close()
