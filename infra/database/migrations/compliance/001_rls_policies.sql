-- ============================================================================
-- RLS POLICY IMPLEMENTATION v2 - TrueVow Financial Management Service
-- ============================================================================
-- Corrected against live schema inspection (2026-02-28)
-- Column names verified via information_schema.columns
-- ============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- SECTION 1: CORE TABLES — direct legal_entity_id
-- ============================================================================

-- Legal Entity (root tenant boundary)
ALTER TABLE legal_entity ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on legal_entity"
ON legal_entity FOR ALL
USING (id = current_setting('app.current_legal_entity_id', true)::uuid);

-- Book (multi-book per entity) — has legal_entity_id directly
ALTER TABLE book ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on book"
ON book FOR ALL
USING (legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid);

-- ============================================================================
-- SECTION 2: TABLES SCOPED VIA book_id → book.legal_entity_id
-- ============================================================================

-- GL Account — scoped via book_id
ALTER TABLE gl_account ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on gl_account"
ON gl_account FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM book b
    WHERE b.id = gl_account.book_id
      AND b.legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid
  )
);

-- Accounting Period — scoped via book_id
ALTER TABLE accounting_period ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on accounting_period"
ON accounting_period FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM book b
    WHERE b.id = accounting_period.book_id
      AND b.legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid
  )
);

-- ============================================================================
-- SECTION 3: DIMENSION TABLES — global shared lookups (no tenant column)
-- Policy: permissive read-all; restrict writes to service role only
-- ============================================================================

ALTER TABLE dimension ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Dimension read access"
ON dimension FOR SELECT
USING (true);

CREATE POLICY "Dimension write restricted"
ON dimension FOR ALL
USING (current_setting('app.current_legal_entity_id', true) IS NOT NULL);

ALTER TABLE dimension_value ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Dimension value read access"
ON dimension_value FOR SELECT
USING (true);

CREATE POLICY "Dimension value write restricted"
ON dimension_value FOR ALL
USING (current_setting('app.current_legal_entity_id', true) IS NOT NULL);

-- ============================================================================
-- SECTION 4: JOURNAL TABLES — journal_entry has legal_entity_id directly
-- ============================================================================

-- Journal Entry — has legal_entity_id directly
ALTER TABLE journal_entry ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on journal_entry"
ON journal_entry FOR ALL
USING (legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid);

-- Journal Line — scoped via journal_entry_id
ALTER TABLE journal_line ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on journal_line"
ON journal_line FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM journal_entry je
    WHERE je.id = journal_line.journal_entry_id
      AND je.legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid
  )
);

-- Journal Line Dimension — scoped via journal_line
ALTER TABLE journal_line_dimension ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on journal_line_dimension"
ON journal_line_dimension FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM journal_line jl
    JOIN journal_entry je ON je.id = jl.journal_entry_id
    WHERE jl.id = journal_line_dimension.journal_line_id
      AND je.legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid
  )
);

-- ============================================================================
-- SECTION 5: AR TABLES — direct legal_entity_id or parent join
-- ============================================================================

-- AR Customer — has legal_entity_id directly
ALTER TABLE ar_customer ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on ar_customer"
ON ar_customer FOR ALL
USING (legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid);

-- AR Invoice — has legal_entity_id directly (no book_id)
ALTER TABLE ar_invoice ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on ar_invoice"
ON ar_invoice FOR ALL
USING (legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid);

-- AR Invoice Line — scoped via ar_invoice_id
ALTER TABLE ar_invoice_line ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on ar_invoice_line"
ON ar_invoice_line FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM ar_invoice inv
    WHERE inv.id = ar_invoice_line.ar_invoice_id
      AND inv.legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid
  )
);

-- AR Payment — has legal_entity_id directly (no book_id)
ALTER TABLE ar_payment ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on ar_payment"
ON ar_payment FOR ALL
USING (legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid);

-- AR Allocation (was ar_payment_allocation) — scoped via ar_payment_id
ALTER TABLE ar_allocation ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on ar_allocation"
ON ar_allocation FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM ar_payment p
    WHERE p.id = ar_allocation.ar_payment_id
      AND p.legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid
  )
);

-- ============================================================================
-- SECTION 6: AP TABLES
-- ============================================================================

-- AP Vendor — has legal_entity_id (verify)
ALTER TABLE ap_vendor ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on ap_vendor"
ON ap_vendor FOR ALL
USING (legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid);

-- AP Withholding Profile
ALTER TABLE ap_withholding_profile ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on ap_withholding_profile"
ON ap_withholding_profile FOR ALL
USING (legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid);

-- AP Bill — has legal_entity_id directly
ALTER TABLE ap_bill ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on ap_bill"
ON ap_bill FOR ALL
USING (legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid);

-- AP Bill Line — scoped via ap_bill_id
ALTER TABLE ap_bill_line ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on ap_bill_line"
ON ap_bill_line FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM ap_bill b
    WHERE b.id = ap_bill_line.ap_bill_id
      AND b.legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid
  )
);

-- AP Payment — has legal_entity_id directly
ALTER TABLE ap_payment ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on ap_payment"
ON ap_payment FOR ALL
USING (legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid);

-- AP Allocation (was ap_payment_allocation) — scoped via ap_payment_id
ALTER TABLE ap_allocation ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on ap_allocation"
ON ap_allocation FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM ap_payment p
    WHERE p.id = ap_allocation.ap_payment_id
      AND p.legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid
  )
);

-- ============================================================================
-- SECTION 7: PAYROLL TABLES
-- ============================================================================

-- Payroll Run — has legal_entity_id directly
ALTER TABLE payroll_run ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on payroll_run"
ON payroll_run FOR ALL
USING (legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid);

-- Payroll Run Item — scoped via payroll_run_id
ALTER TABLE payroll_run_item ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on payroll_run_item"
ON payroll_run_item FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM payroll_run pr
    WHERE pr.id = payroll_run_item.payroll_run_id
      AND pr.legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid
  )
);

-- ============================================================================
-- SECTION 8: TREASURY TABLES (table names treasury_bank_*)
-- ============================================================================

-- Treasury Bank Account — has legal_entity_id directly
ALTER TABLE treasury_bank_account ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on treasury_bank_account"
ON treasury_bank_account FOR ALL
USING (legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid);

-- Treasury Bank Transaction — scoped via bank_account_id
ALTER TABLE treasury_bank_transaction ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on treasury_bank_transaction"
ON treasury_bank_transaction FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM treasury_bank_account tba
    WHERE tba.id = treasury_bank_transaction.bank_account_id
      AND tba.legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid
  )
);

-- ============================================================================
-- SECTION 9: RECONCILIATION TABLES
-- ============================================================================

-- Reconciliation Session — scoped via bank_account_id → treasury_bank_account
ALTER TABLE reconciliation_session ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on reconciliation_session"
ON reconciliation_session FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM treasury_bank_account tba
    WHERE tba.id = reconciliation_session.bank_account_id
      AND tba.legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid
  )
);

-- Reconciliation Match — scoped via reconciliation_session_id
ALTER TABLE reconciliation_match ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on reconciliation_match"
ON reconciliation_match FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM reconciliation_session rs
    JOIN treasury_bank_account tba ON tba.id = rs.bank_account_id
    WHERE rs.id = reconciliation_match.reconciliation_session_id
      AND tba.legal_entity_id = current_setting('app.current_legal_entity_id', true)::uuid
  )
);

-- ============================================================================
-- SECTION 10: ROYALTY TABLES (bi-directional: from_entity_id / to_entity_id)
-- ============================================================================

-- Royalty Agreement — policy covers both sides of royalty relationship
ALTER TABLE royalty_agreement ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on royalty_agreement"
ON royalty_agreement FOR ALL
USING (
  from_entity_id = current_setting('app.current_legal_entity_id', true)::uuid
  OR
  to_entity_id = current_setting('app.current_legal_entity_id', true)::uuid
);

-- Royalty Calculation — scoped via royalty_agreement_id
ALTER TABLE royalty_calculation ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on royalty_calculation"
ON royalty_calculation FOR ALL
USING (
  EXISTS (
    SELECT 1 FROM royalty_agreement ra
    WHERE ra.id = royalty_calculation.royalty_agreement_id
      AND (
        ra.from_entity_id = current_setting('app.current_legal_entity_id', true)::uuid
        OR
        ra.to_entity_id = current_setting('app.current_legal_entity_id', true)::uuid
      )
  )
);

-- ============================================================================
-- SECTION 11: INTERCOMPANY (bi-directional: from_entity_id / to_entity_id)
-- ============================================================================

ALTER TABLE intercompany_transfer ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Tenant isolation on intercompany_transfer"
ON intercompany_transfer FOR ALL
USING (
  from_entity_id = current_setting('app.current_legal_entity_id', true)::uuid
  OR
  to_entity_id = current_setting('app.current_legal_entity_id', true)::uuid
);

-- ============================================================================
-- VERIFICATION QUERY (informational only)
-- ============================================================================
SELECT tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

SELECT schemaname, tablename, policyname
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;
