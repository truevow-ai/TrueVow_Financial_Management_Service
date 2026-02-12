from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres.ififhzrbhadmtedyvzhb:Intakely%40786@aws-1-us-east-1.pooler.supabase.com:6543/postgres')
conn = engine.connect()

# Get current tables
result = conn.execute(text("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema='public' 
    ORDER BY table_name
"""))
current_tables = {r[0] for r in result.fetchall()}

# Expected FM tables per PRD Section 13 (Data Model)
expected_fm_tables = {
    # Shared Concepts
    'legal_entity',
    'book',
    'dimension',
    'dimension_value',
    'journal_line_dimension',
    'audit_log',
    'idempotency_keys',
    'external_sync_cursor',
    'source_object_map',
    
    # FM Core
    'gl_account',
    'gl_account_mapping',
    'accounting_period',
    'journal_entry',
    'journal_line',
    
    # AR
    'ar_customer',
    'ar_invoice',
    'ar_invoice_line',
    'ar_payment',
    'ar_allocation',
    
    # Deferred Revenue
    'revenue_schedule',
    'revenue_schedule_period',
    
    # AP
    'ap_vendor',
    'ap_bill',
    'ap_bill_line',
    'ap_payment',
    'ap_allocation',
    'ap_withholding_profile',
    
    # Payroll
    'hr_employee',
    'hr_employee_bank',
    'pay_group',
    'pay_component_definition',
    'pay_component_assignment',
    'pay_rule_set',
    'pay_rule',
    'stat_contribution_rule',
    'tax_withholding_table',
    'payroll_run',
    'payroll_run_item',
    'payroll_run_component_line',
    'payroll_payment_batch',
    'payroll_export_template',
    'payroll_liability_balance',
    'commission_plan',
    'commission_rule',
    'commission_ledger',
    'bonus_plan',
    'bonus_result',
    
    # Affiliates
    'affiliate_partner',
    'affiliate_agreement',
    'affiliate_earning_event',
    'affiliate_payout',
    
    # Treasury
    'treasury_bank_account',
    'treasury_bank_transaction',
    'treasury_settlement',
    'treasury_fx_conversion',
    'treasury_transfer',
    'treasury_sync_cursor',
    
    # Reconciliation
    'reconciliation_session',
    'reconciliation_match',
    
    # Intercompany
    'intercompany_transfer',
    'intercompany_balance',
    'royalty_agreement',
    'royalty_calculation',
    
    # Sync/Integration
    'billing_sync_batch',
    
    # Period Management
    'period_close_checklist',
    
    # Infrastructure
    'alembic_version',
}

# Non-FM tables (should be removed)
non_fm_tables = {
    'cs_customer_onboarding_progress',
    'cs_onboarding_calendar_integrations',
    'cs_onboarding_communications',
    'cs_onboarding_compliance_settings',
    'cs_onboarding_firm_profile',
    'cs_onboarding_milestone_completions',
    'cs_onboarding_milestones',
    'cs_onboarding_phone_config',
    'cs_onboarding_sequences',
    'cs_onboarding_step_completions',
}

# Analysis
missing_fm = expected_fm_tables - current_tables
present_fm = current_tables & expected_fm_tables
unwanted = current_tables & non_fm_tables
unknown = current_tables - expected_fm_tables - non_fm_tables

print("=== FM DATABASE TABLE ANALYSIS (per PRD Section 13) ===\\n")
print(f"Expected FM tables (PRD): {len(expected_fm_tables)}")
print(f"Current tables in DB: {len(current_tables)}")
print(f"FM tables present: {len(present_fm)}/{len(expected_fm_tables)} ({100*len(present_fm)//len(expected_fm_tables)}%)")
print(f"Missing FM tables: {len(missing_fm)}")
print(f"Non-FM tables (CS onboarding): {len(unwanted)}")
print(f"Unknown/unexpected tables: {len(unknown)}")

if missing_fm:
    print(f"\\n[MISSING] FM TABLES ({len(missing_fm)}):")
    for t in sorted(missing_fm):
        print(f"  - {t}")

if unwanted:
    print(f"\\n[REMOVE] NON-FM TABLES ({len(unwanted)}):")
    for t in sorted(unwanted):
        print(f"  - {t}")

if unknown:
    print(f"\\n[WARNING] UNEXPECTED TABLES (not in PRD, not CS) ({len(unknown)}):")
    for t in sorted(unknown):
        print(f"  - {t}")

print(f"\\n[OK] FM TABLES PRESENT ({len(present_fm)}):")
for t in sorted(present_fm):
    print(f"  - {t}")

conn.close()

print("\\n=== RECOMMENDATIONS ===")
if missing_fm:
    print(f"1. Create {len(missing_fm)} missing tables (see fix_missing_tables.sql)")
if unwanted:
    print(f"2. Remove {len(unwanted)} CS onboarding tables (see fix_missing_tables.sql)")
if unknown:
    print(f"3. Review {len(unknown)} unexpected tables - verify if needed or remove")
if not missing_fm and not unwanted:
    print("Database schema matches PRD Section 13!")
