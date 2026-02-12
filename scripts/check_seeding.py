from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres.ififhzrbhadmtedyvzhb:Intakely%40786@aws-1-us-east-1.pooler.supabase.com:6543/postgres')
conn = engine.connect()

# Check legal_entity
result = conn.execute(text("SELECT code, name FROM legal_entity ORDER BY code"))
entities = result.fetchall()
print(f"Legal Entities: {len(entities)}")
for e in entities:
    print(f"  - {e[0]}: {e[1]}")

# Check book
result = conn.execute(text("SELECT COUNT(*) FROM book"))
book_count = result.scalar()
print(f"\nBooks: {book_count}")

# Check dimension
result = conn.execute(text("SELECT code, name FROM dimension ORDER BY code"))
dims = result.fetchall()
print(f"\nDimensions: {len(dims)}")
for d in dims:
    print(f"  - {d[0]}: {d[1]}")

# Check accounting_period
result = conn.execute(text("SELECT COUNT(*) FROM accounting_period"))
period_count = result.scalar()
print(f"\nAccounting Periods: {period_count}")

conn.close()
