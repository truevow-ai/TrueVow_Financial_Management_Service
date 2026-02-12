from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres.ififhzrbhadmtedyvzhb:Intakely%40786@aws-1-us-east-1.pooler.supabase.com:6543/postgres')
conn = engine.connect()
result = conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='accounting_period' ORDER BY ordinal_position"))
for r in result:
    print(f'{r[0]}: {r[1]}')
conn.close()
