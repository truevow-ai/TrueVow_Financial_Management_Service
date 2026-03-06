#!/usr/bin/env python3
"""
Comprehensive mock data seed — Oakwood Law Firm scenario.

Entity : INTAKELY_PAK (17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c)
Customer: Oakwood Law Firm (Clerk e2362e1c-759a-402d-9b38-2eab1ae8ad3f)

Uses DIRECT database connection (no pgBouncer) so queries cannot hang.
Idempotent — safe to re-run.
"""
import asyncio
import asyncpg
import sys
import os
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

load_dotenv()
load_dotenv('.env.local')

# Session pooler with statement_cache_size=0 (required for pgBouncer compatibility)
URL = os.getenv('FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL', '').replace(
    'postgresql+asyncpg://', 'postgresql://'
)
if not URL:
    raise RuntimeError('FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL not set')

ENTITY_ID = '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c'
BOOK_ID   = '48972d9f-0f08-4f01-93ce-de078cb8bd3a'
CLERK_OAK = 'e2362e1c-759a-402d-9b38-2eab1ae8ad3f'
TODAY     = date.today()
CURRENCY  = 'PKR'

CHART_OF_ACCOUNTS = [
    ('1000', 'Cash - Operating Account',         'ASSET'),
    ('1050', 'Petty Cash',                        'ASSET'),
    ('1200', 'Accounts Receivable - Trade',       'ASSET'),
    ('1210', 'Accounts Receivable - Retainer',    'ASSET'),
    ('1300', 'Prepaid Expenses',                  'ASSET'),
    ('1400', 'Work in Progress',                  'ASSET'),
    ('2000', 'Accounts Payable',                  'LIABILITY'),
    ('2100', 'Accrued Liabilities',               'LIABILITY'),
    ('2200', 'Deferred Revenue',                  'LIABILITY'),
    ('2300', 'Payroll Taxes Payable',             'LIABILITY'),
    ('3000', 'Retained Earnings',                 'EQUITY'),
    ('3100', 'Owners Equity',                     'EQUITY'),
    ('4100', 'Service Revenue - Retainer',        'REVENUE'),
    ('4200', 'Service Revenue - Contingency',     'REVENUE'),
    ('4300', 'Service Revenue - Hourly',          'REVENUE'),
    ('4400', 'Late Payment Fees',                 'REVENUE'),
    ('5100', 'Salaries & Wages',                  'EXPENSE'),
    ('5200', 'Office Lease',                      'EXPENSE'),
    ('5300', 'Legal Research Subscriptions',      'EXPENSE'),
    ('5400', 'IT & Cloud Services',               'EXPENSE'),
    ('5500', 'Professional Development',          'EXPENSE'),
    ('5600', 'Marketing & Business Development',  'EXPENSE'),
]


def p(msg):
    print(msg, flush=True)


async def main():
    p(f'Connecting to: {URL[:55]}...')
    c = await asyncpg.connect(URL, timeout=20, statement_cache_size=0)
    p(f'Connected — INTAKELY_PAK ({ENTITY_ID})')

    try:
        # ── 1. GL Accounts ────────────────────────────────────────────────────
        p('\n[1/6] GL Accounts')
        p('  inserting accounts...', )
        for i, (code, name, acc_type) in enumerate(CHART_OF_ACCOUNTS):
            p(f'  [{i+1}/22] {code} {name}...')
            await c.execute(
                'INSERT INTO gl_account '
                '(book_id, account_code, account_name, account_type, is_active) '
                'VALUES ($1,$2,$3,$4,true) ON CONFLICT DO NOTHING',
                BOOK_ID, code, name, acc_type
            )
            p(f'  [{i+1}/22] done')
        gl_cnt = await c.fetchval('SELECT count(*) FROM gl_account WHERE book_id=$1', BOOK_ID)
        p(f'  GL accounts: {gl_cnt}')

        # ── 2. Accounting Periods ─────────────────────────────────────────────
        # NOTE: accounting_period_no_overlap trigger rejects inserts for overlapping dates.
        # We check existence before each insert to avoid triggering the exception.
        p('\n[2/6] Accounting Periods')
        start = date(2025, 1, 1)
        ins = skipped = 0
        while start <= TODAY.replace(day=1):
            end    = (start + relativedelta(months=1)) - timedelta(days=1)
            status = 'OPEN' if (start.month == TODAY.month and start.year == TODAY.year) else 'CLOSED'
            name   = start.strftime('%B %Y')
            exists = await c.fetchval(
                'SELECT id FROM accounting_period WHERE book_id=$1 AND period_name=$2',
                BOOK_ID, name
            )
            if not exists:
                try:
                    await c.execute(
                        'INSERT INTO accounting_period '
                        '(book_id, start_date, end_date, period_name, status) '
                        'VALUES ($1,$2,$3,$4,$5)',
                        BOOK_ID, start, end, name, status
                    )
                    ins += 1
                except Exception as e:
                    p(f'  WARN period {name}: {e}')
            else:
                skipped += 1
            start += relativedelta(months=1)
        per_cnt = await c.fetchval('SELECT count(*) FROM accounting_period WHERE book_id=$1', BOOK_ID)
        p(f'  Accounting periods: {per_cnt} (new={ins}, skipped={skipped})')

        open_period_id = await c.fetchval(
            "SELECT id FROM accounting_period WHERE book_id=$1 AND status='OPEN' "
            'ORDER BY start_date DESC LIMIT 1', BOOK_ID
        )
        jan_period_id = await c.fetchval(
            "SELECT id FROM accounting_period WHERE book_id=$1 AND period_name='January 2025'",
            BOOK_ID
        )

        # ── 3. AR Customers + Invoices ────────────────────────────────────────
        p('\n[3/6] AR Customers & Invoices')
        await c.execute(
            'INSERT INTO ar_customer '
            '(legal_entity_id, customer_code, customer_name, external_customer_id) '
            'VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING',
            ENTITY_ID, 'OAKWOOD-LAW', 'Oakwood Law Firm', CLERK_OAK
        )
        await c.execute(
            'INSERT INTO ar_customer (legal_entity_id, customer_code, customer_name) '
            'VALUES ($1,$2,$3) ON CONFLICT DO NOTHING',
            ENTITY_ID, 'MERIDIAN-CAP', 'Meridian Capital Group'
        )
        await c.execute(
            'INSERT INTO ar_customer (legal_entity_id, customer_code, customer_name) '
            'VALUES ($1,$2,$3) ON CONFLICT DO NOTHING',
            ENTITY_ID, 'RIVERSIDE', 'Riverside Consulting LLC'
        )

        oak_id = await c.fetchval(
            "SELECT id FROM ar_customer WHERE legal_entity_id=$1 AND customer_code='OAKWOOD-LAW'",
            ENTITY_ID)
        mer_id = await c.fetchval(
            "SELECT id FROM ar_customer WHERE legal_entity_id=$1 AND customer_code='MERIDIAN-CAP'",
            ENTITY_ID)
        riv_id = await c.fetchval(
            "SELECT id FROM ar_customer WHERE legal_entity_id=$1 AND customer_code='RIVERSIDE'",
            ENTITY_ID)
        cust_cnt = await c.fetchval('SELECT count(*) FROM ar_customer WHERE legal_entity_id=$1', ENTITY_ID)
        p(f'  AR customers: {cust_cnt}')

        # Oakwood — 12 months monthly retainer
        amounts = [8500, 9200, 11500, 10800, 12000, 9800, 11200, 13500, 9500, 10200, 14000, 8800]
        for i in range(12):
            mago     = 12 - i
            inv_date = TODAY.replace(day=1) - relativedelta(months=mago)
            due_date = inv_date + timedelta(days=30)
            amount   = float(amounts[i])
            if mago >= 3:
                status, out = 'PAID', 0.0
            elif mago == 2:
                status, out = 'PARTIALLY_PAID', round(amount * 0.4, 2)
            else:
                status, out = 'ISSUED', amount
            await c.execute(
                'INSERT INTO ar_invoice '
                '(legal_entity_id, ar_customer_id, invoice_number, external_invoice_id, '
                ' invoice_date, due_date, status, total_amount, outstanding_amount, currency) '
                'VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) ON CONFLICT DO NOTHING',
                ENTITY_ID, oak_id, f'INV-OAK-{i+1:03d}', f'oak-inv-{i+1:03d}',
                inv_date, due_date, status, amount, out, CURRENCY
            )

        for (cid, num, ext, dago, dfwd, status, total, out) in [
            (oak_id, 'INV-OAK-CUR', 'oak-inv-cur', 0, 30, 'ISSUED', 11000.0, 11000.0),
            (mer_id, 'INV-MER-001', 'mer-inv-001', 45, -15, 'ISSUED', 22500.0, 22500.0),
            (riv_id, 'INV-RIV-001', 'riv-inv-001', 20, -10, 'ISSUED', 7800.0, 7800.0),
        ]:
            inv_date = TODAY.replace(day=1) if dago == 0 else TODAY - timedelta(days=dago)
            due_date = inv_date + timedelta(days=30) if dfwd == 30 else TODAY + timedelta(days=abs(dfwd)) if dfwd < 0 else TODAY + timedelta(days=dfwd)
            await c.execute(
                'INSERT INTO ar_invoice '
                '(legal_entity_id, ar_customer_id, invoice_number, external_invoice_id, '
                ' invoice_date, due_date, status, total_amount, outstanding_amount, currency) '
                'VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) ON CONFLICT DO NOTHING',
                ENTITY_ID, cid, num, ext, inv_date, due_date, status, total, out, CURRENCY
            )

        inv_cnt = await c.fetchval('SELECT count(*) FROM ar_invoice WHERE legal_entity_id=$1', ENTITY_ID)
        oak_cnt = await c.fetchval('SELECT count(*) FROM ar_invoice WHERE ar_customer_id=$1', oak_id)
        p(f'  AR invoices: {inv_cnt} total (Oakwood: {oak_cnt})')

        # ── 4. AP Vendors + Bills ─────────────────────────────────────────────
        p('\n[4/6] AP Vendors & Bills')
        vend_list = [
            ('LEXISNEXIS',   'LexisNexis - Legal Research'),
            ('WESTLAW',      'Thomson Reuters Westlaw'),
            ('OFFICE-LEASE', 'Downtown Office Lease LLC'),
            ('IT-CLOUD',     'Cloud IT Services Inc'),
            ('MALPRACT-INS', 'Professional Liability Insurance'),
        ]
        for vcode, vname in vend_list:
            await c.execute(
                'INSERT INTO ap_vendor '
                '(legal_entity_id, vendor_code, vendor_name, default_currency) '
                'VALUES ($1,$2,$3,$4) ON CONFLICT DO NOTHING',
                ENTITY_ID, vcode, vname, CURRENCY
            )
        vend_ids = {}
        for vcode, _ in vend_list:
            vend_ids[vcode] = await c.fetchval(
                'SELECT id FROM ap_vendor WHERE legal_entity_id=$1 AND vendor_code=$2',
                ENTITY_ID, vcode
            )
        vend_cnt = await c.fetchval('SELECT count(*) FROM ap_vendor WHERE legal_entity_id=$1', ENTITY_ID)
        p(f'  AP vendors: {vend_cnt}')

        for (vcode, bnum, bdate, ddate, status, total, out) in [
            ('LEXISNEXIS',   'BILL-LEX-001',    TODAY - timedelta(15), TODAY + timedelta(15), 'APPROVED', 1200.0,  1200.0),
            ('WESTLAW',      'BILL-WEST-001',   TODAY - timedelta(15), TODAY + timedelta(15), 'APPROVED',  980.0,   980.0),
            ('OFFICE-LEASE', 'BILL-OFFICE-001', TODAY - timedelta(5),  TODAY + timedelta(25), 'APPROVED', 8500.0,  8500.0),
            ('IT-CLOUD',     'BILL-IT-001',     TODAY - timedelta(10), TODAY + timedelta(20), 'APPROVED',  650.0,   650.0),
            ('MALPRACT-INS', 'BILL-INS-001',    TODAY - timedelta(90), TODAY - timedelta(60), 'PAID',     5400.0,    0.0),
            ('LEXISNEXIS',   'BILL-LEX-002',    TODAY - timedelta(45), TODAY - timedelta(15), 'PAID',     1200.0,    0.0),
            ('WESTLAW',      'BILL-WEST-002',   TODAY - timedelta(45), TODAY - timedelta(15), 'PAID',      980.0,    0.0),
            ('OFFICE-LEASE', 'BILL-OFFICE-002', TODAY - timedelta(35), TODAY - timedelta(5),  'PAID',     8500.0,    0.0),
        ]:
            vid = vend_ids.get(vcode)
            if vid:
                await c.execute(
                    'INSERT INTO ap_bill '
                    '(legal_entity_id, book_id, ap_vendor_id, bill_number, bill_date, due_date, '
                    ' status, total_amount, outstanding_amount, currency) '
                    'VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) ON CONFLICT DO NOTHING',
                    ENTITY_ID, BOOK_ID, vid, bnum, bdate, ddate, status, total, out, CURRENCY
                )
        bill_cnt = await c.fetchval('SELECT count(*) FROM ap_bill WHERE legal_entity_id=$1', ENTITY_ID)
        p(f'  AP bills: {bill_cnt}')

        # ── 5. Journal Entries + Lines ────────────────────────────────────────
        p('\n[5/6] Journal Entries')
        accts = {}
        for code in ('1000', '1200', '2000', '4100', '5100', '5200', '5300'):
            accts[code] = await c.fetchval(
                'SELECT id FROM gl_account WHERE book_id=$1 AND account_code=$2',
                BOOK_ID, code
            )

        async def insert_je(entry_number, entry_date, description, status, period_id, lines):
            try:
                await c.execute(
                    'INSERT INTO journal_entry '
                    '(book_id, period_id, legal_entity_id, entry_number, entry_date, description, status) '
                    'VALUES ($1,$2,$3,$4,$5,$6,$7) ON CONFLICT DO NOTHING',
                    BOOK_ID, period_id, ENTITY_ID, entry_number, entry_date, description, status
                )
            except Exception as e:
                p(f'  WARN je {entry_number}: {e}')
                return
            je_id = await c.fetchval(
                'SELECT id FROM journal_entry WHERE book_id=$1 AND entry_number=$2',
                BOOK_ID, entry_number
            )
            if not je_id:
                return
            for i, (acct_id, dr, cr) in enumerate(lines, 1):
                if await c.fetchval(
                    'SELECT count(*) FROM journal_line WHERE journal_entry_id=$1 AND line_number=$2',
                    je_id, i
                ) == 0:
                    try:
                        await c.execute(
                            'INSERT INTO journal_line '
                            '(journal_entry_id, book_id, gl_account_id, line_number, '
                            ' debit_tc, credit_tc, currency) '
                            'VALUES ($1,$2,$3,$4,$5,$6,$7)',
                            je_id, BOOK_ID, acct_id, i, float(dr), float(cr), CURRENCY
                        )
                    except Exception as e:
                        p(f'  WARN jl {i}/{entry_number}: {e}')

        if jan_period_id:
            await insert_je(
                'JE-OPEN-2025', date(2025, 1, 1), 'Opening balances FY2025', 'POSTED', jan_period_id,
                [(accts['1000'], 45000, 0), (accts['1200'], 28000, 0),
                 (accts['2000'], 0, 18000), (accts['4100'], 0, 55000)]
            )

        for m in range(3, 0, -1):
            mo = TODAY.replace(day=1) - relativedelta(months=m)
            per_id = await c.fetchval(
                'SELECT id FROM accounting_period WHERE book_id=$1 AND start_date=$2',
                BOOK_ID, mo
            )
            if not per_id:
                continue
            label   = mo.strftime('%b%Y')
            rev_amt = float([85000, 92000, 78500][3 - m])
            await insert_je(
                f'JE-REV-{label}', mo + timedelta(27),
                f'Revenue recognition {mo.strftime("%B %Y")}', 'POSTED', per_id,
                [(accts['1000'], rev_amt * 0.75, 0), (accts['1200'], rev_amt * 0.25, 0),
                 (accts['4100'], 0, rev_amt)]
            )
            exp = rev_amt * 0.60
            await insert_je(
                f'JE-EXP-{label}', mo + timedelta(28),
                f'Expense accrual {mo.strftime("%B %Y")}', 'POSTED', per_id,
                [(accts['5100'], exp, 0), (accts['5200'], 8500, 0), (accts['5300'], 2180, 0),
                 (accts['2000'], 0, exp + 10680)]
            )

        if open_period_id:
            await insert_je(
                f'JE-DRAFT-{TODAY.strftime("%b%Y")}', TODAY,
                f'Accrual estimate {TODAY.strftime("%B %Y")}', 'DRAFT', open_period_id,
                [(accts['1200'], 11000, 0), (accts['4100'], 0, 11000)]
            )

        je_cnt = await c.fetchval('SELECT count(*) FROM journal_entry WHERE legal_entity_id=$1', ENTITY_ID)
        jl_cnt = await c.fetchval(
            'SELECT count(*) FROM journal_line jl '
            'JOIN journal_entry je ON je.id=jl.journal_entry_id '
            'WHERE je.legal_entity_id=$1', ENTITY_ID
        )
        p(f'  Journal entries: {je_cnt}  Journal lines: {jl_cnt}')

        # ── 6. Summary ────────────────────────────────────────────────────────
        p('\n[6/6] Summary')
        p(f'  ╔══════════════════════════════════════╗')
        p(f'  ║  INTAKELY_PAK — Seed Complete        ║')
        p(f'  ╠══════════════════════════════════════╣')
        p(f'  ║  GL Accounts       : {gl_cnt:<18}║')
        p(f'  ║  Accounting Periods: {per_cnt:<18}║')
        p(f'  ║  AR Customers      : {cust_cnt:<18}║')
        p(f'  ║  AR Invoices       : {inv_cnt:<18}║')
        p(f'  ║  AP Vendors        : {vend_cnt:<18}║')
        p(f'  ║  AP Bills          : {bill_cnt:<18}║')
        p(f'  ║  Journal Entries   : {je_cnt:<18}║')
        p(f'  ║  Journal Lines     : {jl_cnt:<18}║')
        p(f'  ╚══════════════════════════════════════╝')

        p(f'\n  Oakwood Law Firm invoices ({oak_cnt}):')
        invs = await c.fetch(
            'SELECT invoice_number, status, total_amount, outstanding_amount '
            'FROM ar_invoice WHERE ar_customer_id=$1 ORDER BY invoice_date', oak_id
        )
        for r in invs:
            p(f'    {r["invoice_number"]:<22} {r["status"]:<16} '
              f'PKR {r["total_amount"]:>10,.0f}  out={r["outstanding_amount"]:>10,.0f}')

    finally:
        await c.close()

    p('\nDone. Next: python scripts\\test_rls_enforcement.py')


asyncio.run(main())
