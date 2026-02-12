from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres.ififhzrbhadmtedyvzhb:Intakely%40786@aws-1-us-east-1.pooler.supabase.com:6543/postgres')
conn = engine.connect()

result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='dimension_value' ORDER BY ordinal_position"))
print("dimension_value columns:")
for r in result.fetchall():
    print(f"  - {r[0]} ({r[1]})")

# Check dimension values
result = conn.execute(text("SELECT dimension_code, value_code, value_name FROM dimension_value ORDER BY dimension_code, value_code"))
values = result.fetchall()
print(f"\nTotal dimension_value rows: {len(values)}")
for row in values:
    print(f"  {row[0]} -> {row[1]}: {row[2]}")

conn.close()
