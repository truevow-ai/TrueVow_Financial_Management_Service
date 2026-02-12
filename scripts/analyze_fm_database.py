from sqlalchemy import create_engine, text
engine = create_engine('postgresql://postgres.ififhzrbhadmtedyvzhb:Intakely%40786@aws-1-us-east-1.pooler.supabase.com:6543/postgres')
conn = engine.connect()

# Get all current tables
result = conn.execute(text("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema='public' 
    ORDER BY table_name
"""))
current_tables = {r[0] for r in result.fetchall()}

# Define expected FM tables based on models
expected_fm_tables = {
    # Core GL
    'legal_entity',
    'book',
    'dimension',
    'dimension_value',
    'gl_account',
    'gl_account_mapping',
    'accounting_period',
    'journal_entry',
    'journal_line',
    'journal_line_dimension',
    'period_close_checklist',
    
    # AR (Accounts Receivable)
    'ar_customer',
    'ar_invoice',
    'ar_invoice_line',
    'ar_payment',
    'ar_allocation',
    'revenue_schedule',
    'revenue_schedule_period',
    'billing_sync_batch',
    
    # AP (Accounts Payable)
    'ap_vendor',
    'ap_bill',
    'ap_bill_line',
    'ap_payment',
    'ap_allocation',
    'ap_withholding_profile',
    
    # Treasury/Cash Management
    'treasury_bank_account',
    'treasury_bank_transaction',
    'treasury_settlement',
    'treasury_fx_conversion',
    'treasury_transfer',
    'treasury_sync_cursor',
    
    # Payroll
    'hr_employee',
    'hr_employee_bank',
    'pay_group',
    'pay_component_definition',
    'pay_component_assignment',
    'payroll_run',
    'payroll_run_item',
    'payroll_run_component_line',
    'payroll_payment_batch',
    'commission_plan',
    'commission_rule',
    'commission_ledger',
    'bonus_plan',
    'bonus_result',
    'pay_rule_set',
    'pay_rule',
    'stat_contribution_rule',
    'tax_withholding_table',
    'payroll_export_template',
    'payroll_liability_balance',
    
    # Intercompany
    'intercompany_transfer',
    'intercompany_balance',
    'royalty_agreement',
    'royalty_calculation',
    
    # Affiliates
    'affiliate_partner',
    'affiliate_agreement',
    'affiliate_earning_event',
    'affiliate_payout',
    
    # Reconciliation
    'reconciliation_session',
    'reconciliation_match',
    
    # Sync/Integration
    'external_sync_cursor',
    'source_object_map',
    
    # Core Infrastructure
    'idempotency_keys',
    'audit_log',
    'alembic_version',
}

# Tables that should NOT be in FM database
non_fm_tables = {t for t in current_tables if 'cs_' in t or 'onboarding' in t or 'cursor' in t}

# Missing FM tables
missing_fm_tables = expected_fm_tables - current_tables

# Extra tables (not FM-related)
extra_tables = current_tables - expected_fm_tables

print("=== FINANCIAL MANAGEMENT DATABASE ANALYSIS ===\n")
print(f"Total tables in database: {len(current_tables)}")
print(f"Expected FM tables: {len(expected_fm_tables)}")
print(f"Tables present: {len(current_tables & expected_fm_tables)}")
print(f"Missing FM tables: {len(missing_fm_tables)}")
print(f"Non-FM tables (should be removed): {len(non_fm_tables)}")

if missing_fm_tables:
    print(f"\n[MISSING] FM TABLES ({len(missing_fm_tables)}):")
    for t in sorted(missing_fm_tables):
        print(f"  - {t}")

if non_fm_tables:
    print(f"\n[REMOVE] NON-FM TABLES ({len(non_fm_tables)}):")
    for t in sorted(non_fm_tables):
        print(f"  - {t}")

if extra_tables - non_fm_tables:
    print(f"\n[WARNING] OTHER EXTRA TABLES ({len(extra_tables - non_fm_tables)}):")
    for t in sorted(extra_tables - non_fm_tables):
        print(f"  - {t}")

print(f"\n[OK] FM TABLES PRESENT ({len(current_tables & expected_fm_tables)}):")
for t in sorted(current_tables & expected_fm_tables):
    print(f"  - {t}")

conn.close()
