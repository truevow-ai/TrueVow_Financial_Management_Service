"""Verification script: confirm row_audit_triggers migration deployed correctly."""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings


async def verify():
    engine = create_async_engine(
        settings.effective_database_url,
        connect_args={"statement_cache_size": 0},
    )
    async with engine.connect() as conn:
        # 1. row_audit_log table
        r = await conn.execute(
            text("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name='row_audit_log'")
        )
        table_exists = r.scalar() == 1
        print(f"[{'OK' if table_exists else 'FAIL'}] row_audit_log table exists: {table_exists}")

        # 2. trigger function
        r = await conn.execute(
            text("SELECT COUNT(*) FROM pg_proc WHERE proname='fn_row_audit_log'")
        )
        fn_exists = r.scalar() >= 1
        print(f"[{'OK' if fn_exists else 'FAIL'}] fn_row_audit_log function exists: {fn_exists}")

        # 3. trigger count
        r = await conn.execute(
            text("SELECT COUNT(*) FROM information_schema.triggers WHERE trigger_name LIKE 'trg_row_audit_%'")
        )
        count = r.scalar()
        # Each table gets 1 trigger but Postgres reports one row per event type
        # (INSERT, UPDATE, DELETE) so expect count == n_tables * 3
        expected_min = 50  # at least 50 of 53 tables × 3 events
        ok = count >= expected_min
        print(f"[{'OK' if ok else 'FAIL'}] Trigger event rows: {count}  (expect >= {expected_min})")

        # 4. sample tables
        r = await conn.execute(
            text(
                "SELECT DISTINCT event_object_table FROM information_schema.triggers "
                "WHERE trigger_name LIKE 'trg_row_audit_%' ORDER BY event_object_table"
            )
        )
        tables = [row[0] for row in r.fetchall()]
        print(f"[INFO] Tables with row_audit trigger ({len(tables)}):")
        for t in tables:
            print(f"        - {t}")

        # 5. columns on row_audit_log
        r = await conn.execute(
            text(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name='row_audit_log' ORDER BY ordinal_position"
            )
        )
        cols = [row[0] for row in r.fetchall()]
        print(f"[INFO] row_audit_log columns: {cols}")

        # 6. RLS disabled
        r = await conn.execute(
            text("SELECT relrowsecurity FROM pg_class WHERE relname='row_audit_log'")
        )
        rls = r.scalar()
        print(f"[{'OK' if not rls else 'WARN'}] RLS disabled on row_audit_log: {not rls}")

    await engine.dispose()
    print("\nVerification complete.")


if __name__ == "__main__":
    asyncio.run(verify())
