from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres.ififhzrbhadmtedyvzhb:Intakely%40786@aws-1-us-east-1.pooler.supabase.com:6543/postgres')
conn = engine.connect()

# Check idempotency_keys
result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='idempotency_keys'"))
idem_exists = result.scalar()
print(f"idempotency_keys table exists: {idem_exists > 0}")

if idem_exists:
    result = conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='idempotency_keys' ORDER BY ordinal_position"))
    cols = [r[0] for r in result.fetchall()]
    print(f"  Columns: {', '.join(cols)}")

# Check audit_log  
result = conn.execute(text("SELECT COUNT(*) FROM information_schema.tables WHERE table_name='audit_log'"))
audit_exists = result.scalar()
print(f"\naudit_log table exists: {audit_exists > 0}")

# Check migration history
result = conn.execute(text("SELECT version_num FROM alembic_version"))
version = result.scalar()
print(f"\nCurrent migration version: {version}")

conn.close()
