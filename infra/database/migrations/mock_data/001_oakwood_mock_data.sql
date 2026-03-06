-- ==========================================================================
-- Mock Data: Oakwood Law Firm scenario — INTAKELY_PAK entity
-- Entity ID : 17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c
-- Book ID   : 48972d9f-0f08-4f01-93ce-de078cb8bd3a  (ACCRUAL)
-- Clerk OAK : e2362e1c-759a-402d-9b38-2eab1ae8ad3f
-- Currency  : PKR
-- Safe to re-run (ON CONFLICT DO NOTHING everywhere)
-- ==========================================================================

-- ── GL Accounts (ACCRUAL book) ──────────────────────────────────────────────
INSERT INTO gl_account (book_id, account_code, account_name, account_type, is_active)
VALUES
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','1000','Cash - Operating Account','ASSET',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','1050','Petty Cash','ASSET',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','1200','Accounts Receivable - Trade','ASSET',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','1210','Accounts Receivable - Retainer','ASSET',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','1300','Prepaid Expenses','ASSET',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','1400','Work in Progress','ASSET',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','2000','Accounts Payable','LIABILITY',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','2100','Accrued Liabilities','LIABILITY',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','2200','Deferred Revenue','LIABILITY',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','2300','Payroll Taxes Payable','LIABILITY',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','3000','Retained Earnings','EQUITY',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','3100','Owners Equity','EQUITY',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','4100','Service Revenue - Retainer','REVENUE',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','4200','Service Revenue - Contingency','REVENUE',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','4300','Service Revenue - Hourly','REVENUE',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','4400','Late Payment Fees','REVENUE',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','5100','Salaries & Wages','EXPENSE',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','5200','Office Lease','EXPENSE',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','5300','Legal Research Subscriptions','EXPENSE',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','5400','IT & Cloud Services','EXPENSE',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','5500','Professional Development','EXPENSE',true),
  ('48972d9f-0f08-4f01-93ce-de078cb8bd3a','5600','Marketing & Business Development','EXPENSE',true)
ON CONFLICT DO NOTHING;

-- ── Accounting Periods (ACCRUAL book) ──────────────────────────────────────
-- Using check-before-insert approach (see accounting_period_no_overlap trigger)
-- We insert only if period_name does not exist for this book
INSERT INTO accounting_period (book_id, start_date, end_date, period_name, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a','2025-01-01','2025-01-31','January 2025','CLOSED'
WHERE NOT EXISTS (SELECT 1 FROM accounting_period WHERE book_id='48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND period_name='January 2025');

INSERT INTO accounting_period (book_id, start_date, end_date, period_name, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a','2025-02-01','2025-02-28','February 2025','CLOSED'
WHERE NOT EXISTS (SELECT 1 FROM accounting_period WHERE book_id='48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND period_name='February 2025');

INSERT INTO accounting_period (book_id, start_date, end_date, period_name, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a','2025-03-01','2025-03-31','March 2025','CLOSED'
WHERE NOT EXISTS (SELECT 1 FROM accounting_period WHERE book_id='48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND period_name='March 2025');

INSERT INTO accounting_period (book_id, start_date, end_date, period_name, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a','2025-04-01','2025-04-30','April 2025','CLOSED'
WHERE NOT EXISTS (SELECT 1 FROM accounting_period WHERE book_id='48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND period_name='April 2025');

INSERT INTO accounting_period (book_id, start_date, end_date, period_name, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a','2025-05-01','2025-05-31','May 2025','CLOSED'
WHERE NOT EXISTS (SELECT 1 FROM accounting_period WHERE book_id='48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND period_name='May 2025');

INSERT INTO accounting_period (book_id, start_date, end_date, period_name, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a','2025-06-01','2025-06-30','June 2025','CLOSED'
WHERE NOT EXISTS (SELECT 1 FROM accounting_period WHERE book_id='48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND period_name='June 2025');

INSERT INTO accounting_period (book_id, start_date, end_date, period_name, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a','2025-07-01','2025-07-31','July 2025','CLOSED'
WHERE NOT EXISTS (SELECT 1 FROM accounting_period WHERE book_id='48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND period_name='July 2025');

INSERT INTO accounting_period (book_id, start_date, end_date, period_name, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a','2025-08-01','2025-08-31','August 2025','CLOSED'
WHERE NOT EXISTS (SELECT 1 FROM accounting_period WHERE book_id='48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND period_name='August 2025');

INSERT INTO accounting_period (book_id, start_date, end_date, period_name, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a','2025-09-01','2025-09-30','September 2025','CLOSED'
WHERE NOT EXISTS (SELECT 1 FROM accounting_period WHERE book_id='48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND period_name='September 2025');

INSERT INTO accounting_period (book_id, start_date, end_date, period_name, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a','2025-10-01','2025-10-31','October 2025','CLOSED'
WHERE NOT EXISTS (SELECT 1 FROM accounting_period WHERE book_id='48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND period_name='October 2025');

INSERT INTO accounting_period (book_id, start_date, end_date, period_name, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a','2025-11-01','2025-11-30','November 2025','CLOSED'
WHERE NOT EXISTS (SELECT 1 FROM accounting_period WHERE book_id='48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND period_name='November 2025');

INSERT INTO accounting_period (book_id, start_date, end_date, period_name, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a','2025-12-01','2025-12-31','December 2025','CLOSED'
WHERE NOT EXISTS (SELECT 1 FROM accounting_period WHERE book_id='48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND period_name='December 2025');

INSERT INTO accounting_period (book_id, start_date, end_date, period_name, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a','2026-01-01','2026-01-31','January 2026','CLOSED'
WHERE NOT EXISTS (SELECT 1 FROM accounting_period WHERE book_id='48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND period_name='January 2026');

INSERT INTO accounting_period (book_id, start_date, end_date, period_name, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a','2026-02-01','2026-02-28','February 2026','CLOSED'
WHERE NOT EXISTS (SELECT 1 FROM accounting_period WHERE book_id='48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND period_name='February 2026');

INSERT INTO accounting_period (book_id, start_date, end_date, period_name, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a','2026-03-01','2026-03-31','March 2026','OPEN'
WHERE NOT EXISTS (SELECT 1 FROM accounting_period WHERE book_id='48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND period_name='March 2026');

-- ── AR Customers ────────────────────────────────────────────────────────────
INSERT INTO ar_customer (legal_entity_id, customer_code, customer_name, external_customer_id)
VALUES ('17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c','OAKWOOD-LAW','Oakwood Law Firm','e2362e1c-759a-402d-9b38-2eab1ae8ad3f')
ON CONFLICT DO NOTHING;

INSERT INTO ar_customer (legal_entity_id, customer_code, customer_name, external_customer_id)
VALUES ('17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c','MERIDIAN-CAP','Meridian Capital Group','mer-cap-0000-0000-000000000001')
ON CONFLICT DO NOTHING;

INSERT INTO ar_customer (legal_entity_id, customer_code, customer_name, external_customer_id)
VALUES ('17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c','RIVERSIDE','Riverside Consulting LLC','riverside-00-0000-000000000002')
ON CONFLICT DO NOTHING;

-- ── AR Invoices: Oakwood Law Firm (12 months + current) ────────────────────
-- Using DO UPDATE to reset the legal_entity_id in case it's missing from old rows
INSERT INTO ar_invoice (legal_entity_id, ar_customer_id, invoice_number, external_invoice_id,
  invoice_date, due_date, status, total_amount, outstanding_amount, currency)
SELECT
  '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c',
  ac.id,
  v.invoice_number, v.ext_id,
  v.inv_date::date, v.due_date::date,
  v.status::invoice_status, v.total, v.outstanding, 'PKR'
FROM (VALUES
  ('INV-OAK-001','oak-inv-001', CURRENT_DATE - INTERVAL '12 months', CURRENT_DATE - INTERVAL '9 months',  'PAID',         8500,    0),
  ('INV-OAK-002','oak-inv-002', CURRENT_DATE - INTERVAL '11 months', CURRENT_DATE - INTERVAL '8 months',  'PAID',         9200,    0),
  ('INV-OAK-003','oak-inv-003', CURRENT_DATE - INTERVAL '10 months', CURRENT_DATE - INTERVAL '7 months',  'PAID',        11500,    0),
  ('INV-OAK-004','oak-inv-004', CURRENT_DATE - INTERVAL '9 months',  CURRENT_DATE - INTERVAL '6 months',  'PAID',        10800,    0),
  ('INV-OAK-005','oak-inv-005', CURRENT_DATE - INTERVAL '8 months',  CURRENT_DATE - INTERVAL '5 months',  'PAID',        12000,    0),
  ('INV-OAK-006','oak-inv-006', CURRENT_DATE - INTERVAL '7 months',  CURRENT_DATE - INTERVAL '4 months',  'PAID',         9800,    0),
  ('INV-OAK-007','oak-inv-007', CURRENT_DATE - INTERVAL '6 months',  CURRENT_DATE - INTERVAL '3 months',  'PAID',        11200,    0),
  ('INV-OAK-008','oak-inv-008', CURRENT_DATE - INTERVAL '5 months',  CURRENT_DATE - INTERVAL '2 months',  'PAID',        13500,    0),
  ('INV-OAK-009','oak-inv-009', CURRENT_DATE - INTERVAL '4 months',  CURRENT_DATE - INTERVAL '1 month',   'PAID',         9500,    0),
  ('INV-OAK-010','oak-inv-010', CURRENT_DATE - INTERVAL '3 months',  CURRENT_DATE,                        'PAID',        10200,    0),
  ('INV-OAK-011','oak-inv-011', CURRENT_DATE - INTERVAL '2 months',  CURRENT_DATE + INTERVAL '1 month',   'PARTIALLY_PAID', 14000, 5600),
  ('INV-OAK-012','oak-inv-012', CURRENT_DATE - INTERVAL '1 month',   CURRENT_DATE + INTERVAL '2 months',  'ISSUED',       8800, 8800),
  ('INV-OAK-CUR','oak-inv-cur', DATE_TRUNC('month', CURRENT_DATE),   DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '30 days', 'ISSUED', 11000, 11000)
) AS v(invoice_number, ext_id, inv_date, due_date, status, total, outstanding)
JOIN ar_customer ac ON ac.legal_entity_id = '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c'
  AND ac.customer_code = 'OAKWOOD-LAW'
ON CONFLICT (external_invoice_id) DO NOTHING;

-- ── AR Invoices: Meridian + Riverside ──────────────────────────────────────
INSERT INTO ar_invoice (legal_entity_id, ar_customer_id, invoice_number, external_invoice_id,
  invoice_date, due_date, status, total_amount, outstanding_amount, currency)
SELECT '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c', ac.id,
  'INV-MER-001','mer-inv-001',
  CURRENT_DATE - INTERVAL '45 days', CURRENT_DATE - INTERVAL '15 days',
  'ISSUED', 22500, 22500, 'PKR'
FROM ar_customer ac
WHERE ac.legal_entity_id = '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c'
  AND ac.customer_code = 'MERIDIAN-CAP'
ON CONFLICT (external_invoice_id) DO NOTHING;

INSERT INTO ar_invoice (legal_entity_id, ar_customer_id, invoice_number, external_invoice_id,
  invoice_date, due_date, status, total_amount, outstanding_amount, currency)
SELECT '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c', ac.id,
  'INV-RIV-001','riv-inv-001',
  CURRENT_DATE - INTERVAL '20 days', CURRENT_DATE + INTERVAL '10 days',
  'ISSUED', 7800, 7800, 'PKR'
FROM ar_customer ac
WHERE ac.legal_entity_id = '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c'
  AND ac.customer_code = 'RIVERSIDE'
ON CONFLICT (external_invoice_id) DO NOTHING;

-- ── AP Vendors ──────────────────────────────────────────────────────────────
INSERT INTO ap_vendor (legal_entity_id, vendor_code, vendor_name, default_currency)
VALUES
  ('17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c','LEXISNEXIS',  'LexisNexis - Legal Research',  'PKR'),
  ('17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c','WESTLAW',     'Thomson Reuters Westlaw',       'PKR'),
  ('17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c','OFFICE-LEASE','Downtown Office Lease LLC',     'PKR'),
  ('17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c','IT-CLOUD',    'Cloud IT Services Inc',         'PKR'),
  ('17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c','MALPRACT-INS','Professional Liability Insurance','PKR')
ON CONFLICT DO NOTHING;

-- ── AP Bills ────────────────────────────────────────────────────────────────
INSERT INTO ap_bill (legal_entity_id, book_id, ap_vendor_id, bill_number, bill_date, due_date,
  status, total_amount, paid_amount, outstanding_amount, currency)
SELECT
  '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c',
  '48972d9f-0f08-4f01-93ce-de078cb8bd3a',
  v.id, b.bill_number, b.bill_date::date, b.due_date::date,
  b.status, b.total, b.paid, b.outstanding, 'PKR'
FROM (VALUES
  ('LEXISNEXIS',   'BILL-LEX-001',    CURRENT_DATE - 15, CURRENT_DATE + 15, 'APPROVED', 1200,    0, 1200),
  ('WESTLAW',      'BILL-WEST-001',   CURRENT_DATE - 15, CURRENT_DATE + 15, 'APPROVED',  980,    0,  980),
  ('OFFICE-LEASE', 'BILL-OFFICE-001', CURRENT_DATE -  5, CURRENT_DATE + 25, 'APPROVED', 8500,    0, 8500),
  ('IT-CLOUD',     'BILL-IT-001',     CURRENT_DATE - 10, CURRENT_DATE + 20, 'APPROVED',  650,    0,  650),
  ('MALPRACT-INS', 'BILL-INS-001',    CURRENT_DATE - 90, CURRENT_DATE - 60, 'PAID',     5400, 5400,    0),
  ('LEXISNEXIS',   'BILL-LEX-002',    CURRENT_DATE - 45, CURRENT_DATE - 15, 'PAID',     1200, 1200,    0),
  ('WESTLAW',      'BILL-WEST-002',   CURRENT_DATE - 45, CURRENT_DATE - 15, 'PAID',      980,  980,    0),
  ('OFFICE-LEASE', 'BILL-OFFICE-002', CURRENT_DATE - 35, CURRENT_DATE -  5, 'PAID',     8500, 8500,    0)
) AS b(vendor_code, bill_number, bill_date, due_date, status, total, paid, outstanding)
JOIN ap_vendor v ON v.legal_entity_id = '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c'
  AND v.vendor_code = b.vendor_code
ON CONFLICT DO NOTHING;

-- ── Journal Entries + Lines ─────────────────────────────────────────────────
-- Opening balances — January 2025
INSERT INTO journal_entry (book_id, period_id, legal_entity_id, entry_number, entry_date, description, status)
SELECT
  '48972d9f-0f08-4f01-93ce-de078cb8bd3a',
  ap.id,
  '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c',
  'JE-OPEN-2025', '2025-01-01', 'Opening balances FY2025', 'POSTED'
FROM accounting_period ap
WHERE ap.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a'
  AND ap.period_name = 'January 2025'
ON CONFLICT DO NOTHING;

INSERT INTO journal_line (journal_entry_id, book_id, gl_account_id, line_number, debit_tc, credit_tc, currency)
SELECT je.id, '48972d9f-0f08-4f01-93ce-de078cb8bd3a', ga.id, v.line_no, v.dr, v.cr, 'PKR'
FROM (VALUES (1,'1000',45000,0),(2,'1200',28000,0),(3,'2000',0,18000),(4,'4100',0,55000)) AS v(line_no, code, dr, cr)
JOIN gl_account ga ON ga.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND ga.account_code = v.code
JOIN journal_entry je ON je.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND je.entry_number = 'JE-OPEN-2025'
WHERE NOT EXISTS (SELECT 1 FROM journal_line jl WHERE jl.journal_entry_id = je.id AND jl.line_number = v.line_no);

-- Revenue recognition — December 2025
INSERT INTO journal_entry (book_id, period_id, legal_entity_id, entry_number, entry_date, description, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a', ap.id, '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c',
  'JE-REV-Dec2025', '2025-12-27', 'Revenue recognition December 2025', 'POSTED'
FROM accounting_period ap
WHERE ap.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND ap.period_name = 'December 2025'
ON CONFLICT DO NOTHING;

INSERT INTO journal_line (journal_entry_id, book_id, gl_account_id, line_number, debit_tc, credit_tc, currency)
SELECT je.id, '48972d9f-0f08-4f01-93ce-de078cb8bd3a', ga.id, v.line_no, v.dr, v.cr, 'PKR'
FROM (VALUES (1,'1000',63750,0),(2,'1200',21250,0),(3,'4100',0,85000)) AS v(line_no, code, dr, cr)
JOIN gl_account ga ON ga.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND ga.account_code = v.code
JOIN journal_entry je ON je.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND je.entry_number = 'JE-REV-Dec2025'
WHERE NOT EXISTS (SELECT 1 FROM journal_line jl WHERE jl.journal_entry_id = je.id AND jl.line_number = v.line_no);

-- Expense accrual — December 2025
INSERT INTO journal_entry (book_id, period_id, legal_entity_id, entry_number, entry_date, description, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a', ap.id, '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c',
  'JE-EXP-Dec2025', '2025-12-28', 'Expense accrual December 2025', 'POSTED'
FROM accounting_period ap
WHERE ap.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND ap.period_name = 'December 2025'
ON CONFLICT DO NOTHING;

INSERT INTO journal_line (journal_entry_id, book_id, gl_account_id, line_number, debit_tc, credit_tc, currency)
SELECT je.id, '48972d9f-0f08-4f01-93ce-de078cb8bd3a', ga.id, v.line_no, v.dr, v.cr, 'PKR'
FROM (VALUES (1,'5100',51000,0),(2,'5200',8500,0),(3,'5300',2180,0),(4,'2000',0,61680)) AS v(line_no, code, dr, cr)
JOIN gl_account ga ON ga.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND ga.account_code = v.code
JOIN journal_entry je ON je.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND je.entry_number = 'JE-EXP-Dec2025'
WHERE NOT EXISTS (SELECT 1 FROM journal_line jl WHERE jl.journal_entry_id = je.id AND jl.line_number = v.line_no);

-- Revenue recognition — January 2026
INSERT INTO journal_entry (book_id, period_id, legal_entity_id, entry_number, entry_date, description, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a', ap.id, '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c',
  'JE-REV-Jan2026', '2026-01-27', 'Revenue recognition January 2026', 'POSTED'
FROM accounting_period ap
WHERE ap.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND ap.period_name = 'January 2026'
ON CONFLICT DO NOTHING;

INSERT INTO journal_line (journal_entry_id, book_id, gl_account_id, line_number, debit_tc, credit_tc, currency)
SELECT je.id, '48972d9f-0f08-4f01-93ce-de078cb8bd3a', ga.id, v.line_no, v.dr, v.cr, 'PKR'
FROM (VALUES (1,'1000',69000,0),(2,'1200',23000,0),(3,'4100',0,92000)) AS v(line_no, code, dr, cr)
JOIN gl_account ga ON ga.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND ga.account_code = v.code
JOIN journal_entry je ON je.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND je.entry_number = 'JE-REV-Jan2026'
WHERE NOT EXISTS (SELECT 1 FROM journal_line jl WHERE jl.journal_entry_id = je.id AND jl.line_number = v.line_no);

-- Expense accrual — January 2026
INSERT INTO journal_entry (book_id, period_id, legal_entity_id, entry_number, entry_date, description, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a', ap.id, '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c',
  'JE-EXP-Jan2026', '2026-01-28', 'Expense accrual January 2026', 'POSTED'
FROM accounting_period ap
WHERE ap.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND ap.period_name = 'January 2026'
ON CONFLICT DO NOTHING;

INSERT INTO journal_line (journal_entry_id, book_id, gl_account_id, line_number, debit_tc, credit_tc, currency)
SELECT je.id, '48972d9f-0f08-4f01-93ce-de078cb8bd3a', ga.id, v.line_no, v.dr, v.cr, 'PKR'
FROM (VALUES (1,'5100',55200,0),(2,'5200',8500,0),(3,'5300',2180,0),(4,'2000',0,65880)) AS v(line_no, code, dr, cr)
JOIN gl_account ga ON ga.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND ga.account_code = v.code
JOIN journal_entry je ON je.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND je.entry_number = 'JE-EXP-Jan2026'
WHERE NOT EXISTS (SELECT 1 FROM journal_line jl WHERE jl.journal_entry_id = je.id AND jl.line_number = v.line_no);

-- Revenue recognition — February 2026
INSERT INTO journal_entry (book_id, period_id, legal_entity_id, entry_number, entry_date, description, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a', ap.id, '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c',
  'JE-REV-Feb2026', '2026-02-24', 'Revenue recognition February 2026', 'POSTED'
FROM accounting_period ap
WHERE ap.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND ap.period_name = 'February 2026'
ON CONFLICT DO NOTHING;

INSERT INTO journal_line (journal_entry_id, book_id, gl_account_id, line_number, debit_tc, credit_tc, currency)
SELECT je.id, '48972d9f-0f08-4f01-93ce-de078cb8bd3a', ga.id, v.line_no, v.dr, v.cr, 'PKR'
FROM (VALUES (1,'1000',58875,0),(2,'1200',19625,0),(3,'4100',0,78500)) AS v(line_no, code, dr, cr)
JOIN gl_account ga ON ga.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND ga.account_code = v.code
JOIN journal_entry je ON je.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND je.entry_number = 'JE-REV-Feb2026'
WHERE NOT EXISTS (SELECT 1 FROM journal_line jl WHERE jl.journal_entry_id = je.id AND jl.line_number = v.line_no);

-- Current month draft entry — March 2026
INSERT INTO journal_entry (book_id, period_id, legal_entity_id, entry_number, entry_date, description, status)
SELECT '48972d9f-0f08-4f01-93ce-de078cb8bd3a', ap.id, '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c',
  'JE-DRAFT-Mar2026', CURRENT_DATE, 'Accrual estimate March 2026', 'DRAFT'
FROM accounting_period ap
WHERE ap.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND ap.period_name = 'March 2026'
ON CONFLICT DO NOTHING;

INSERT INTO journal_line (journal_entry_id, book_id, gl_account_id, line_number, debit_tc, credit_tc, currency)
SELECT je.id, '48972d9f-0f08-4f01-93ce-de078cb8bd3a', ga.id, v.line_no, v.dr, v.cr, 'PKR'
FROM (VALUES (1,'1200',11000,0),(2,'4100',0,11000)) AS v(line_no, code, dr, cr)
JOIN gl_account ga ON ga.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND ga.account_code = v.code
JOIN journal_entry je ON je.book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a' AND je.entry_number = 'JE-DRAFT-Mar2026'
WHERE NOT EXISTS (SELECT 1 FROM journal_line jl WHERE jl.journal_entry_id = je.id AND jl.line_number = v.line_no);

-- ── Verification ─────────────────────────────────────────────────────────────
SELECT 'gl_accounts'        AS tbl, count(*) AS cnt FROM gl_account WHERE book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a'
UNION ALL
SELECT 'accounting_periods', count(*) FROM accounting_period WHERE book_id = '48972d9f-0f08-4f01-93ce-de078cb8bd3a'
UNION ALL
SELECT 'ar_customers',       count(*) FROM ar_customer WHERE legal_entity_id = '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c'
UNION ALL
SELECT 'ar_invoices',        count(*) FROM ar_invoice WHERE legal_entity_id = '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c'
UNION ALL
SELECT 'ap_vendors',         count(*) FROM ap_vendor WHERE legal_entity_id = '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c'
UNION ALL
SELECT 'ap_bills',           count(*) FROM ap_bill WHERE legal_entity_id = '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c'
UNION ALL
SELECT 'journal_entries',    count(*) FROM journal_entry WHERE legal_entity_id = '17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c'
UNION ALL
SELECT 'journal_lines',      count(*) FROM journal_line jl JOIN journal_entry je ON je.id=jl.journal_entry_id WHERE je.legal_entity_id='17bd1a2f-0d6b-4ff0-9c83-a76d87b0a14c';
