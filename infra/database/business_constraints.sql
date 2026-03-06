-- =====================================================
-- TrueVow Financial Management - Business Constraints
-- =====================================================
-- Purpose: Additional business constraints for data integrity
-- Priority: P2 - HIGH (Complete within 1 week)
-- Date: 2026-03-02
-- =====================================================
--
-- INSTRUCTIONS:
-- 1. Run this script in Supabase SQL Editor or via psql
-- 2. The script is IDEMPOTENT - uses DROP IF EXISTS
-- 3. Run AFTER rls_policies.sql and immutability_constraints.sql
--
-- WHAT THIS ADDS:
-- - Unique constraints on business keys
-- - Check constraints for data integrity
-- - Additional validation rules
-- =====================================================

-- =====================================================
-- PART 1: UNIQUE CONSTRAINTS ON BUSINESS KEYS
-- =====================================================

-- Journal Entry: Unique (book_id, entry_number) - already exists as UNIQUE on entry_number
-- But we should ensure entry_number is unique per book
ALTER TABLE journal_entry 
    DROP CONSTRAINT IF EXISTS uq_journal_entry_book_entry_number;
ALTER TABLE journal_entry 
    ADD CONSTRAINT uq_journal_entry_book_entry_number UNIQUE (book_id, entry_number);

-- GL Account: Unique (book_id, account_code)
ALTER TABLE gl_account 
    DROP CONSTRAINT IF EXISTS uq_gl_account_book_code;
ALTER TABLE gl_account 
    ADD CONSTRAINT uq_gl_account_book_code UNIQUE (book_id, account_code);

-- Legal Entity: Unique code (already exists)
-- Book: Unique name per legal_entity
ALTER TABLE book 
    DROP CONSTRAINT IF EXISTS uq_book_legal_entity_name;
ALTER TABLE book 
    ADD CONSTRAINT uq_book_legal_entity_name UNIQUE (legal_entity_id, name);

-- Dimension: Unique code (already exists)
-- Dimension Value: Unique (dimension_code, value_code)
ALTER TABLE dimension_value 
    DROP CONSTRAINT IF EXISTS uq_dimension_value_code;
ALTER TABLE dimension_value 
    ADD CONSTRAINT uq_dimension_value_code UNIQUE (dimension_code, value_code);

-- Accounting Period: Unique (book_id, period_name)
ALTER TABLE accounting_period 
    DROP CONSTRAINT IF EXISTS uq_accounting_period_book_name;
ALTER TABLE accounting_period 
    ADD CONSTRAINT uq_accounting_period_book_name UNIQUE (book_id, period_name);

-- AR Customer: Unique external_customer_id (already exists)
-- AR Customer: Unique customer_code per legal_entity
ALTER TABLE ar_customer 
    DROP CONSTRAINT IF EXISTS uq_ar_customer_legal_entity_code;
ALTER TABLE ar_customer 
    ADD CONSTRAINT uq_ar_customer_legal_entity_code UNIQUE (legal_entity_id, customer_code);

-- AR Invoice: Unique invoice_number (already exists)
-- AR Invoice: Unique external_invoice_id (already exists)

-- AR Payment: Unique external_payment_id (already exists)

-- AP Vendor: Unique vendor_code (already exists)

-- AP Bill: Unique bill_number (already exists)

-- AP Payment: Unique payment_number (already exists)

-- Pay Group: Unique group_code (already exists)

-- HR Employee: Unique employee_code (already exists)

-- Payroll Run: Unique run_number (already exists)

-- Payroll Payment Batch: Unique batch_number (already exists)

-- Affiliate Partner: Unique partner_code (already exists)

-- Affiliate Payout: Unique payout_number (already exists)

-- Treasury Bank Account: Unique account_number per legal_entity (if provided)
-- Note: Partial unique indexes require CREATE INDEX, not ALTER TABLE
DROP INDEX IF EXISTS uq_treasury_bank_account_number;
CREATE UNIQUE INDEX uq_treasury_bank_account_number 
    ON treasury_bank_account (legal_entity_id, account_number) 
    WHERE account_number IS NOT NULL;

-- =====================================================
-- PART 2: CHECK CONSTRAINTS FOR DATA INTEGRITY
-- =====================================================

-- Journal Line: Debit or Credit, not both (already exists)
-- Additional: At least one must be positive
ALTER TABLE journal_line 
    DROP CONSTRAINT IF EXISTS chk_journal_line_amounts;
ALTER TABLE journal_line 
    ADD CONSTRAINT chk_journal_line_amounts CHECK (
        (debit_tc > 0 AND credit_tc = 0) OR 
        (debit_tc = 0 AND credit_tc > 0) OR
        (debit_fc > 0 AND credit_fc = 0) OR
        (debit_fc = 0 AND credit_fc > 0)
    );

-- Journal Line: Non-negative amounts
ALTER TABLE journal_line 
    DROP CONSTRAINT IF EXISTS chk_journal_line_non_negative;
ALTER TABLE journal_line 
    ADD CONSTRAINT chk_journal_line_non_negative CHECK (
        debit_tc >= 0 AND credit_tc >= 0 AND
        debit_fc >= 0 AND credit_fc >= 0
    );

-- Accounting Period: Valid date range (already added in immutability_constraints.sql)
-- payroll_run: Valid date range (already added in immutability_constraints.sql)

-- Payroll Run: Non-negative totals
ALTER TABLE payroll_run 
    DROP CONSTRAINT IF EXISTS chk_payroll_run_totals;
ALTER TABLE payroll_run 
    ADD CONSTRAINT chk_payroll_run_totals CHECK (
        total_gross >= 0 AND
        total_deductions >= 0 AND
        total_net >= 0 AND
        total_employer_contrib >= 0
    );

-- Payroll Run Item: Non-negative amounts
ALTER TABLE payroll_run_item 
    DROP CONSTRAINT IF EXISTS chk_payroll_run_item_amounts;
ALTER TABLE payroll_run_item 
    ADD CONSTRAINT chk_payroll_run_item_amounts CHECK (
        gross_pay >= 0 AND
        total_deductions >= 0 AND
        net_pay >= 0 AND
        employer_contributions >= 0
    );

-- Payroll Run Component Line: Non-negative amount
ALTER TABLE payroll_run_component_line 
    DROP CONSTRAINT IF EXISTS chk_payroll_run_component_line_amount;
ALTER TABLE payroll_run_component_line 
    ADD CONSTRAINT chk_payroll_run_component_line_amount CHECK (amount >= 0);

-- AR Invoice: Non-negative amounts
ALTER TABLE ar_invoice 
    DROP CONSTRAINT IF EXISTS chk_ar_invoice_amounts;
ALTER TABLE ar_invoice 
    ADD CONSTRAINT chk_ar_invoice_amounts CHECK (
        total_amount >= 0 AND
        paid_amount >= 0 AND
        outstanding_amount >= 0
    );

-- AR Invoice Line: Non-negative amounts
ALTER TABLE ar_invoice_line 
    DROP CONSTRAINT IF EXISTS chk_ar_invoice_line_amounts;
ALTER TABLE ar_invoice_line 
    ADD CONSTRAINT chk_ar_invoice_line_amounts CHECK (
        quantity >= 0 AND
        unit_price >= 0 AND
        line_amount >= 0
    );

-- AR Payment: Non-negative amount
ALTER TABLE ar_payment 
    DROP CONSTRAINT IF EXISTS chk_ar_payment_amount;
ALTER TABLE ar_payment 
    ADD CONSTRAINT chk_ar_payment_amount CHECK (payment_amount >= 0);

-- AR Allocation: Non-negative amount
ALTER TABLE ar_allocation 
    DROP CONSTRAINT IF EXISTS chk_ar_allocation_amount;
ALTER TABLE ar_allocation 
    ADD CONSTRAINT chk_ar_allocation_amount CHECK (allocated_amount >= 0);

-- AP Bill: Non-negative amounts
ALTER TABLE ap_bill 
    DROP CONSTRAINT IF EXISTS chk_ap_bill_amounts;
ALTER TABLE ap_bill 
    ADD CONSTRAINT chk_ap_bill_amounts CHECK (
        total_amount >= 0 AND
        paid_amount >= 0 AND
        outstanding_amount >= 0 AND
        withholding_amount >= 0
    );

-- AP Bill Line: Non-negative amounts
ALTER TABLE ap_bill_line 
    DROP CONSTRAINT IF EXISTS chk_ap_bill_line_amounts;
ALTER TABLE ap_bill_line 
    ADD CONSTRAINT chk_ap_bill_line_amounts CHECK (
        quantity >= 0 AND
        unit_price >= 0 AND
        line_amount >= 0
    );

-- AP Payment: Non-negative amount
ALTER TABLE ap_payment 
    DROP CONSTRAINT IF EXISTS chk_ap_payment_amount;
ALTER TABLE ap_payment 
    ADD CONSTRAINT chk_ap_payment_amount CHECK (payment_amount >= 0);

-- AP Allocation: Non-negative amount
ALTER TABLE ap_allocation 
    DROP CONSTRAINT IF EXISTS chk_ap_allocation_amount;
ALTER TABLE ap_allocation 
    ADD CONSTRAINT chk_ap_allocation_amount CHECK (allocated_amount >= 0);

-- Treasury Bank Transaction: Non-negative balance_after (if provided)
ALTER TABLE treasury_bank_transaction 
    DROP CONSTRAINT IF EXISTS chk_treasury_bank_transaction_balance;
ALTER TABLE treasury_bank_transaction 
    ADD CONSTRAINT chk_treasury_bank_transaction_balance CHECK (
        balance_after IS NULL OR balance_after >= 0
    );

-- Treasury Transfer: Non-negative amount
ALTER TABLE treasury_transfer 
    DROP CONSTRAINT IF EXISTS chk_treasury_transfer_amount;
ALTER TABLE treasury_transfer 
    ADD CONSTRAINT chk_treasury_transfer_amount CHECK (amount >= 0);

-- Treasury FX Conversion: Non-negative amounts
ALTER TABLE treasury_fx_conversion 
    DROP CONSTRAINT IF EXISTS chk_treasury_fx_conversion_amounts;
ALTER TABLE treasury_fx_conversion 
    ADD CONSTRAINT chk_treasury_fx_conversion_amounts CHECK (
        from_amount >= 0 AND
        to_amount >= 0 AND
        fx_rate > 0
    );

-- Treasury Settlement: Non-negative amount
ALTER TABLE treasury_settlement 
    DROP CONSTRAINT IF EXISTS chk_treasury_settlement_amount;
ALTER TABLE treasury_settlement 
    ADD CONSTRAINT chk_treasury_settlement_amount CHECK (amount >= 0);

-- Intercompany Transfer: Non-negative amount
ALTER TABLE intercompany_transfer 
    DROP CONSTRAINT IF EXISTS chk_intercompany_transfer_amount;
ALTER TABLE intercompany_transfer 
    ADD CONSTRAINT chk_intercompany_transfer_amount CHECK (amount >= 0);

-- Royalty Agreement: Non-negative rate and amount
ALTER TABLE royalty_agreement 
    DROP CONSTRAINT IF EXISTS chk_royalty_agreement_values;
ALTER TABLE royalty_agreement 
    ADD CONSTRAINT chk_royalty_agreement_values CHECK (
        (rate IS NULL OR rate >= 0) AND
        (amount IS NULL OR amount >= 0)
    );

-- Royalty Calculation: Non-negative amounts
ALTER TABLE royalty_calculation 
    DROP CONSTRAINT IF EXISTS chk_royalty_calculation_amounts;
ALTER TABLE royalty_calculation 
    ADD CONSTRAINT chk_royalty_calculation_amounts CHECK (
        basis_amount >= 0 AND
        royalty_amount >= 0
    );

-- Intercompany Balance: Non-negative balance (could be negative for liabilities)
-- No constraint - balances can be negative

-- Commission Rule: Non-negative rate and amount
ALTER TABLE commission_rule 
    DROP CONSTRAINT IF EXISTS chk_commission_rule_values;
ALTER TABLE commission_rule 
    ADD CONSTRAINT chk_commission_rule_values CHECK (
        (rate IS NULL OR rate >= 0) AND
        (amount IS NULL OR amount >= 0)
    );

-- Commission Ledger: Non-negative amounts
ALTER TABLE commission_ledger 
    DROP CONSTRAINT IF EXISTS chk_commission_ledger_amounts;
ALTER TABLE commission_ledger 
    ADD CONSTRAINT chk_commission_ledger_amounts CHECK (
        basis_amount >= 0 AND
        commission_amount >= 0
    );

-- Bonus Result: Non-negative amount
ALTER TABLE bonus_result 
    DROP CONSTRAINT IF EXISTS chk_bonus_result_amount;
ALTER TABLE bonus_result 
    ADD CONSTRAINT chk_bonus_result_amount CHECK (bonus_amount >= 0);

-- Affiliate Earning Event: Non-negative amounts
ALTER TABLE affiliate_earning_event 
    DROP CONSTRAINT IF EXISTS chk_affiliate_earning_event_amounts;
ALTER TABLE affiliate_earning_event 
    ADD CONSTRAINT chk_affiliate_earning_event_amounts CHECK (
        basis_amount >= 0 AND
        commission_amount >= 0
    );

-- Affiliate Payout: Non-negative amount
ALTER TABLE affiliate_payout 
    DROP CONSTRAINT IF EXISTS chk_affiliate_payout_amount;
ALTER TABLE affiliate_payout 
    ADD CONSTRAINT chk_affiliate_payout_amount CHECK (payout_amount >= 0);

-- Pay Component Assignment: Non-negative amount and rate
ALTER TABLE pay_component_assignment 
    DROP CONSTRAINT IF EXISTS chk_pay_component_assignment_values;
ALTER TABLE pay_component_assignment 
    ADD CONSTRAINT chk_pay_component_assignment_values CHECK (
        (amount IS NULL OR amount >= 0) AND
        (rate IS NULL OR rate >= 0)
    );

-- Statutory Contribution Rule: Non-negative rates
ALTER TABLE stat_contribution_rule 
    DROP CONSTRAINT IF EXISTS chk_stat_contribution_rule_rates;
ALTER TABLE stat_contribution_rule 
    ADD CONSTRAINT chk_stat_contribution_rule_rates CHECK (
        employee_rate >= 0 AND
        employer_rate >= 0 AND
        (salary_cap IS NULL OR salary_cap >= 0)
    );

-- Tax Withholding Table: Non-negative values
ALTER TABLE tax_withholding_table 
    DROP CONSTRAINT IF EXISTS chk_tax_withholding_table_values;
ALTER TABLE tax_withholding_table 
    ADD CONSTRAINT chk_tax_withholding_table_values CHECK (
        income_from >= 0 AND
        (income_to IS NULL OR income_to >= income_from) AND
        tax_rate >= 0 AND
        tax_rate <= 100 AND
        fixed_amount >= 0
    );

-- AP Withholding Profile: Non-negative rate
ALTER TABLE ap_withholding_profile 
    DROP CONSTRAINT IF EXISTS chk_ap_withholding_profile_rate;
ALTER TABLE ap_withholding_profile 
    ADD CONSTRAINT chk_ap_withholding_profile_rate CHECK (
        withholding_rate >= 0 AND
        withholding_rate <= 100
    );

-- Payroll Liability Balance: Non-negative balance (could be negative for overpayments)
-- No constraint - liability balances can be negative

-- =====================================================
-- PART 3: CURRENCY VALIDATION
-- =====================================================

-- Add check constraint for valid ISO 4217 currency codes (3 characters)
-- Note: This is a basic check; full validation would require a currency lookup table

-- Create a function to validate currency code
CREATE OR REPLACE FUNCTION is_valid_currency(p_currency VARCHAR)
RETURNS BOOLEAN AS $$
BEGIN
    -- Basic check: 3 uppercase letters
    RETURN p_currency ~ '^[A-Z]{3}$';
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Apply to all currency columns
ALTER TABLE legal_entity 
    DROP CONSTRAINT IF EXISTS chk_legal_entity_currency;
ALTER TABLE legal_entity 
    ADD CONSTRAINT chk_legal_entity_currency CHECK (is_valid_currency(functional_currency));

ALTER TABLE journal_line 
    DROP CONSTRAINT IF EXISTS chk_journal_line_currency;
ALTER TABLE journal_line 
    ADD CONSTRAINT chk_journal_line_currency CHECK (is_valid_currency(currency));

ALTER TABLE ar_invoice 
    DROP CONSTRAINT IF EXISTS chk_ar_invoice_currency;
ALTER TABLE ar_invoice 
    ADD CONSTRAINT chk_ar_invoice_currency CHECK (is_valid_currency(currency));

ALTER TABLE ar_payment 
    DROP CONSTRAINT IF EXISTS chk_ar_payment_currency;
ALTER TABLE ar_payment 
    ADD CONSTRAINT chk_ar_payment_currency CHECK (is_valid_currency(currency));

ALTER TABLE ap_bill 
    DROP CONSTRAINT IF EXISTS chk_ap_bill_currency;
ALTER TABLE ap_bill 
    ADD CONSTRAINT chk_ap_bill_currency CHECK (is_valid_currency(currency));

ALTER TABLE ap_payment 
    DROP CONSTRAINT IF EXISTS chk_ap_payment_currency;
ALTER TABLE ap_payment 
    ADD CONSTRAINT chk_ap_payment_currency CHECK (is_valid_currency(currency));

ALTER TABLE treasury_bank_account 
    DROP CONSTRAINT IF EXISTS chk_treasury_bank_account_currency;
ALTER TABLE treasury_bank_account 
    ADD CONSTRAINT chk_treasury_bank_account_currency CHECK (is_valid_currency(currency));

ALTER TABLE treasury_bank_transaction 
    DROP CONSTRAINT IF EXISTS chk_treasury_bank_transaction_currency;
ALTER TABLE treasury_bank_transaction 
    ADD CONSTRAINT chk_treasury_bank_transaction_currency CHECK (is_valid_currency(currency));

ALTER TABLE treasury_transfer 
    DROP CONSTRAINT IF EXISTS chk_treasury_transfer_currency;
ALTER TABLE treasury_transfer 
    ADD CONSTRAINT chk_treasury_transfer_currency CHECK (is_valid_currency(currency));

ALTER TABLE treasury_fx_conversion 
    DROP CONSTRAINT IF EXISTS chk_treasury_fx_conversion_currency;
ALTER TABLE treasury_fx_conversion 
    ADD CONSTRAINT chk_treasury_fx_conversion_currency CHECK (
        is_valid_currency(from_currency) AND is_valid_currency(to_currency)
    );

ALTER TABLE treasury_settlement 
    DROP CONSTRAINT IF EXISTS chk_treasury_settlement_currency;
ALTER TABLE treasury_settlement 
    ADD CONSTRAINT chk_treasury_settlement_currency CHECK (is_valid_currency(currency));

ALTER TABLE payroll_run 
    DROP CONSTRAINT IF EXISTS chk_payroll_run_currency;
ALTER TABLE payroll_run 
    ADD CONSTRAINT chk_payroll_run_currency CHECK (is_valid_currency(currency));

ALTER TABLE pay_group 
    DROP CONSTRAINT IF EXISTS chk_pay_group_currency;
ALTER TABLE pay_group 
    ADD CONSTRAINT chk_pay_group_currency CHECK (is_valid_currency(payroll_currency));

ALTER TABLE hr_employee 
    DROP CONSTRAINT IF EXISTS chk_hr_employee_currency;
ALTER TABLE hr_employee 
    ADD CONSTRAINT chk_hr_employee_currency CHECK (is_valid_currency(currency));

-- =====================================================
-- PART 4: DATE VALIDATION
-- =====================================================

-- Revenue Schedule: service_start < service_end
ALTER TABLE revenue_schedule 
    DROP CONSTRAINT IF EXISTS chk_revenue_schedule_dates;
ALTER TABLE revenue_schedule 
    ADD CONSTRAINT chk_revenue_schedule_dates CHECK (service_start < service_end);

-- Revenue Schedule Period: period_start < period_end
ALTER TABLE revenue_schedule_period 
    DROP CONSTRAINT IF EXISTS chk_revenue_schedule_period_dates;
ALTER TABLE revenue_schedule_period 
    ADD CONSTRAINT chk_revenue_schedule_period_dates CHECK (period_start < period_end);

-- AR Invoice Line: service_start < service_end (if provided)
ALTER TABLE ar_invoice_line 
    DROP CONSTRAINT IF EXISTS chk_ar_invoice_line_dates;
ALTER TABLE ar_invoice_line 
    ADD CONSTRAINT chk_ar_invoice_line_dates CHECK (
        service_start IS NULL OR 
        service_end IS NULL OR 
        service_start <= service_end
    );

-- Royalty Agreement: effective_from < effective_to (if provided)
ALTER TABLE royalty_agreement 
    DROP CONSTRAINT IF EXISTS chk_royalty_agreement_dates;
ALTER TABLE royalty_agreement 
    ADD CONSTRAINT chk_royalty_agreement_dates CHECK (
        effective_to IS NULL OR effective_from < effective_to
    );

-- Affiliate Agreement: effective_from < effective_to (if provided)
ALTER TABLE affiliate_agreement 
    DROP CONSTRAINT IF EXISTS chk_affiliate_agreement_dates;
ALTER TABLE affiliate_agreement 
    ADD CONSTRAINT chk_affiliate_agreement_dates CHECK (
        effective_to IS NULL OR effective_from < effective_to
    );

-- Statutory Contribution Rule: effective_from < effective_to (if provided)
ALTER TABLE stat_contribution_rule 
    DROP CONSTRAINT IF EXISTS chk_stat_contribution_rule_dates;
ALTER TABLE stat_contribution_rule 
    ADD CONSTRAINT chk_stat_contribution_rule_dates CHECK (
        effective_to IS NULL OR effective_from < effective_to
    );

-- Tax Withholding Table: effective_from < effective_to (if provided)
ALTER TABLE tax_withholding_table 
    DROP CONSTRAINT IF EXISTS chk_tax_withholding_table_dates;
ALTER TABLE tax_withholding_table 
    ADD CONSTRAINT chk_tax_withholding_table_dates CHECK (
        effective_to IS NULL OR effective_from < effective_to
    );

-- Pay Component Assignment: effective_from < effective_to (if provided)
ALTER TABLE pay_component_assignment 
    DROP CONSTRAINT IF EXISTS chk_pay_component_assignment_dates;
ALTER TABLE pay_component_assignment 
    ADD CONSTRAINT chk_pay_component_assignment_dates CHECK (
        effective_to IS NULL OR effective_from < effective_to
    );

-- HR Employee: hire_date < termination_date (if provided)
ALTER TABLE hr_employee 
    DROP CONSTRAINT IF EXISTS chk_hr_employee_dates;
ALTER TABLE hr_employee 
    ADD CONSTRAINT chk_hr_employee_dates CHECK (
        termination_date IS NULL OR hire_date IS NULL OR hire_date <= termination_date
    );

-- =====================================================
-- PART 5: BUSINESS LOGIC CONSTRAINTS
-- =====================================================

-- Intercompany Transfer: from_entity_id != to_entity_id
ALTER TABLE intercompany_transfer 
    DROP CONSTRAINT IF EXISTS chk_intercompany_transfer_entities;
ALTER TABLE intercompany_transfer 
    ADD CONSTRAINT chk_intercompany_transfer_entities CHECK (from_entity_id != to_entity_id);

-- Royalty Agreement: from_entity_id != to_entity_id
ALTER TABLE royalty_agreement 
    DROP CONSTRAINT IF EXISTS chk_royalty_agreement_entities;
ALTER TABLE royalty_agreement 
    ADD CONSTRAINT chk_royalty_agreement_entities CHECK (from_entity_id != to_entity_id);

-- Intercompany Balance: from_entity_id != to_entity_id
ALTER TABLE intercompany_balance 
    DROP CONSTRAINT IF EXISTS chk_intercompany_balance_entities;
ALTER TABLE intercompany_balance 
    ADD CONSTRAINT chk_intercompany_balance_entities CHECK (from_entity_id != to_entity_id);

-- FX Conversion: from_currency != to_currency
ALTER TABLE treasury_fx_conversion 
    DROP CONSTRAINT IF EXISTS chk_treasury_fx_conversion_currencies;
ALTER TABLE treasury_fx_conversion 
    ADD CONSTRAINT chk_treasury_fx_conversion_currencies CHECK (from_currency != to_currency);

-- =====================================================
-- PART 6: VERIFICATION QUERIES
-- =====================================================

-- Run these after applying to verify constraints are active:

-- List all check constraints:
-- SELECT conname, conrelid::regclass, pg_get_constraintdef(oid)
-- FROM pg_constraint
-- WHERE contype = 'c' AND connamespace = 'public'::regnamespace
-- ORDER BY conrelid::regclass, conname;

-- List all unique constraints:
-- SELECT conname, conrelid::regclass, pg_get_constraintdef(oid)
-- FROM pg_constraint
-- WHERE contype = 'u' AND connamespace = 'public'::regnamespace
-- ORDER BY conrelid::regclass, conname;

-- Test constraint violation (should fail):
-- INSERT INTO journal_line (id, journal_entry_id, book_id, gl_account_id, line_number, debit_tc, credit_tc, currency)
-- VALUES (uuid_generate_v4(), 'some-id', 'some-id', 'some-id', 1, 100, 100, 'USD');
-- Expected: ERROR - violates check constraint (both debit and credit positive)

-- =====================================================
-- END OF BUSINESS CONSTRAINTS
-- =====================================================
