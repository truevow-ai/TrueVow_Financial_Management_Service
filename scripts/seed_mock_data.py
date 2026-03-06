#!/usr/bin/env python3
"""
Seed mock data for Oakwood Law Firm scenario — INTAKELY_PAK entity.
Uses the exact same proven pattern as deploy_compliance.py.
Safe to re-run (all statements are idempotent).
"""
import asyncio
import asyncpg
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

# Force UTF-8 output on Windows (box-drawing chars in SQL comments)
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

load_dotenv()
load_dotenv('.env.local')

BASE_DIR  = Path(__file__).parent.parent
SQL_FILE  = BASE_DIR / 'database' / 'migrations' / 'mock_data' / '001_oakwood_mock_data.sql'
LOG_FILE  = BASE_DIR / 'logs' / 'seed_mock_data.log'

RAW_URL = os.getenv(
    'FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL',
    os.getenv('FINANCIAL_MANAGEMENT_DATABASE_URL', '')
)
DB_URL = RAW_URL.replace('postgresql+asyncpg://', 'postgresql://')

log_lines: list[str] = []


def log(msg: str):
    print(msg)
    log_lines.append(msg)


_DOLLAR_TAG_RE = re.compile(r'\$([A-Za-z_][A-Za-z0-9_]*)\$|\$\$')


def split_sql_statements(sql: str) -> tuple[list[str], list[str]]:
    """Identical parser to deploy_compliance.py — battle-tested."""
    ddl_stmts: list[str] = []
    sel_stmts: list[str] = []
    i = 0
    n = len(sql)
    current: list[str] = []
    in_line_comment  = False
    in_block_comment = False
    in_single_quote  = False
    dollar_tag: str | None = None

    while i < n:
        ch = sql[i]
        if in_line_comment:
            current.append(ch)
            if ch == '\n':
                in_line_comment = False
            i += 1
            continue
        if in_block_comment:
            current.append(ch)
            if sql[i:i+2] == '*/':
                current.append('/')
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue
        if in_single_quote:
            current.append(ch)
            if ch == "'" and sql[i:i+2] != "''":
                in_single_quote = False
            elif ch == "'" and sql[i:i+2] == "''":
                current.append("'")
                i += 2
                continue
            i += 1
            continue
        if dollar_tag is not None:
            closing = dollar_tag
            if sql[i:i+len(closing)] == closing:
                current.append(closing)
                dollar_tag = None
                i += len(closing)
            else:
                current.append(ch)
                i += 1
            continue
        if sql[i:i+2] == '--':
            in_line_comment = True
            current.append(ch)
            i += 1
            continue
        if sql[i:i+2] == '/*':
            in_block_comment = True
            current.append(ch)
            i += 1
            continue
        if ch == "'":
            in_single_quote = True
            current.append(ch)
            i += 1
            continue
        m = _DOLLAR_TAG_RE.match(sql, i)
        if m:
            tag = m.group(0)
            dollar_tag = tag
            current.append(tag)
            i += len(tag)
            continue
        if ch == ';':
            stmt = ''.join(current).strip()
            current = []
            stmt_clean = re.sub(r'--[^\n]*', '', stmt).strip()
            stmt_clean = re.sub(r'/\*.*?\*/', '', stmt_clean, flags=re.DOTALL).strip()
            if stmt_clean:
                keyword = stmt_clean.split()[0].upper() if stmt_clean.split() else ''
                if keyword == 'SELECT':
                    sel_stmts.append(stmt)
                elif keyword:
                    ddl_stmts.append(stmt)
            i += 1
            continue
        current.append(ch)
        i += 1

    return ddl_stmts, sel_stmts


async def main():
    log("=" * 70)
    log("Oakwood Mock Data Seed — INTAKELY_PAK entity")
    log("=" * 70)
    log(f"SQL file : {SQL_FILE}")
    log(f"Target DB: ...{DB_URL.split('@')[-1] if '@' in DB_URL else DB_URL[:60]}")
    log("")

    if not DB_URL:
        log("BLOCKED: No database URL found")
        sys.exit(1)

    if not SQL_FILE.exists():
        log(f"BLOCKED: SQL file not found: {SQL_FILE}")
        sys.exit(1)

    sql_content = SQL_FILE.read_text(encoding='utf-8')
    ddl_stmts, sel_stmts = split_sql_statements(sql_content)
    log(f"Parsed: {len(ddl_stmts)} DML/DDL statements, {len(sel_stmts)} SELECT queries")
    log("")

    try:
        conn = await asyncpg.connect(DB_URL, timeout=20, statement_cache_size=0)
        log("Connected\n")
    except Exception as e:
        log(f"Connection failed: {e}")
        sys.exit(1)

    failed = 0
    try:
        for idx, stmt in enumerate(ddl_stmts, 1):
            first_line = stmt.strip().split('\n')[0][:72]
            # Strip non-ASCII chars (box-drawing chars in SQL section comments)
            first_line_safe = first_line.encode('ascii', 'replace').decode('ascii')
            try:
                await conn.execute(stmt)
                log(f"  [{idx:02d}] OK   {first_line_safe}")
            except Exception as e:
                log(f"  [{idx:02d}] FAIL {first_line_safe}")
                log(f"       ERROR: {e}")
                failed += 1

        log("")
        log("-" * 70)
        log("VERIFICATION (counts):")
        log("-" * 70)
        for sel in sel_stmts:
            try:
                rows = await conn.fetch(sel)
                for r in rows:
                    log(f"  {r[0]:<25} {r[1]}")
            except Exception as e:
                log(f"  SELECT error: {e}")

    finally:
        await conn.close()
        log("\nConnection closed")

    log("")
    log("=" * 70)
    if failed == 0:
        log("ALL STATEMENTS APPLIED SUCCESSFULLY")
    else:
        log(f"COMPLETED WITH {failed} FAILURE(S) — review output above")
    log("=" * 70)

    LOG_FILE.parent.mkdir(exist_ok=True)
    LOG_FILE.write_text('\n'.join(log_lines), encoding='utf-8')
    print(f"\nFull log: {LOG_FILE}")

    sys.exit(0 if failed == 0 else 1)


asyncio.run(main())
