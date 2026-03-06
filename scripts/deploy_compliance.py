#!/usr/bin/env python3
"""
Automated Compliance Deployment - All 3 Phases
Executes RLS, Immutability, and Business Constraint SQL scripts via asyncpg
"""
import asyncio
import asyncpg
import os
import re
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
load_dotenv('.env.local')

BASE_DIR = Path(__file__).parent.parent
SQL_DIR  = BASE_DIR / 'database' / 'migrations' / 'compliance'
LOG_FILE = BASE_DIR / 'logs' / 'compliance_deployment.log'

# Use session pooler — stripping asyncpg dialect prefix if present
RAW_URL = os.getenv(
    'FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL',
    os.getenv('FINANCIAL_MANAGEMENT_DATABASE_URL', '')
)
DB_URL = RAW_URL.replace('postgresql+asyncpg://', 'postgresql://')

log_lines = []

def log(msg: str):
    print(msg)
    log_lines.append(msg)

_DOLLAR_TAG_RE = re.compile(r'\$([A-Za-z_][A-Za-z0-9_]*)\$|\$\$')


def split_sql_statements(sql: str) -> tuple[list[str], list[str]]:
    """
    Correctly split SQL into individual executable statements.
    Handles:
      - Line comments (-- ... newline) — semicolons inside are ignored
      - Block comments (/* ... */)     — semicolons inside are ignored
      - Single-quoted strings          — semicolons inside are ignored
      - Dollar-quoted strings          — both $$ and $tag$ forms
    Returns (ddl_statements, select_statements)
    """
    ddl_stmts: list[str] = []
    sel_stmts: list[str] = []

    i               = 0
    n               = len(sql)
    current: list[str] = []
    in_line_comment  = False
    in_block_comment = False
    in_single_quote  = False
    dollar_tag: str | None = None   # None = not in dollar quote; str = current tag

    while i < n:
        ch = sql[i]

        # ── LINE COMMENT ─────────────────────────────────────────────────────
        if in_line_comment:
            current.append(ch)
            if ch == '\n':
                in_line_comment = False
            i += 1
            continue

        # ── BLOCK COMMENT ────────────────────────────────────────────────────
        if in_block_comment:
            current.append(ch)
            if sql[i:i+2] == '*/':
                current.append('/')  # append the closing /
                in_block_comment = False
                i += 2
            else:
                i += 1
            continue

        # ── SINGLE-QUOTED STRING ─────────────────────────────────────────────
        if in_single_quote:
            current.append(ch)
            if ch == "'" and sql[i:i+2] != "''":   # escaped quote
                in_single_quote = False
            elif ch == "'" and sql[i:i+2] == "''":
                current.append("'")
                i += 2
                continue
            i += 1
            continue

        # ── DOLLAR-QUOTED STRING ─────────────────────────────────────────────
        if dollar_tag is not None:
            # look for closing tag
            closing = dollar_tag
            if sql[i:i+len(closing)] == closing:
                current.append(closing)
                dollar_tag = None
                i += len(closing)
            else:
                current.append(ch)
                i += 1
            continue

        # ── DETECT STARTS ────────────────────────────────────────────────────
        # Line comment
        if sql[i:i+2] == '--':
            in_line_comment = True
            current.append(ch)
            i += 1
            continue

        # Block comment
        if sql[i:i+2] == '/*':
            in_block_comment = True
            current.append(ch)
            i += 1
            continue

        # Single quote
        if ch == "'":
            in_single_quote = True
            current.append(ch)
            i += 1
            continue

        # Dollar quote — match $tag$ or $$
        m = _DOLLAR_TAG_RE.match(sql, i)
        if m:
            tag = m.group(0)          # e.g. '$fn$' or '$$'
            dollar_tag = tag
            current.append(tag)
            i += len(tag)
            continue

        # ── STATEMENT TERMINATOR ─────────────────────────────────────────────
        if ch == ';':
            stmt = ''.join(current).strip()
            current = []
            # Strip inline comments to determine keyword
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


async def execute_phase(conn: asyncpg.Connection, phase_name: str, sql_file: Path) -> bool:
    log(f"\n{'='*80}")
    log(f"EXECUTING: {phase_name}")
    log(f"File     : {sql_file.name}")
    log(f"{'='*80}")

    if not sql_file.exists():
        log(f"❌ File not found: {sql_file}")
        return False

    sql_content  = sql_file.read_text(encoding='utf-8')
    ddl_stmts, sel_stmts = split_sql_statements(sql_content)

    log(f"DDL statements  : {len(ddl_stmts)}")
    log(f"SELECT queries  : {len(sel_stmts)}")

    # Execute DDL statements one by one — stop on first failure
    failed = 0
    skipped = 0
    for idx, stmt in enumerate(ddl_stmts, 1):
        first_line = stmt.strip().split('\n')[0][:80]
        try:
            await conn.execute(stmt)
        except asyncpg.exceptions.DuplicateObjectError:
            log(f"  [{idx:03d}] SKIP (already exists) : {first_line}")
            skipped += 1
        except asyncpg.exceptions.DuplicateTableError:
            log(f"  [{idx:03d}] SKIP (duplicate table): {first_line}")
            skipped += 1
        except Exception as e:
            log(f"  [{idx:03d}] ❌ ERROR : {first_line}")
            log(f"           Reason  : {e}")
            failed += 1
            # Continue (non-blocking) so we collect all failures, but flag phase as failed
    
    log(f"\n  Results: {len(ddl_stmts)-failed-skipped} applied, {skipped} skipped, {failed} failed")

    if failed > 0:
        log(f"❌ {phase_name} completed WITH ERRORS ({failed} failed statements)")
        return False

    log(f"✅ {phase_name} completed successfully")
    return True


async def verify_rls(conn: asyncpg.Connection) -> bool:
    log(f"\n{'─'*80}")
    log("VERIFICATION: RLS Policies")
    log(f"{'─'*80}")

    rows = await conn.fetch("""
        SELECT tablename, rowsecurity
        FROM pg_tables
        WHERE schemaname = 'public'
          AND tablename IN (
            'legal_entity','book','gl_account','accounting_period',
            'dimension','dimension_value','journal_entry','journal_line',
            'ar_customer','ar_invoice','ar_payment','ap_vendor','ap_bill',
            'payroll_run','bank_account','bank_transaction',
            'intercompany_transfer','royalty_agreement'
          )
        ORDER BY tablename
    """)

    enabled = 0
    for r in rows:
        icon = '✅' if r['rowsecurity'] else '❌'
        log(f"  {icon} {r['tablename']:<35} rls={r['rowsecurity']}")
        if r['rowsecurity']:
            enabled += 1

    total = len(rows)
    log(f"\n  RLS enabled: {enabled}/{total} tables")

    policy_rows = await conn.fetch("""
        SELECT COUNT(*) AS cnt FROM pg_policies WHERE schemaname = 'public'
    """)
    log(f"  Total policies: {policy_rows[0]['cnt']}")
    return enabled == total


async def verify_triggers(conn: asyncpg.Connection) -> bool:
    log(f"\n{'─'*80}")
    log("VERIFICATION: Immutability Triggers")
    log(f"{'─'*80}")

    rows = await conn.fetch("""
        SELECT event_object_table AS tbl, trigger_name
        FROM information_schema.triggers
        WHERE trigger_schema = 'public'
          AND (trigger_name LIKE '%immutability%'
               OR trigger_name LIKE '%status_transition%'
               OR trigger_name LIKE '%no_overlap%'
               OR trigger_name LIKE '%timestamps%')
        ORDER BY event_object_table, trigger_name
    """)

    for r in rows:
        log(f"  ✅ {r['tbl']:<35} → {r['trigger_name']}")

    log(f"\n  Total triggers: {len(rows)}")
    return len(rows) >= 6


async def verify_constraints(conn: asyncpg.Connection) -> bool:
    log(f"\n{'─'*80}")
    log("VERIFICATION: Business Constraints")
    log(f"{'─'*80}")

    rows = await conn.fetch("""
        SELECT tc.table_name, tc.constraint_type, COUNT(*) AS cnt
        FROM information_schema.table_constraints tc
        WHERE tc.constraint_schema = 'public'
          AND tc.constraint_type IN ('UNIQUE','CHECK')
        GROUP BY tc.table_name, tc.constraint_type
        ORDER BY tc.table_name, tc.constraint_type
    """)

    for r in rows:
        log(f"  ✅ {r['table_name']:<35} {r['constraint_type']:<8} count={r['cnt']}")

    idx_rows = await conn.fetch("""
        SELECT COUNT(*) AS cnt FROM pg_indexes
        WHERE schemaname = 'public' AND indexname LIKE 'idx_%'
    """)
    log(f"\n  Performance indexes : {idx_rows[0]['cnt']}")

    return len(rows) > 0


async def main():
    log("=" * 80)
    log("TrueVow FM — Full Compliance Deployment (Phases 1→2→3)")
    log("=" * 80)
    log(f"Target DB: ...{DB_URL.split('@')[-1] if '@' in DB_URL else DB_URL[:60]}")
    log("")

    if not DB_URL:
        log("❌ BLOCKED: No database URL found in environment")
        return False

    try:
        conn = await asyncpg.connect(DB_URL, timeout=15)
        log("✅ Connected to database\n")
    except Exception as e:
        log(f"❌ Connection failed: {e}")
        return False

    results = {}

    try:
        # Phase 1: RLS Policies
        results['phase1'] = await execute_phase(
            conn, "Phase 1: RLS Policies",
            SQL_DIR / '001_rls_policies.sql'
        )

        # Phase 2: Immutability Constraints
        results['phase2'] = await execute_phase(
            conn, "Phase 2: Immutability Constraints",
            SQL_DIR / '002_immutability_constraints.sql'
        )

        # Phase 3: Business Constraints
        results['phase3'] = await execute_phase(
            conn, "Phase 3: Business Constraints",
            SQL_DIR / '003_business_constraints.sql'
        )

        # Verification
        log(f"\n{'='*80}")
        log("VERIFICATION CHECKS")
        log(f"{'='*80}")

        results['rls_ok']         = await verify_rls(conn)
        results['triggers_ok']    = await verify_triggers(conn)
        results['constraints_ok'] = await verify_constraints(conn)

    finally:
        await conn.close()
        log("\n✅ Database connection closed")

    # Final summary
    log(f"\n{'='*80}")
    log("DEPLOYMENT SUMMARY")
    log(f"{'='*80}")
    log(f"  Phase 1 — RLS Policies          : {'✅ PASS' if results.get('phase1') else '❌ FAIL'}")
    log(f"  Phase 2 — Immutability          : {'✅ PASS' if results.get('phase2') else '❌ FAIL'}")
    log(f"  Phase 3 — Business Constraints  : {'✅ PASS' if results.get('phase3') else '❌ FAIL'}")
    log(f"  Verify  — RLS active            : {'✅ PASS' if results.get('rls_ok') else '❌ FAIL'}")
    log(f"  Verify  — Triggers active       : {'✅ PASS' if results.get('triggers_ok') else '❌ FAIL'}")
    log(f"  Verify  — Constraints active    : {'✅ PASS' if results.get('constraints_ok') else '❌ FAIL'}")
    log(f"{'='*80}")

    all_pass = all(results.values())
    log(f"\n{'🎉 ALL CHECKS PASSED — Compliance deployment DONE' if all_pass else '⚠️  SOME CHECKS FAILED — Review logs/compliance_deployment.log'}")
    log("=" * 80)

    # Write log file
    LOG_FILE.parent.mkdir(exist_ok=True)
    LOG_FILE.write_text('\n'.join(log_lines), encoding='utf-8')
    print(f"\nFull log: {LOG_FILE}")

    return all_pass


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
