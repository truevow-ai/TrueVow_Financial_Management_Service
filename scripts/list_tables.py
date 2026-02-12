from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres.ififhzrbhadmtedyvzhb:Intakely%40786@aws-1-us-east-1.pooler.supabase.com:6543/postgres')
with engine.connect() as conn:
    result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"))
    print('\n'.join([r[0] for r in result]))
