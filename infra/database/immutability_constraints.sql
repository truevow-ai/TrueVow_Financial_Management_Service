-- =====================================================
-- TrueVow Financial Management - Immutability Constraints
-- =====================================================
-- Purpose: Prevent modification of POSTED/CLOSED entries
-- Priority: P1 - URGENT (Complete within 24 hours)
-- Date: 2026-03-02
-- =====================================================
--
-- INSTRUCTIONS:
-- 1. Run this script in Supabase SQL Editor or via psql
-- 2. The script is IDEMPOTENT - safe to run multiple times
-- 3. After running, test by attempting to UPDATE a POSTED entry
--
-- WHAT THIS PROTECTS:
-- - journal_entry: Cannot modify POSTED entries
-- - journal_line: Cannot modify lines of POSTED entries
-- - accounting_period: Cannot modify CLOSED/LOCKED periods
-- - payroll_run: Cannot modify POSTED runs
-- - ar_payment_allocation: Immutable after creation
-- =====================================================

-- =====================================================
-- PART 1: HELPER FUNCTIONS
-- =====================================================

-- Function to check if a journal entry is POSTED
CREATE OR REPLACE FUNCTION is_journal_entry_posted(p_journal_entry_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM journal_entry 
        WHERE id = p_journal_entry_id AND status = 'POSTED'
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to check if an accounting period is CLOSED or LOCKED
CREATE OR REPLACE FUNCTION is_period_closed_or_locked(p_period_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM accounting_period 
        WHERE id = p_period_id AND status IN ('CLOSED', 'LOCKED')
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to check if a payroll run is POSTED
CREATE OR REPLACE FUNCTION is_payroll_run_posted(p_payroll_run_id UUID)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM payroll_run 
        WHERE id = p_payroll_run_id AND status = 'POSTED'
    );
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================
-- PART 2: JOURNAL ENTRY IMMUTABILITY
-- =====================================================

-- Trigger function to prevent modification of POSTED journal entries
CREATE OR REPLACE FUNCTION prevent_journal_entry_modification()
RETURNS TRIGGER AS $$
BEGIN
    -- On UPDATE: Prevent any changes to POSTED entries (except reversal fields)
    IF TG_OP = 'UPDATE' THEN
        IF OLD.status = 'POSTED' THEN
            -- Allow only the reversal_reference update for reversals
            IF NEW.status != 'REVERSED' THEN
                -- Check if any field changed (other than updated_at which is automatic)
                IF ROW(OLD.id, OLD.book_id, OLD.period_id, OLD.entry_number, OLD.entry_date, 
                       OLD.description, OLD.reference_number, OLD.source_service, 
                       OLD.source_type, OLD.source_id, OLD.idempotency_key) IS DISTINCT FROM
                   ROW(NEW.id, NEW.book_id, NEW.period_id, NEW.entry_number, NEW.entry_date, 
                       NEW.description, NEW.reference_number, NEW.source_service, 
                       NEW.source_type, NEW.source_id, NEW.idempotency_key) THEN
                    RAISE EXCEPTION 'Cannot modify POSTED journal entry. Entry: %', OLD.entry_number;
                END IF;
            END IF;
        END IF;
        
        -- Prevent changing status from REVERSED back to anything else
        IF OLD.status = 'REVERSED' AND NEW.status != 'REVERSED' THEN
            RAISE EXCEPTION 'Cannot change status of REVERSED journal entry. Entry: %', OLD.entry_number;
        END IF;
    END IF;
    
    -- On DELETE: Prevent deletion of POSTED entries
    IF TG_OP = 'DELETE' THEN
        IF OLD.status IN ('POSTED', 'REVERSED') THEN
            RAISE EXCEPTION 'Cannot delete POSTED or REVERSED journal entry. Entry: %', OLD.entry_number;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if exists, then create
DROP TRIGGER IF EXISTS journal_entry_immutability ON journal_entry;
CREATE TRIGGER journal_entry_immutability
    BEFORE UPDATE OR DELETE ON journal_entry
    FOR EACH ROW
    EXECUTE FUNCTION prevent_journal_entry_modification();

-- =====================================================
-- PART 3: JOURNAL LINE IMMUTABILITY
-- =====================================================

-- Trigger function to prevent modification of journal lines for POSTED entries
CREATE OR REPLACE FUNCTION prevent_journal_line_modification()
RETURNS TRIGGER AS $$
BEGIN
    -- On INSERT: Check if journal entry is already POSTED
    IF TG_OP = 'INSERT' THEN
        IF is_journal_entry_posted(NEW.journal_entry_id) THEN
            RAISE EXCEPTION 'Cannot add lines to POSTED journal entry.';
        END IF;
    END IF;
    
    -- On UPDATE: Check if journal entry is POSTED
    IF TG_OP = 'UPDATE' THEN
        IF is_journal_entry_posted(NEW.journal_entry_id) THEN
            RAISE EXCEPTION 'Cannot modify lines of POSTED journal entry.';
        END IF;
    END IF;
    
    -- On DELETE: Check if journal entry is POSTED
    IF TG_OP = 'DELETE' THEN
        IF is_journal_entry_posted(OLD.journal_entry_id) THEN
            RAISE EXCEPTION 'Cannot delete lines from POSTED journal entry.';
        END IF;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if exists, then create
DROP TRIGGER IF EXISTS journal_line_immutability ON journal_line;
CREATE TRIGGER journal_line_immutability
    BEFORE INSERT OR UPDATE OR DELETE ON journal_line
    FOR EACH ROW
    EXECUTE FUNCTION prevent_journal_line_modification();

-- =====================================================
-- PART 4: ACCOUNTING PERIOD IMMUTABILITY
-- =====================================================

-- Trigger function to prevent modification of CLOSED/LOCKED periods
CREATE OR REPLACE FUNCTION prevent_period_modification()
RETURNS TRIGGER AS $$
BEGIN
    -- On UPDATE: Prevent changes to CLOSED/LOCKED periods (except status transitions)
    IF TG_OP = 'UPDATE' THEN
        IF OLD.status = 'LOCKED' THEN
            -- LOCKED periods cannot be modified at all
            IF ROW(OLD.*) IS DISTINCT FROM ROW(NEW.*) THEN
                RAISE EXCEPTION 'Cannot modify LOCKED accounting period. Period: %', OLD.period_name;
            END IF;
        END IF;
        
        IF OLD.status = 'CLOSED' THEN
            -- CLOSED periods can only transition to LOCKED
            IF NEW.status != 'LOCKED' THEN
                RAISE EXCEPTION 'CLOSED period can only transition to LOCKED. Period: %', OLD.period_name;
            END IF;
            -- No other changes allowed
            IF OLD.start_date != NEW.start_date OR OLD.end_date != NEW.end_date THEN
                RAISE EXCEPTION 'Cannot modify dates of CLOSED period. Period: %', OLD.period_name;
            END IF;
        END IF;
        
        -- Prevent changing status from CLOSED/LOCKED back to OPEN
        IF OLD.status IN ('CLOSED', 'LOCKED') AND NEW.status NOT IN ('CLOSED', 'LOCKED') THEN
            RAISE EXCEPTION 'Cannot reopen CLOSED or LOCKED period. Period: %', OLD.period_name;
        END IF;
    END IF;
    
    -- On DELETE: Prevent deletion of CLOSED/LOCKED periods
    IF TG_OP = 'DELETE' THEN
        IF OLD.status IN ('CLOSED', 'LOCKED') THEN
            RAISE EXCEPTION 'Cannot delete CLOSED or LOCKED accounting period. Period: %', OLD.period_name;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if exists, then create
DROP TRIGGER IF EXISTS accounting_period_immutability ON accounting_period;
CREATE TRIGGER accounting_period_immutability
    BEFORE UPDATE OR DELETE ON accounting_period
    FOR EACH ROW
    EXECUTE FUNCTION prevent_period_modification();

-- =====================================================
-- PART 5: PAYROLL RUN IMMUTABILITY
-- =====================================================

-- Trigger function to prevent modification of POSTED payroll runs
CREATE OR REPLACE FUNCTION prevent_payroll_run_modification()
RETURNS TRIGGER AS $$
BEGIN
    -- On UPDATE: Prevent changes to POSTED runs
    IF TG_OP = 'UPDATE' THEN
        IF OLD.status = 'POSTED' THEN
            -- No changes allowed to posted runs (except automatic updated_at)
            IF ROW(OLD.id, OLD.legal_entity_id, OLD.book_id, OLD.pay_group_id, 
                   OLD.run_number, OLD.pay_period_start, OLD.pay_period_end, 
                   OLD.pay_date, OLD.total_gross, OLD.total_deductions, 
                   OLD.total_net, OLD.total_employer_contrib, OLD.currency) IS DISTINCT FROM
               ROW(NEW.id, NEW.legal_entity_id, NEW.book_id, NEW.pay_group_id, 
                   NEW.run_number, NEW.pay_period_start, NEW.pay_period_end, 
                   NEW.pay_date, NEW.total_gross, NEW.total_deductions, 
                   NEW.total_net, NEW.total_employer_contrib, NEW.currency) THEN
                RAISE EXCEPTION 'Cannot modify POSTED payroll run. Run: %', OLD.run_number;
            END IF;
        END IF;
        
        -- Prevent changing status from PAID or CLOSED
        IF OLD.status IN ('PAID', 'CLOSED') AND NEW.status != OLD.status THEN
            RAISE EXCEPTION 'Cannot change status of % payroll run. Run: %', OLD.status, OLD.run_number;
        END IF;
    END IF;
    
    -- On DELETE: Prevent deletion of APPROVED/POSTED/PAID/CLOSED runs
    IF TG_OP = 'DELETE' THEN
        IF OLD.status IN ('APPROVED', 'POSTED', 'PAID', 'CLOSED') THEN
            RAISE EXCEPTION 'Cannot delete % payroll run. Run: %', OLD.status, OLD.run_number;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if exists, then create
DROP TRIGGER IF EXISTS payroll_run_immutability ON payroll_run;
CREATE TRIGGER payroll_run_immutability
    BEFORE UPDATE OR DELETE ON payroll_run
    FOR EACH ROW
    EXECUTE FUNCTION prevent_payroll_run_modification();

-- =====================================================
-- PART 6: PAYROLL RUN ITEM IMMUTABILITY
-- =====================================================

-- Trigger function to prevent modification of payroll run items for POSTED runs
CREATE OR REPLACE FUNCTION prevent_payroll_run_item_modification()
RETURNS TRIGGER AS $$
BEGIN
    -- On INSERT: Check if payroll run is already POSTED
    IF TG_OP = 'INSERT' THEN
        IF is_payroll_run_posted(NEW.payroll_run_id) THEN
            RAISE EXCEPTION 'Cannot add items to POSTED payroll run.';
        END IF;
    END IF;
    
    -- On UPDATE: Check if payroll run is POSTED
    IF TG_OP = 'UPDATE' THEN
        IF is_payroll_run_posted(NEW.payroll_run_id) THEN
            RAISE EXCEPTION 'Cannot modify items of POSTED payroll run.';
        END IF;
    END IF;
    
    -- On DELETE: Check if payroll run is POSTED
    IF TG_OP = 'DELETE' THEN
        IF is_payroll_run_posted(OLD.payroll_run_id) THEN
            RAISE EXCEPTION 'Cannot delete items from POSTED payroll run.';
        END IF;
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if exists, then create
DROP TRIGGER IF EXISTS payroll_run_item_immutability ON payroll_run_item;
CREATE TRIGGER payroll_run_item_immutability
    BEFORE INSERT OR UPDATE OR DELETE ON payroll_run_item
    FOR EACH ROW
    EXECUTE FUNCTION prevent_payroll_run_item_modification();

-- =====================================================
-- PART 7: AR ALLOCATION IMMUTABILITY
-- =====================================================

-- Trigger function to prevent modification of AR allocations (immutable after creation)
CREATE OR REPLACE FUNCTION prevent_ar_allocation_modification()
RETURNS TRIGGER AS $$
BEGIN
    -- AR allocations are immutable after creation
    IF TG_OP = 'UPDATE' THEN
        RAISE EXCEPTION 'AR allocations cannot be modified after creation. Create a reversing allocation instead.';
    END IF;
    
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'AR allocations cannot be deleted. Create a reversing allocation instead.';
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if exists, then create
DROP TRIGGER IF EXISTS ar_allocation_immutability ON ar_allocation;
CREATE TRIGGER ar_allocation_immutability
    BEFORE UPDATE OR DELETE ON ar_allocation
    FOR EACH ROW
    EXECUTE FUNCTION prevent_ar_allocation_modification();

-- =====================================================
-- PART 8: AP ALLOCATION IMMUTABILITY
-- =====================================================

-- Trigger function to prevent modification of AP allocations (immutable after creation)
CREATE OR REPLACE FUNCTION prevent_ap_allocation_modification()
RETURNS TRIGGER AS $$
BEGIN
    -- AP allocations are immutable after creation
    IF TG_OP = 'UPDATE' THEN
        RAISE EXCEPTION 'AP allocations cannot be modified after creation. Create a reversing allocation instead.';
    END IF;
    
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION 'AP allocations cannot be deleted. Create a reversing allocation instead.';
    END IF;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if exists, then create
DROP TRIGGER IF EXISTS ap_allocation_immutability ON ap_allocation;
CREATE TRIGGER ap_allocation_immutability
    BEFORE UPDATE OR DELETE ON ap_allocation
    FOR EACH ROW
    EXECUTE FUNCTION prevent_ap_allocation_modification();

-- =====================================================
-- PART 9: JOURNAL ENTRY BALANCE VALIDATION
-- =====================================================

-- Function to validate journal entry balance before posting
CREATE OR REPLACE FUNCTION validate_journal_entry_balance()
RETURNS TRIGGER AS $$
DECLARE
    total_debit NUMERIC(15, 2);
    total_credit NUMERIC(15, 2);
    tolerance NUMERIC(15, 2) := 0.01; -- Allow 0.01 tolerance for rounding
BEGIN
    -- Only validate when status changes to POSTED
    IF TG_OP = 'UPDATE' AND NEW.status = 'POSTED' AND OLD.status != 'POSTED' THEN
        -- Calculate totals
        SELECT COALESCE(SUM(debit_tc), 0), COALESCE(SUM(credit_tc), 0)
        INTO total_debit, total_credit
        FROM journal_line
        WHERE journal_entry_id = NEW.id;
        
        -- Check balance
        IF ABS(total_debit - total_credit) > tolerance THEN
            RAISE EXCEPTION 'Journal entry must balance. Debits: %, Credits: %, Difference: %', 
                total_debit, total_credit, ABS(total_debit - total_credit);
        END IF;
        
        -- Check that there are lines
        IF total_debit = 0 AND total_credit = 0 THEN
            RAISE EXCEPTION 'Journal entry must have at least one line.';
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if exists, then create
DROP TRIGGER IF EXISTS journal_entry_balance_validation ON journal_entry;
CREATE TRIGGER journal_entry_balance_validation
    BEFORE UPDATE ON journal_entry
    FOR EACH ROW
    EXECUTE FUNCTION validate_journal_entry_balance();

-- =====================================================
-- PART 10: PERIOD DATE VALIDATION
-- =====================================================

-- Check constraint for period dates (start < end)
ALTER TABLE accounting_period 
    DROP CONSTRAINT IF EXISTS chk_period_dates;
ALTER TABLE accounting_period 
    ADD CONSTRAINT chk_period_dates CHECK (start_date < end_date);

-- Check constraint for payroll period dates
ALTER TABLE payroll_run 
    DROP CONSTRAINT IF EXISTS chk_payroll_period_dates;
ALTER TABLE payroll_run 
    ADD CONSTRAINT chk_payroll_period_dates CHECK (pay_period_start < pay_period_end);

-- =====================================================
-- PART 11: STATUS TRANSITION VALIDATION
-- =====================================================

-- Function to validate journal entry status transitions
CREATE OR REPLACE FUNCTION validate_journal_entry_status_transition()
RETURNS TRIGGER AS $$
BEGIN
    -- Valid transitions:
    -- DRAFT -> POSTED
    -- DRAFT -> (delete)
    -- POSTED -> REVERSED (via reversal entry)
    
    IF TG_OP = 'UPDATE' THEN
        -- DRAFT can go to POSTED or stay DRAFT
        IF OLD.status = 'DRAFT' AND NEW.status NOT IN ('DRAFT', 'POSTED') THEN
            RAISE EXCEPTION 'Invalid status transition from DRAFT to %. Entry: %', NEW.status, OLD.entry_number;
        END IF;
        
        -- POSTED can only go to REVERSED
        IF OLD.status = 'POSTED' AND NEW.status NOT IN ('POSTED', 'REVERSED') THEN
            RAISE EXCEPTION 'Invalid status transition from POSTED to %. Entry: %', NEW.status, OLD.entry_number;
        END IF;
        
        -- REVERSED cannot change
        IF OLD.status = 'REVERSED' AND NEW.status != 'REVERSED' THEN
            RAISE EXCEPTION 'Invalid status transition from REVERSED to %. Entry: %', NEW.status, OLD.entry_number;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if exists, then create
DROP TRIGGER IF EXISTS journal_entry_status_validation ON journal_entry;
CREATE TRIGGER journal_entry_status_validation
    BEFORE UPDATE ON journal_entry
    FOR EACH ROW
    EXECUTE FUNCTION validate_journal_entry_status_transition();

-- Function to validate payroll run status transitions
CREATE OR REPLACE FUNCTION validate_payroll_run_status_transition()
RETURNS TRIGGER AS $$
BEGIN
    -- Valid transitions:
    -- DRAFT -> CALCULATED
    -- CALCULATED -> APPROVED or DRAFT
    -- APPROVED -> POSTED or CALCULATED
    -- POSTED -> PAID
    -- PAID -> CLOSED
    
    IF TG_OP = 'UPDATE' THEN
        -- DRAFT can go to CALCULATED
        IF OLD.status = 'DRAFT' AND NEW.status NOT IN ('DRAFT', 'CALCULATED') THEN
            RAISE EXCEPTION 'Invalid status transition from DRAFT to %. Run: %', NEW.status, OLD.run_number;
        END IF;
        
        -- CALCULATED can go to APPROVED or back to DRAFT
        IF OLD.status = 'CALCULATED' AND NEW.status NOT IN ('CALCULATED', 'APPROVED', 'DRAFT') THEN
            RAISE EXCEPTION 'Invalid status transition from CALCULATED to %. Run: %', NEW.status, OLD.run_number;
        END IF;
        
        -- APPROVED can go to POSTED or back to CALCULATED
        IF OLD.status = 'APPROVED' AND NEW.status NOT IN ('APPROVED', 'POSTED', 'CALCULATED') THEN
            RAISE EXCEPTION 'Invalid status transition from APPROVED to %. Run: %', NEW.status, OLD.run_number;
        END IF;
        
        -- POSTED can go to PAID
        IF OLD.status = 'POSTED' AND NEW.status NOT IN ('POSTED', 'PAID') THEN
            RAISE EXCEPTION 'Invalid status transition from POSTED to %. Run: %', NEW.status, OLD.run_number;
        END IF;
        
        -- PAID can go to CLOSED
        IF OLD.status = 'PAID' AND NEW.status NOT IN ('PAID', 'CLOSED') THEN
            RAISE EXCEPTION 'Invalid status transition from PAID to %. Run: %', NEW.status, OLD.run_number;
        END IF;
        
        -- CLOSED cannot change
        IF OLD.status = 'CLOSED' AND NEW.status != 'CLOSED' THEN
            RAISE EXCEPTION 'Invalid status transition from CLOSED to %. Run: %', NEW.status, OLD.run_number;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Drop existing trigger if exists, then create
DROP TRIGGER IF EXISTS payroll_run_status_validation ON payroll_run;
CREATE TRIGGER payroll_run_status_validation
    BEFORE UPDATE ON payroll_run
    FOR EACH ROW
    EXECUTE FUNCTION validate_payroll_run_status_transition();

-- =====================================================
-- PART 12: VERIFICATION QUERIES
-- =====================================================

-- Run these after applying to verify triggers are active:

-- List all triggers:
-- SELECT trigger_name, event_manipulation, event_object_table 
-- FROM information_schema.triggers 
-- WHERE trigger_schema = 'public'
-- ORDER BY event_object_table;

-- Test immutability (should fail):
-- UPDATE journal_entry SET description = 'test' WHERE status = 'POSTED' LIMIT 1;
-- Expected: ERROR: Cannot modify POSTED journal entry

-- Test balance validation (should fail if unbalanced):
-- UPDATE journal_entry SET status = 'POSTED' WHERE status = 'DRAFT' AND id = '<unbalanced_entry_id>';
-- Expected: ERROR: Journal entry must balance

-- =====================================================
-- END OF IMMUTABILITY CONSTRAINTS
-- =====================================================
