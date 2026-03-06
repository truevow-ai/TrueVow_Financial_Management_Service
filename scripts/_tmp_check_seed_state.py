"""Check full current state of INTAKELY_PAK seeded data."""
import asyncio, asyncpg, os
from dotenv import load_dotenv
load_dotenv('.env.local')

URL = os.getenv('FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL')
ENTITY_ID = '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c'
BOOK_ID   = '48972d9f-0f08-4f01-93ce-de078cb8bd3a'

async def main():
    conn = await asyncpg.connect(URL, timeout=15)

    gl  = await conn.fetchval('SELECT count(*) FROM gl_account WHERE book_id=$1', BOOK_ID)
    per = await conn.fetchval('SELECT count(*) FROM accounting_period WHERE book_id=$1', BOOK_ID)
    cust = await conn.fetchval('SELECT count(*) FROM ar_customer WHERE legal_entity_id=$1', ENTITY_ID)
    inv  = await conn.fetchval('SELECT count(*) FROM ar_invoice WHERE legal_entity_id=$1', ENTITY_ID)
    vend = await conn.fetchval('SELECT count(*) FROM ap_vendor WHERE legal_entity_id=$1', ENTITY_ID)
    bill = await conn.fetchval('SELECT count(*) FROM ap_bill WHERE legal_entity_id=$1', ENTITY_ID)
    je   = await conn.fetchval('SELECT count(*) FROM journal_entry WHERE legal_entity_id=$1', ENTITY_ID)
    jl   = await conn.fetchval(
        'SELECT count(*) FROM journal_line jl '
        'JOIN journal_entry je ON je.id = jl.journal_entry_id '
        'WHERE je.legal_entity_id=$1', ENTITY_ID
    )

    print('INTAKELY_PAK data summary:')
    print(f'  GL Accounts      : {gl}')
    print(f'  Acctg Periods    : {per}')
    print(f'  AR Customers     : {cust}')
    print(f'  AR Invoices      : {inv}')
    print(f'  AP Vendors       : {vend}')
    print(f'  AP Bills         : {bill}')
    print(f'  Journal Entries  : {je}')
    print(f'  Journal Lines    : {jl}')

    # AP vendor issue — check if code is globally unique
    dupe = await conn.fetch(
        "SELECT vendor_code, count(*) FROM ap_vendor GROUP BY vendor_code HAVING count(*) > 1"
    )
    if dupe:
        print(f'\nWARN: Duplicate vendor codes: {[(r["vendor_code"], r["count"]) for r in dupe]}')
    else:
        print('\nNo duplicate vendor codes')

    # Oakwood invoices
    oak = await conn.fetchrow("SELECT id FROM ar_customer WHERE legal_entity_id=$1 AND customer_code='OAKWOOD-LAW'", ENTITY_ID)
    if oak:
        invs = await conn.fetch(
            'SELECT invoice_number, status, total_amount, outstanding_amount FROM ar_invoice '
            'WHERE ar_customer_id=$1 ORDER BY invoice_date', oak['id']
        )
        print(f'\nOakwood Law Firm invoices ({len(invs)}):')
        for r in invs:
            print(f'  {r["invoice_number"]:<25} {r["status"]:<18} total={r["total_amount"]:>10,.2f}  out={r["outstanding_amount"]:>10,.2f}')

    await conn.close()

asyncio.run(main())
