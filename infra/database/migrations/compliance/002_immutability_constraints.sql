-- ============================================================================
-- IMMUTABILITY CONSTRAINTS v2 - TrueVow Financial Management Service
-- ============================================================================
-- Corrected against live schema inspection (2026-02-28)
-- Key corrections:
--   - journal_line uses debit_tc/credit_tc (not debit/credit)
--   - journal_entry has no total_debit/total_credit header columns
--   - ar_allocation (not ar_payment_allocation)
--   - ap_allocation (not ap_payment_allocation)
-- ============================================================================

-- ============================================================================
-- TRIGGER 1: Journal Entry Immutability
-- POSTED entries cannot be modified (except status POSTED→REVERSED)
-- ============================================================================
CREATE OR REPLACE FUNCTION prevent_posted_journal_modification()
RETURNS TRIGGER AS $fn$
BEGIN
  IF TG_OP = 'DELETE' AND OLD.status = 'POSTED' THEN
    RAISE EXCEPTION 'Cannot delete POSTED journal entry (id=%)', OLD.id;
  END IF;

  IF TG_OP = 'UPDATE' AND OLD.status = 'POSTED' THEN
    -- Only allow POSTED → REVERSED transition, and only status field changes
    IF NEW.status = 'REVERSED' THEN
      -- Validate that only reversal fields changed
      IF NEW.id         != OLD.id         OR
         NEW.book_id    != OLD.book_id    OR
         NEW.entry_date != OLD.entry_date OR
         NEW.entry_number != OLD.entry_number THEN
        RAISE EXCEPTION 'Cannot modify core fields of POSTED journal entry (id=%)', OLD.id;
      END IF;
      RETURN NEW;  -- allow status update to REVERSED
    ELSE
      RAISE EXCEPTION 'Cannot modify POSTED journal entry (id=%). Only REVERSED transition is allowed.', OLD.id;
    END IF;
  END IF;

  RETURN NEW;
END;
$fn$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS journal_entry_immutability ON journal_entry;
CREATE TRIGGER journal_entry_immutability
BEFORE UPDATE OR DELETE ON journal_entry
FOR EACH ROW EXECUTE FUNCTION prevent_posted_journal_modification();

-- ============================================================================
-- TRIGGER 2: Journal Line Immutability
-- Lines of POSTED entries cannot be modified
-- Uses debit_tc / credit_tc (transaction currency columns)
-- ============================================================================
CREATE OR REPLACE FUNCTION prevent_posted_journal_line_modification()
RETURNS TRIGGER AS $fn$
DECLARE
  v_entry_status TEXT;
BEGIN
  SELECT status INTO v_entry_status
  FROM journal_entry
  WHERE id = COALESCE(OLD.journal_entry_id, NEW.journal_entry_id);

  IF v_entry_status = 'POSTED' THEN
    RAISE EXCEPTION 'Cannot modify journal line of POSTED entry (journal_entry_id=%)',
      COALESCE(OLD.journal_entry_id, NEW.journal_entry_id);
  END IF;

  RETURN NEW;
END;
$fn$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS journal_line_immutability ON journal_line;
CREATE TRIGGER journal_line_immutability
BEFORE UPDATE OR DELETE ON journal_line
FOR EACH ROW EXECUTE FUNCTION prevent_posted_journal_line_modification();

-- ============================================================================
-- TRIGGER 3: Accounting Period Status Transition
-- Periods can only move OPEN → CLOSED, not back
-- ============================================================================
CREATE OR REPLACE FUNCTION prevent_period_status_regression()
RETURNS TRIGGER AS $fn$
BEGIN
  IF TG_OP = 'UPDATE' THEN
    -- CLOSED periods cannot be re-opened
    IF OLD.status = 'CLOSED' AND NEW.status != 'CLOSED' THEN
      RAISE EXCEPTION 'Cannot reopen CLOSED accounting period (id=%)', OLD.id;
    END IF;
    -- Cannot move from CLOSED back to DRAFT
    IF OLD.status = 'CLOSED' AND NEW.status = 'DRAFT' THEN
      RAISE EXCEPTION 'Cannot move accounting period from CLOSED to DRAFT (id=%)', OLD.id;
    END IF;
  END IF;
  RETURN NEW;
END;
$fn$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS accounting_period_status_transition ON accounting_period;
CREATE TRIGGER accounting_period_status_transition
BEFORE UPDATE ON accounting_period
FOR EACH ROW EXECUTE FUNCTION prevent_period_status_regression();

-- ============================================================================
-- TRIGGER 4: Payroll Run Immutability
-- POSTED/PAID payroll runs cannot be modified
-- ============================================================================
CREATE OR REPLACE FUNCTION prevent_posted_payroll_modification()
RETURNS TRIGGER AS $fn$
BEGIN
  IF TG_OP = 'DELETE' AND OLD.status IN ('POSTED', 'PAID') THEN
    RAISE EXCEPTION 'Cannot delete POSTED/PAID payroll run (id=%)', OLD.id;
  END IF;

  IF TG_OP = 'UPDATE' AND OLD.status IN ('POSTED', 'PAID') THEN
    -- Only allow status field update (e.g., POSTED → PAID)
    IF NEW.total_gross          != OLD.total_gross          OR
       NEW.total_deductions     != OLD.total_deductions     OR
       NEW.total_net            != OLD.total_net            OR
       NEW.pay_period_start     != OLD.pay_period_start     OR
       NEW.pay_period_end       != OLD.pay_period_end       THEN
      RAISE EXCEPTION 'Cannot modify financial fields of POSTED/PAID payroll run (id=%)', OLD.id;
    END IF;
  END IF;
  RETURN NEW;
END;
$fn$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS payroll_run_immutability ON payroll_run;
CREATE TRIGGER payroll_run_immutability
BEFORE UPDATE OR DELETE ON payroll_run
FOR EACH ROW EXECUTE FUNCTION prevent_posted_payroll_modification();

-- ============================================================================
-- TRIGGER 5: AR Invoice Status Transition
-- Prevent backward status transitions (POSTED cannot go back to DRAFT)
-- ============================================================================
CREATE OR REPLACE FUNCTION prevent_ar_invoice_status_regression()
RETURNS TRIGGER AS $fn$
BEGIN
  IF TG_OP = 'UPDATE' THEN
    -- PAID invoices cannot be re-opened
    IF OLD.status = 'PAID' AND NEW.status IN ('DRAFT', 'SENT') THEN
      RAISE EXCEPTION 'Cannot revert PAID AR invoice to % (id=%)', NEW.status, OLD.id;
    END IF;
    -- VOID invoices are final
    IF OLD.status = 'VOID' AND NEW.status != 'VOID' THEN
      RAISE EXCEPTION 'Cannot change status of VOID AR invoice (id=%)', OLD.id;
    END IF;
  END IF;
  RETURN NEW;
END;
$fn$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS ar_invoice_timestamps ON ar_invoice;
CREATE TRIGGER ar_invoice_timestamps
BEFORE UPDATE ON ar_invoice
FOR EACH ROW EXECUTE FUNCTION prevent_ar_invoice_status_regression();

-- ============================================================================
-- TRIGGER 6: AP Bill Status Transition
-- ============================================================================
CREATE OR REPLACE FUNCTION prevent_ap_bill_status_regression()
RETURNS TRIGGER AS $fn$
BEGIN
  IF TG_OP = 'UPDATE' THEN
    IF OLD.status = 'PAID' AND NEW.status IN ('DRAFT', 'APPROVED') THEN
      RAISE EXCEPTION 'Cannot revert PAID AP bill to % (id=%)', NEW.status, OLD.id;
    END IF;
    IF OLD.status = 'VOID' AND NEW.status != 'VOID' THEN
      RAISE EXCEPTION 'Cannot change status of VOID AP bill (id=%)', OLD.id;
    END IF;
  END IF;
  RETURN NEW;
END;
$fn$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS ap_bill_timestamps ON ap_bill;
CREATE TRIGGER ap_bill_timestamps
BEFORE UPDATE ON ap_bill
FOR EACH ROW EXECUTE FUNCTION prevent_ap_bill_status_regression();

-- ============================================================================
-- CHECK CONSTRAINT: Journal Line — debit/credit not both zero
-- Uses debit_tc / credit_tc (transaction currency columns)
-- ============================================================================
ALTER TABLE journal_line DROP CONSTRAINT IF EXISTS journal_line_amount_not_zero;
ALTER TABLE journal_line
ADD CONSTRAINT journal_line_amount_not_zero
CHECK (debit_tc != 0 OR credit_tc != 0);

ALTER TABLE journal_line DROP CONSTRAINT IF EXISTS journal_line_debit_or_credit;
ALTER TABLE journal_line
ADD CONSTRAINT journal_line_debit_or_credit
CHECK (
  (debit_tc > 0 AND credit_tc = 0)
  OR
  (credit_tc > 0 AND debit_tc = 0)
);

-- ============================================================================
-- CHECK CONSTRAINT: AR Allocation — positive amount
-- ============================================================================
ALTER TABLE ar_allocation DROP CONSTRAINT IF EXISTS ar_allocation_amount_positive;
ALTER TABLE ar_allocation
ADD CONSTRAINT ar_allocation_amount_positive
CHECK (allocated_amount > 0);

-- ============================================================================
-- CHECK CONSTRAINT: AP Allocation — positive amount
-- ============================================================================
ALTER TABLE ap_allocation DROP CONSTRAINT IF EXISTS ap_allocation_amount_positive;
ALTER TABLE ap_allocation
ADD CONSTRAINT ap_allocation_amount_positive
CHECK (allocated_amount > 0);

-- ============================================================================
-- VERIFICATION
-- ============================================================================
SELECT event_object_table, trigger_name, event_manipulation
FROM information_schema.triggers
WHERE trigger_schema = 'public'
ORDER BY event_object_table, trigger_name;

SELECT table_name, constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE constraint_schema = 'public'
  AND constraint_type = 'CHECK'
  AND constraint_name LIKE '%immutability%'
  OR constraint_name LIKE '%amount%'
  OR constraint_name LIKE '%debit%'
ORDER BY table_name;
