-- ============================================================================
-- BUSINESS CONSTRAINTS v2 - TrueVow Financial Management Service
-- ============================================================================
-- Corrected against live schema inspection (2026-02-28)
-- Key corrections:
--   - gl_account uses book_id (not legal_entity_id), account_code (not code)
--   - dimension has no legal_entity_id (global lookup)
--   - dimension_value uses dimension_code (not dimension_id)
--   - ar_invoice has legal_entity_id (not book_id)
--   - bank_account → treasury_bank_account
--   - ar/ap_payment_allocation → ar/ap_allocation
--   - journal_entry has no total_debit/total_credit columns
--   - journal_line uses debit_tc/credit_tc
--   - book_type uniqueness skipped (data already has duplicates — by design)
-- ============================================================================

-- ============================================================================
-- SECTION 1: BOOK CONSTRAINTS
-- ============================================================================

-- Book name uniqueness per entity
ALTER TABLE book DROP CONSTRAINT IF EXISTS book_name_unique_per_entity;
ALTER TABLE book
ADD CONSTRAINT book_name_unique_per_entity
UNIQUE (legal_entity_id, name);

-- ============================================================================
-- SECTION 2: GL ACCOUNT CONSTRAINTS
-- gl_account is scoped via book_id (no legal_entity_id directly)
-- ============================================================================

-- Account code uniqueness per book
ALTER TABLE gl_account DROP CONSTRAINT IF EXISTS gl_account_code_unique_per_book;
ALTER TABLE gl_account
ADD CONSTRAINT gl_account_code_unique_per_book
UNIQUE (book_id, account_code);

-- GL Account mapping: unique map_key per book
ALTER TABLE gl_account_mapping DROP CONSTRAINT IF EXISTS gl_account_mapping_unique_per_book;
ALTER TABLE gl_account_mapping
ADD CONSTRAINT gl_account_mapping_unique_per_book
UNIQUE (book_id, map_key);

-- ============================================================================
-- SECTION 3: ACCOUNTING PERIOD CONSTRAINTS
-- ============================================================================

-- Period name uniqueness per book
ALTER TABLE accounting_period DROP CONSTRAINT IF EXISTS accounting_period_name_unique_per_book;
ALTER TABLE accounting_period
ADD CONSTRAINT accounting_period_name_unique_per_book
UNIQUE (book_id, period_name);

-- Period overlap prevention
CREATE OR REPLACE FUNCTION validate_period_no_overlap()
RETURNS TRIGGER AS $fn$
DECLARE
  v_overlap_count INT;
BEGIN
  SELECT COUNT(*) INTO v_overlap_count
  FROM accounting_period
  WHERE book_id = NEW.book_id
    AND id != COALESCE(NEW.id, '00000000-0000-0000-0000-000000000000'::uuid)
    AND (
      (NEW.start_date >= start_date AND NEW.start_date < end_date) OR
      (NEW.end_date   >  start_date AND NEW.end_date  <= end_date) OR
      (NEW.start_date <= start_date AND NEW.end_date  >= end_date)
    );

  IF v_overlap_count > 0 THEN
    RAISE EXCEPTION 'Accounting period overlaps with an existing period for book_id=%', NEW.book_id;
  END IF;
  RETURN NEW;
END;
$fn$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS accounting_period_no_overlap ON accounting_period;
CREATE TRIGGER accounting_period_no_overlap
BEFORE INSERT OR UPDATE ON accounting_period
FOR EACH ROW EXECUTE FUNCTION validate_period_no_overlap();

-- ============================================================================
-- SECTION 4: JOURNAL CONSTRAINTS
-- ============================================================================

-- Entry number uniqueness per book
ALTER TABLE journal_entry DROP CONSTRAINT IF EXISTS journal_entry_number_unique_per_book;
ALTER TABLE journal_entry
ADD CONSTRAINT journal_entry_number_unique_per_book
UNIQUE (book_id, entry_number);

-- Journal line: debit and credit cannot both be non-zero
-- (uses debit_tc / credit_tc — transaction currency)
ALTER TABLE journal_line DROP CONSTRAINT IF EXISTS journal_line_debit_xor_credit;
ALTER TABLE journal_line
ADD CONSTRAINT journal_line_debit_xor_credit
CHECK (
  (debit_tc > 0 AND credit_tc = 0)
  OR
  (credit_tc > 0 AND debit_tc = 0)
);

-- Journal line: at least one side must be non-zero
ALTER TABLE journal_line DROP CONSTRAINT IF EXISTS journal_line_nonzero_amount;
ALTER TABLE journal_line
ADD CONSTRAINT journal_line_nonzero_amount
CHECK (debit_tc > 0 OR credit_tc > 0);

-- ============================================================================
-- SECTION 5: AR CONSTRAINTS
-- ar_invoice has legal_entity_id directly (no book_id)
-- ============================================================================

-- Invoice number uniqueness per entity
ALTER TABLE ar_invoice DROP CONSTRAINT IF EXISTS ar_invoice_number_unique_per_entity;
ALTER TABLE ar_invoice
ADD CONSTRAINT ar_invoice_number_unique_per_entity
UNIQUE (legal_entity_id, invoice_number);

-- AR Invoice: amounts must be logically consistent
ALTER TABLE ar_invoice DROP CONSTRAINT IF EXISTS ar_invoice_paid_not_exceed_total;
ALTER TABLE ar_invoice
ADD CONSTRAINT ar_invoice_paid_not_exceed_total
CHECK (paid_amount <= total_amount);

ALTER TABLE ar_invoice DROP CONSTRAINT IF EXISTS ar_invoice_outstanding_not_negative;
ALTER TABLE ar_invoice
ADD CONSTRAINT ar_invoice_outstanding_not_negative
CHECK (outstanding_amount >= 0);

-- AR Invoice: total_amount must be positive
ALTER TABLE ar_invoice DROP CONSTRAINT IF EXISTS ar_invoice_total_amount_positive;
ALTER TABLE ar_invoice
ADD CONSTRAINT ar_invoice_total_amount_positive
CHECK (total_amount > 0);

-- AR Invoice Line: line amount positive
ALTER TABLE ar_invoice_line DROP CONSTRAINT IF EXISTS ar_invoice_line_amount_positive;
ALTER TABLE ar_invoice_line
ADD CONSTRAINT ar_invoice_line_amount_positive
CHECK (line_amount > 0);

-- AR Payment: payment amount positive
ALTER TABLE ar_payment DROP CONSTRAINT IF EXISTS ar_payment_amount_positive;
ALTER TABLE ar_payment
ADD CONSTRAINT ar_payment_amount_positive
CHECK (payment_amount > 0);

-- AR Allocation: allocated amount positive
ALTER TABLE ar_allocation DROP CONSTRAINT IF EXISTS ar_allocation_amount_positive;
ALTER TABLE ar_allocation
ADD CONSTRAINT ar_allocation_amount_positive
CHECK (allocated_amount > 0);

-- ============================================================================
-- SECTION 6: AP CONSTRAINTS
-- ============================================================================

-- Bill number uniqueness per entity
ALTER TABLE ap_bill DROP CONSTRAINT IF EXISTS ap_bill_number_unique_per_entity;
ALTER TABLE ap_bill
ADD CONSTRAINT ap_bill_number_unique_per_entity
UNIQUE (legal_entity_id, bill_number);

-- AP Bill: amounts must be logical
ALTER TABLE ap_bill DROP CONSTRAINT IF EXISTS ap_bill_paid_not_exceed_total;
ALTER TABLE ap_bill
ADD CONSTRAINT ap_bill_paid_not_exceed_total
CHECK (paid_amount <= total_amount);

ALTER TABLE ap_bill DROP CONSTRAINT IF EXISTS ap_bill_outstanding_not_negative;
ALTER TABLE ap_bill
ADD CONSTRAINT ap_bill_outstanding_not_negative
CHECK (outstanding_amount >= 0);

ALTER TABLE ap_bill DROP CONSTRAINT IF EXISTS ap_bill_total_amount_positive;
ALTER TABLE ap_bill
ADD CONSTRAINT ap_bill_total_amount_positive
CHECK (total_amount > 0);

-- AP Bill Line: line amount positive
ALTER TABLE ap_bill_line DROP CONSTRAINT IF EXISTS ap_bill_line_amount_positive;
ALTER TABLE ap_bill_line
ADD CONSTRAINT ap_bill_line_amount_positive
CHECK (line_amount > 0);

-- AP Payment: positive amount
ALTER TABLE ap_payment DROP CONSTRAINT IF EXISTS ap_payment_amount_positive;
ALTER TABLE ap_payment
ADD CONSTRAINT ap_payment_amount_positive
CHECK (payment_amount > 0);

-- AP Allocation: positive amount
ALTER TABLE ap_allocation DROP CONSTRAINT IF EXISTS ap_allocation_amount_positive;
ALTER TABLE ap_allocation
ADD CONSTRAINT ap_allocation_amount_positive
CHECK (allocated_amount > 0);

-- ============================================================================
-- SECTION 7: TREASURY CONSTRAINTS
-- ============================================================================

-- Treasury bank account: unique account number per entity
ALTER TABLE treasury_bank_account DROP CONSTRAINT IF EXISTS treasury_bank_account_number_unique_per_entity;
ALTER TABLE treasury_bank_account
ADD CONSTRAINT treasury_bank_account_number_unique_per_entity
UNIQUE (legal_entity_id, account_number);

-- ============================================================================
-- SECTION 8: PAYROLL CONSTRAINTS
-- ============================================================================

-- Payroll run number uniqueness per legal entity
ALTER TABLE payroll_run DROP CONSTRAINT IF EXISTS payroll_run_number_unique_per_entity;
ALTER TABLE payroll_run
ADD CONSTRAINT payroll_run_number_unique_per_entity
UNIQUE (legal_entity_id, run_number);

-- Payroll amounts: positive gross pay
ALTER TABLE payroll_run DROP CONSTRAINT IF EXISTS payroll_run_total_gross_positive;
ALTER TABLE payroll_run
ADD CONSTRAINT payroll_run_total_gross_positive
CHECK (total_gross >= 0);

ALTER TABLE payroll_run DROP CONSTRAINT IF EXISTS payroll_run_net_not_exceed_gross;
ALTER TABLE payroll_run
ADD CONSTRAINT payroll_run_net_not_exceed_gross
CHECK (total_net <= total_gross);

-- ============================================================================
-- SECTION 9: ROYALTY CONSTRAINTS
-- ============================================================================

-- Royalty rate must be between 0 and 1 (percentage basis)
ALTER TABLE royalty_agreement DROP CONSTRAINT IF EXISTS royalty_agreement_rate_range;
ALTER TABLE royalty_agreement
ADD CONSTRAINT royalty_agreement_rate_range
CHECK (rate IS NULL OR (rate >= 0 AND rate <= 1));

-- Royalty calculation amount positive
ALTER TABLE royalty_calculation DROP CONSTRAINT IF EXISTS royalty_calculation_amount_positive;
ALTER TABLE royalty_calculation
ADD CONSTRAINT royalty_calculation_amount_positive
CHECK (royalty_amount >= 0);

-- ============================================================================
-- SECTION 10: PERFORMANCE INDEXES
-- ============================================================================

-- Journal Entry indexes
CREATE INDEX IF NOT EXISTS idx_journal_entry_legal_entity ON journal_entry(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_journal_entry_book_status ON journal_entry(book_id, status);
CREATE INDEX IF NOT EXISTS idx_journal_entry_entry_date ON journal_entry(entry_date);
CREATE INDEX IF NOT EXISTS idx_journal_entry_source ON journal_entry(source_service, source_type, source_id);
CREATE INDEX IF NOT EXISTS idx_journal_entry_idempotency ON journal_entry(idempotency_key) WHERE idempotency_key IS NOT NULL;

-- Journal Line indexes
CREATE INDEX IF NOT EXISTS idx_journal_line_entry ON journal_line(journal_entry_id);
CREATE INDEX IF NOT EXISTS idx_journal_line_account ON journal_line(gl_account_id);

-- GL Account indexes
CREATE INDEX IF NOT EXISTS idx_gl_account_book ON gl_account(book_id);
CREATE INDEX IF NOT EXISTS idx_gl_account_code ON gl_account(book_id, account_code);

-- Accounting Period indexes
CREATE INDEX IF NOT EXISTS idx_accounting_period_book ON accounting_period(book_id, status);
CREATE INDEX IF NOT EXISTS idx_accounting_period_dates ON accounting_period(start_date, end_date);

-- AR indexes
CREATE INDEX IF NOT EXISTS idx_ar_invoice_entity ON ar_invoice(legal_entity_id, status);
CREATE INDEX IF NOT EXISTS idx_ar_invoice_customer ON ar_invoice(ar_customer_id);
CREATE INDEX IF NOT EXISTS idx_ar_payment_entity ON ar_payment(legal_entity_id, status);
CREATE INDEX IF NOT EXISTS idx_ar_allocation_payment ON ar_allocation(ar_payment_id);
CREATE INDEX IF NOT EXISTS idx_ar_allocation_invoice ON ar_allocation(ar_invoice_id);

-- AP indexes
CREATE INDEX IF NOT EXISTS idx_ap_bill_entity ON ap_bill(legal_entity_id, status);
CREATE INDEX IF NOT EXISTS idx_ap_bill_vendor ON ap_bill(ap_vendor_id);
CREATE INDEX IF NOT EXISTS idx_ap_payment_entity ON ap_payment(legal_entity_id, status);
CREATE INDEX IF NOT EXISTS idx_ap_allocation_payment ON ap_allocation(ap_payment_id);
CREATE INDEX IF NOT EXISTS idx_ap_allocation_bill ON ap_allocation(ap_bill_id);

-- Payroll indexes
CREATE INDEX IF NOT EXISTS idx_payroll_run_entity ON payroll_run(legal_entity_id, status);
CREATE INDEX IF NOT EXISTS idx_payroll_run_item_run ON payroll_run_item(payroll_run_id);

-- Treasury indexes
CREATE INDEX IF NOT EXISTS idx_treasury_bank_account_entity ON treasury_bank_account(legal_entity_id);
CREATE INDEX IF NOT EXISTS idx_treasury_bank_txn_account ON treasury_bank_transaction(bank_account_id);
CREATE INDEX IF NOT EXISTS idx_treasury_bank_txn_date ON treasury_bank_transaction(transaction_date);

-- Royalty indexes
CREATE INDEX IF NOT EXISTS idx_royalty_agreement_from ON royalty_agreement(from_entity_id);
CREATE INDEX IF NOT EXISTS idx_royalty_agreement_to ON royalty_agreement(to_entity_id);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
SELECT tc.table_name, tc.constraint_type, COUNT(*) AS cnt
FROM information_schema.table_constraints tc
WHERE tc.constraint_schema = 'public'
  AND tc.constraint_type IN ('UNIQUE', 'CHECK')
GROUP BY tc.table_name, tc.constraint_type
ORDER BY tc.table_name, tc.constraint_type;

SELECT COUNT(*) AS total_indexes FROM pg_indexes
WHERE schemaname = 'public' AND indexname LIKE 'idx_%';
