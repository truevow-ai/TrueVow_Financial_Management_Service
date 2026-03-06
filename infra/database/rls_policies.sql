-- =====================================================
-- TrueVow Financial Management - RLS Policies
-- =====================================================
-- Purpose: Row-Level Security for multi-tenant isolation
-- Priority: P0 - CRITICAL (Block all other work until complete)
-- Date: 2026-03-02
-- =====================================================
-- 
-- INSTRUCTIONS:
-- 1. Run this script in Supabase SQL Editor or via psql
-- 2. The script is IDEMPOTENT - safe to run multiple times
-- 3. After running, verify with: SELECT * FROM pg_policies;
--
-- TENANT ISOLATION METHOD:
-- - Uses app.current_tenant_id session variable
-- - Set via: SET app.current_tenant_id = '<legal_entity_uuid>';
-- - Or in connection string: ?options=-c%20app.current_tenant_id%3D<uuid>
-- =====================================================

-- =====================================================
-- PART 1: ENABLE RLS ON ALL TABLES
-- =====================================================

-- Core Tables
ALTER TABLE legal_entity ENABLE ROW LEVEL SECURITY;
ALTER TABLE book ENABLE ROW LEVEL SECURITY;
ALTER TABLE dimension ENABLE ROW LEVEL SECURITY;
ALTER TABLE dimension_value ENABLE ROW LEVEL SECURITY;
ALTER TABLE gl_account ENABLE ROW LEVEL SECURITY;
ALTER TABLE gl_account_mapping ENABLE ROW LEVEL SECURITY;
ALTER TABLE accounting_period ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_entry ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_line ENABLE ROW LEVEL SECURITY;
ALTER TABLE journal_line_dimension ENABLE ROW LEVEL SECURITY;

-- AR Tables
ALTER TABLE ar_customer ENABLE ROW LEVEL SECURITY;
ALTER TABLE ar_invoice ENABLE ROW LEVEL SECURITY;
ALTER TABLE ar_invoice_line ENABLE ROW LEVEL SECURITY;
ALTER TABLE ar_payment ENABLE ROW LEVEL SECURITY;
ALTER TABLE ar_allocation ENABLE ROW LEVEL SECURITY;
ALTER TABLE revenue_schedule ENABLE ROW LEVEL SECURITY;
ALTER TABLE revenue_schedule_period ENABLE ROW LEVEL SECURITY;

-- Treasury Tables
ALTER TABLE treasury_bank_account ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury_bank_transaction ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury_transfer ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury_fx_conversion ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury_settlement ENABLE ROW LEVEL SECURITY;
ALTER TABLE treasury_sync_cursor ENABLE ROW LEVEL SECURITY;
ALTER TABLE reconciliation_session ENABLE ROW LEVEL SECURITY;
ALTER TABLE reconciliation_match ENABLE ROW LEVEL SECURITY;

-- Payroll Tables
ALTER TABLE pay_group ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr_employee ENABLE ROW LEVEL SECURITY;
ALTER TABLE hr_employee_bank ENABLE ROW LEVEL SECURITY;
ALTER TABLE pay_component_definition ENABLE ROW LEVEL SECURITY;
ALTER TABLE pay_component_assignment ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll_run ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll_run_item ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll_run_component_line ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll_payment_batch ENABLE ROW LEVEL SECURITY;
ALTER TABLE commission_plan ENABLE ROW LEVEL SECURITY;
ALTER TABLE commission_rule ENABLE ROW LEVEL SECURITY;
ALTER TABLE commission_ledger ENABLE ROW LEVEL SECURITY;
ALTER TABLE bonus_plan ENABLE ROW LEVEL SECURITY;
ALTER TABLE bonus_result ENABLE ROW LEVEL SECURITY;
ALTER TABLE pay_rule_set ENABLE ROW LEVEL SECURITY;
ALTER TABLE pay_rule ENABLE ROW LEVEL SECURITY;
ALTER TABLE stat_contribution_rule ENABLE ROW LEVEL SECURITY;
ALTER TABLE tax_withholding_table ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll_export_template ENABLE ROW LEVEL SECURITY;
ALTER TABLE payroll_liability_balance ENABLE ROW LEVEL SECURITY;

-- Intercompany Tables
ALTER TABLE intercompany_transfer ENABLE ROW LEVEL SECURITY;
ALTER TABLE royalty_agreement ENABLE ROW LEVEL SECURITY;
ALTER TABLE royalty_calculation ENABLE ROW LEVEL SECURITY;
ALTER TABLE intercompany_balance ENABLE ROW LEVEL SECURITY;

-- External Sync Tables
ALTER TABLE external_sync_cursor ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_object_map ENABLE ROW LEVEL SECURITY;

-- AP Tables
ALTER TABLE ap_withholding_profile ENABLE ROW LEVEL SECURITY;
ALTER TABLE ap_vendor ENABLE ROW LEVEL SECURITY;
ALTER TABLE ap_bill ENABLE ROW LEVEL SECURITY;
ALTER TABLE ap_bill_line ENABLE ROW LEVEL SECURITY;
ALTER TABLE ap_payment ENABLE ROW LEVEL SECURITY;
ALTER TABLE ap_allocation ENABLE ROW LEVEL SECURITY;

-- Affiliate Tables
ALTER TABLE affiliate_partner ENABLE ROW LEVEL SECURITY;
ALTER TABLE affiliate_agreement ENABLE ROW LEVEL SECURITY;
ALTER TABLE affiliate_earning_event ENABLE ROW LEVEL SECURITY;
ALTER TABLE affiliate_payout ENABLE ROW LEVEL SECURITY;

-- Audit Tables (special handling - no RLS, service role only)
-- audit_log and idempotency_keys are NOT tenant-scoped

-- =====================================================
-- PART 2: CREATE HELPER FUNCTION FOR TENANT ID
-- =====================================================

CREATE OR REPLACE FUNCTION app_current_tenant_id()
RETURNS UUID AS $$
BEGIN
    RETURN NULLIF(current_setting('app.current_tenant_id', TRUE), '')::UUID;
EXCEPTION WHEN OTHERS THEN
    RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- =====================================================
-- PART 3: RLS POLICIES - CORE TABLES
-- =====================================================

-- legal_entity: Root entity, direct tenant filter
DROP POLICY IF EXISTS "tenant_isolation" ON legal_entity;
CREATE POLICY "tenant_isolation" ON legal_entity
    FOR ALL
    USING (id = app_current_tenant_id());

-- book: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON book;
CREATE POLICY "tenant_isolation" ON book
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- dimension: Global per tenant (if tenant-scoped) or truly global
-- For now, assuming dimensions are shared across tenant's entities
DROP POLICY IF EXISTS "tenant_isolation" ON dimension;
CREATE POLICY "tenant_isolation" ON dimension
    FOR ALL
    USING (
        -- Allow if tenant is set and dimension is accessible
        -- Dimensions may be global, so we allow SELECT for all authenticated
        -- INSERT/UPDATE/DELETE requires tenant context
        EXISTS (SELECT 1 FROM legal_entity WHERE id = app_current_tenant_id())
    );

-- dimension_value: Inherits from dimension
DROP POLICY IF EXISTS "tenant_isolation" ON dimension_value;
CREATE POLICY "tenant_isolation" ON dimension_value
    FOR ALL
    USING (
        EXISTS (SELECT 1 FROM legal_entity WHERE id = app_current_tenant_id())
    );

-- gl_account: Tenant via book -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON gl_account;
CREATE POLICY "tenant_isolation" ON gl_account
    FOR ALL
    USING (
        book_id IN (SELECT id FROM book WHERE legal_entity_id = app_current_tenant_id())
    );

-- gl_account_mapping: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON gl_account_mapping;
CREATE POLICY "tenant_isolation" ON gl_account_mapping
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- accounting_period: Tenant via book -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON accounting_period;
CREATE POLICY "tenant_isolation" ON accounting_period
    FOR ALL
    USING (
        book_id IN (SELECT id FROM book WHERE legal_entity_id = app_current_tenant_id())
    );

-- journal_entry: Tenant via book -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON journal_entry;
CREATE POLICY "tenant_isolation" ON journal_entry
    FOR ALL
    USING (
        book_id IN (SELECT id FROM book WHERE legal_entity_id = app_current_tenant_id())
    );

-- journal_line: Tenant via book_id (denormalized)
DROP POLICY IF EXISTS "tenant_isolation" ON journal_line;
CREATE POLICY "tenant_isolation" ON journal_line
    FOR ALL
    USING (
        book_id IN (SELECT id FROM book WHERE legal_entity_id = app_current_tenant_id())
    );

-- journal_line_dimension: Tenant via journal_line -> journal_entry -> book
DROP POLICY IF EXISTS "tenant_isolation" ON journal_line_dimension;
CREATE POLICY "tenant_isolation" ON journal_line_dimension
    FOR ALL
    USING (
        journal_line_id IN (
            SELECT jl.id 
            FROM journal_line jl
            JOIN book b ON jl.book_id = b.id
            WHERE b.legal_entity_id = app_current_tenant_id()
        )
    );

-- =====================================================
-- PART 4: RLS POLICIES - AR TABLES
-- =====================================================

-- ar_customer: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON ar_customer;
CREATE POLICY "tenant_isolation" ON ar_customer
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- ar_invoice: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON ar_invoice;
CREATE POLICY "tenant_isolation" ON ar_invoice
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- ar_invoice_line: Tenant via ar_invoice -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON ar_invoice_line;
CREATE POLICY "tenant_isolation" ON ar_invoice_line
    FOR ALL
    USING (
        ar_invoice_id IN (
            SELECT id FROM ar_invoice WHERE legal_entity_id = app_current_tenant_id()
        )
    );

-- ar_payment: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON ar_payment;
CREATE POLICY "tenant_isolation" ON ar_payment
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- ar_allocation: Tenant via ar_payment -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON ar_allocation;
CREATE POLICY "tenant_isolation" ON ar_allocation
    FOR ALL
    USING (
        ar_payment_id IN (
            SELECT id FROM ar_payment WHERE legal_entity_id = app_current_tenant_id()
        )
    );

-- revenue_schedule: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON revenue_schedule;
CREATE POLICY "tenant_isolation" ON revenue_schedule
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- revenue_schedule_period: Tenant via revenue_schedule -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON revenue_schedule_period;
CREATE POLICY "tenant_isolation" ON revenue_schedule_period
    FOR ALL
    USING (
        revenue_schedule_id IN (
            SELECT id FROM revenue_schedule WHERE legal_entity_id = app_current_tenant_id()
        )
    );

-- =====================================================
-- PART 5: RLS POLICIES - TREASURY TABLES
-- =====================================================

-- treasury_bank_account: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON treasury_bank_account;
CREATE POLICY "tenant_isolation" ON treasury_bank_account
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- treasury_bank_transaction: Tenant via bank_account -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON treasury_bank_transaction;
CREATE POLICY "tenant_isolation" ON treasury_bank_transaction
    FOR ALL
    USING (
        bank_account_id IN (
            SELECT id FROM treasury_bank_account WHERE legal_entity_id = app_current_tenant_id()
        )
    );

-- treasury_transfer: Tenant via legal_entity_id (also handles intercompany)
DROP POLICY IF EXISTS "tenant_isolation" ON treasury_transfer;
CREATE POLICY "tenant_isolation" ON treasury_transfer
    FOR ALL
    USING (
        legal_entity_id = app_current_tenant_id()
        OR from_bank_account_id IN (SELECT id FROM treasury_bank_account WHERE legal_entity_id = app_current_tenant_id())
        OR to_bank_account_id IN (SELECT id FROM treasury_bank_account WHERE legal_entity_id = app_current_tenant_id())
    );

-- treasury_fx_conversion: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON treasury_fx_conversion;
CREATE POLICY "tenant_isolation" ON treasury_fx_conversion
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- treasury_settlement: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON treasury_settlement;
CREATE POLICY "tenant_isolation" ON treasury_settlement
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- treasury_sync_cursor: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON treasury_sync_cursor;
CREATE POLICY "tenant_isolation" ON treasury_sync_cursor
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- reconciliation_session: Tenant via bank_account -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON reconciliation_session;
CREATE POLICY "tenant_isolation" ON reconciliation_session
    FOR ALL
    USING (
        bank_account_id IN (
            SELECT id FROM treasury_bank_account WHERE legal_entity_id = app_current_tenant_id()
        )
    );

-- reconciliation_match: Tenant via reconciliation_session -> bank_account -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON reconciliation_match;
CREATE POLICY "tenant_isolation" ON reconciliation_match
    FOR ALL
    USING (
        reconciliation_session_id IN (
            SELECT rs.id 
            FROM reconciliation_session rs
            JOIN treasury_bank_account ba ON rs.bank_account_id = ba.id
            WHERE ba.legal_entity_id = app_current_tenant_id()
        )
    );

-- =====================================================
-- PART 6: RLS POLICIES - PAYROLL TABLES
-- =====================================================

-- pay_group: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON pay_group;
CREATE POLICY "tenant_isolation" ON pay_group
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- hr_employee: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON hr_employee;
CREATE POLICY "tenant_isolation" ON hr_employee
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- hr_employee_bank: Tenant via hr_employee -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON hr_employee_bank;
CREATE POLICY "tenant_isolation" ON hr_employee_bank
    FOR ALL
    USING (
        hr_employee_id IN (
            SELECT id FROM hr_employee WHERE legal_entity_id = app_current_tenant_id()
        )
    );

-- pay_component_definition: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON pay_component_definition;
CREATE POLICY "tenant_isolation" ON pay_component_definition
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- pay_component_assignment: Tenant via hr_employee -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON pay_component_assignment;
CREATE POLICY "tenant_isolation" ON pay_component_assignment
    FOR ALL
    USING (
        hr_employee_id IN (
            SELECT id FROM hr_employee WHERE legal_entity_id = app_current_tenant_id()
        )
    );

-- payroll_run: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON payroll_run;
CREATE POLICY "tenant_isolation" ON payroll_run
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- payroll_run_item: Tenant via payroll_run -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON payroll_run_item;
CREATE POLICY "tenant_isolation" ON payroll_run_item
    FOR ALL
    USING (
        payroll_run_id IN (
            SELECT id FROM payroll_run WHERE legal_entity_id = app_current_tenant_id()
        )
    );

-- payroll_run_component_line: Tenant via payroll_run_item -> payroll_run -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON payroll_run_component_line;
CREATE POLICY "tenant_isolation" ON payroll_run_component_line
    FOR ALL
    USING (
        payroll_run_item_id IN (
            SELECT pri.id 
            FROM payroll_run_item pri
            JOIN payroll_run pr ON pri.payroll_run_id = pr.id
            WHERE pr.legal_entity_id = app_current_tenant_id()
        )
    );

-- payroll_payment_batch: Tenant via payroll_run -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON payroll_payment_batch;
CREATE POLICY "tenant_isolation" ON payroll_payment_batch
    FOR ALL
    USING (
        payroll_run_id IN (
            SELECT id FROM payroll_run WHERE legal_entity_id = app_current_tenant_id()
        )
    );

-- commission_plan: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON commission_plan;
CREATE POLICY "tenant_isolation" ON commission_plan
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- commission_rule: Tenant via commission_plan -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON commission_rule;
CREATE POLICY "tenant_isolation" ON commission_rule
    FOR ALL
    USING (
        commission_plan_id IN (
            SELECT id FROM commission_plan WHERE legal_entity_id = app_current_tenant_id()
        )
    );

-- commission_ledger: Tenant via hr_employee -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON commission_ledger;
CREATE POLICY "tenant_isolation" ON commission_ledger
    FOR ALL
    USING (
        hr_employee_id IN (
            SELECT id FROM hr_employee WHERE legal_entity_id = app_current_tenant_id()
        )
    );

-- bonus_plan: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON bonus_plan;
CREATE POLICY "tenant_isolation" ON bonus_plan
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- bonus_result: Tenant via bonus_plan -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON bonus_result;
CREATE POLICY "tenant_isolation" ON bonus_result
    FOR ALL
    USING (
        bonus_plan_id IN (
            SELECT id FROM bonus_plan WHERE legal_entity_id = app_current_tenant_id()
        )
    );

-- pay_rule_set: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON pay_rule_set;
CREATE POLICY "tenant_isolation" ON pay_rule_set
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- pay_rule: Tenant via pay_rule_set -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON pay_rule;
CREATE POLICY "tenant_isolation" ON pay_rule
    FOR ALL
    USING (
        pay_rule_set_id IN (
            SELECT id FROM pay_rule_set WHERE legal_entity_id = app_current_tenant_id()
        )
    );

-- stat_contribution_rule: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON stat_contribution_rule;
CREATE POLICY "tenant_isolation" ON stat_contribution_rule
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- tax_withholding_table: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON tax_withholding_table;
CREATE POLICY "tenant_isolation" ON tax_withholding_table
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- payroll_export_template: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON payroll_export_template;
CREATE POLICY "tenant_isolation" ON payroll_export_template
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- payroll_liability_balance: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON payroll_liability_balance;
CREATE POLICY "tenant_isolation" ON payroll_liability_balance
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- =====================================================
-- PART 7: RLS POLICIES - INTERCOMPANY TABLES
-- =====================================================

-- intercompany_transfer: Tenant via from_entity_id OR to_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON intercompany_transfer;
CREATE POLICY "tenant_isolation" ON intercompany_transfer
    FOR ALL
    USING (
        from_entity_id = app_current_tenant_id()
        OR to_entity_id = app_current_tenant_id()
    );

-- royalty_agreement: Tenant via from_entity_id OR to_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON royalty_agreement;
CREATE POLICY "tenant_isolation" ON royalty_agreement
    FOR ALL
    USING (
        from_entity_id = app_current_tenant_id()
        OR to_entity_id = app_current_tenant_id()
    );

-- royalty_calculation: Tenant via royalty_agreement -> from_entity_id/to_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON royalty_calculation;
CREATE POLICY "tenant_isolation" ON royalty_calculation
    FOR ALL
    USING (
        royalty_agreement_id IN (
            SELECT id FROM royalty_agreement 
            WHERE from_entity_id = app_current_tenant_id()
            OR to_entity_id = app_current_tenant_id()
        )
    );

-- intercompany_balance: Tenant via from_entity_id OR to_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON intercompany_balance;
CREATE POLICY "tenant_isolation" ON intercompany_balance
    FOR ALL
    USING (
        from_entity_id = app_current_tenant_id()
        OR to_entity_id = app_current_tenant_id()
    );

-- =====================================================
-- PART 8: RLS POLICIES - EXTERNAL SYNC TABLES
-- =====================================================

-- external_sync_cursor: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON external_sync_cursor;
CREATE POLICY "tenant_isolation" ON external_sync_cursor
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- source_object_map: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON source_object_map;
CREATE POLICY "tenant_isolation" ON source_object_map
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- =====================================================
-- PART 9: RLS POLICIES - AP TABLES
-- =====================================================

-- ap_withholding_profile: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON ap_withholding_profile;
CREATE POLICY "tenant_isolation" ON ap_withholding_profile
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- ap_vendor: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON ap_vendor;
CREATE POLICY "tenant_isolation" ON ap_vendor
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- ap_bill: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON ap_bill;
CREATE POLICY "tenant_isolation" ON ap_bill
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- ap_bill_line: Tenant via ap_bill -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON ap_bill_line;
CREATE POLICY "tenant_isolation" ON ap_bill_line
    FOR ALL
    USING (
        ap_bill_id IN (
            SELECT id FROM ap_bill WHERE legal_entity_id = app_current_tenant_id()
        )
    );

-- ap_payment: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON ap_payment;
CREATE POLICY "tenant_isolation" ON ap_payment
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- ap_allocation: Tenant via ap_payment -> legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON ap_allocation;
CREATE POLICY "tenant_isolation" ON ap_allocation
    FOR ALL
    USING (
        ap_payment_id IN (
            SELECT id FROM ap_payment WHERE legal_entity_id = app_current_tenant_id()
        )
    );

-- =====================================================
-- PART 10: RLS POLICIES - AFFILIATE TABLES
-- =====================================================

-- affiliate_partner: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON affiliate_partner;
CREATE POLICY "tenant_isolation" ON affiliate_partner
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- affiliate_agreement: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON affiliate_agreement;
CREATE POLICY "tenant_isolation" ON affiliate_agreement
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- affiliate_earning_event: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON affiliate_earning_event;
CREATE POLICY "tenant_isolation" ON affiliate_earning_event
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- affiliate_payout: Tenant via legal_entity_id
DROP POLICY IF EXISTS "tenant_isolation" ON affiliate_payout;
CREATE POLICY "tenant_isolation" ON affiliate_payout
    FOR ALL
    USING (legal_entity_id = app_current_tenant_id());

-- =====================================================
-- PART 11: SERVICE ROLE BYPASS (FOR SYSTEM OPERATIONS)
-- =====================================================

-- Service role can bypass RLS for system operations (migrations, sync, etc.)
-- This is handled by Supabase automatically when using service_role key
-- NO additional policies needed - service_role bypasses RLS by default

-- =====================================================
-- PART 12: VERIFICATION QUERIES
-- =====================================================

-- Run these after applying to verify RLS is active:

-- Check RLS is enabled on all tables:
-- SELECT schemaname, tablename, rowsecurity 
-- FROM pg_tables 
-- WHERE schemaname = 'public' AND rowsecurity = true;

-- List all policies:
-- SELECT schemaname, tablename, policyname, permissive, roles, cmd, qual 
-- FROM pg_policies 
-- WHERE schemaname = 'public'
-- ORDER BY tablename;

-- Test tenant isolation (replace with actual UUID):
-- SET app.current_tenant_id = '00000000-0000-0000-0000-000000000000';
-- SELECT * FROM legal_entity;  -- Should return only 1 row (the tenant itself)

-- =====================================================
-- END OF RLS POLICIES
-- =====================================================
