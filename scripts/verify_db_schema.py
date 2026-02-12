#!/usr/bin/env python3
"""
Verify DB schema for idempotency and source_key.
Run with: DATABASE_URL or FINANCIAL_MANAGEMENT_DATABASE_URL set.
Prints column lists for idempotency_keys and journal_entry.
"""
import os
import sys

def main():
    url = os.environ.get("DATABASE_URL") or os.environ.get("FINANCIAL_MANAGEMENT_DATABASE_URL")
    if not url:
        print("Set DATABASE_URL or FINANCIAL_MANAGEMENT_DATABASE_URL", file=sys.stderr)
        sys.exit(1)
    # Use sync driver for inspection
    if url.startswith("postgresql+asyncpg"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif "postgres://" in url:
        url = url.replace("postgres://", "postgresql://", 1)
    from sqlalchemy import create_engine, inspect
    engine = create_engine(url)
    inspector = inspect(engine)
    for table in ["idempotency_keys", "journal_entry"]:
        if table not in inspector.get_table_names():
            print(f"{table}: MISSING", file=sys.stderr)
            continue
        cols = [c["name"] for c in inspector.get_columns(table)]
        print(f"{table}: {', '.join(cols)}")
    print("OK")

if __name__ == "__main__":
    main()
