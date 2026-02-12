"""add_audit_columns_to_base_tables

Revision ID: 2e8a98e93966
Revises: 005_add_idempotency_metadata
Create Date: 2026-02-02 04:26:37.894808

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e8a98e93966'
down_revision = '005_add_idempotency_metadata'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add created_by and updated_by to all base tables that inherit from BaseModel
    tables = [
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
        'reconciliation_session',
        'reconciliation_match',
        'external_sync_cursor',
        'source_object_map',
        'treasury_sync_batch',
        'ar_customer',
        'ar_invoice',
        'ar_invoice_line',
        'ar_payment',
        'ar_allocation',
        'revenue_schedule',
        'revenue_schedule_period',
        'billing_sync_batch',
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
        'intercompany_transfer',
        'royalty_agreement',
        'royalty_calculation',
        'intercompany_balance',
        'bank_account',
        'bank_transaction',
        'settlement',
        'fx_conversion',
        'transfer',
        'sync_cursor',
        'ap_vendor',
        'ap_bill',
        'ap_bill_line',
        'ap_payment',
        'ap_allocation',
        'ap_withholding_profile',
        'idempotency_key',
        'audit_log',
    ]
    
    from sqlalchemy.dialects import postgresql
    
    for table in tables:
        # Check if table exists AND columns exist before adding
        op.execute(f"""
            DO $$ 
            BEGIN
                IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name='{table}') THEN
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='{table}' AND column_name='created_by') THEN
                        ALTER TABLE {table} ADD COLUMN created_by UUID;
                    END IF;
                    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                                   WHERE table_name='{table}' AND column_name='updated_by') THEN
                        ALTER TABLE {table} ADD COLUMN updated_by UUID;
                    END IF;
                END IF;
            END $$;
        """)


def downgrade() -> None:
    # Remove created_by and updated_by from all base tables
    tables = [
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
        'reconciliation_session',
        'reconciliation_match',
        'external_sync_cursor',
        'source_object_map',
        'treasury_sync_batch',
        'ar_customer',
        'ar_invoice',
        'ar_invoice_line',
        'ar_payment',
        'ar_allocation',
        'revenue_schedule',
        'revenue_schedule_period',
        'billing_sync_batch',
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
        'intercompany_transfer',
        'royalty_agreement',
        'royalty_calculation',
        'intercompany_balance',
        'bank_account',
        'bank_transaction',
        'settlement',
        'fx_conversion',
        'transfer',
        'sync_cursor',
        'ap_vendor',
        'ap_bill',
        'ap_bill_line',
        'ap_payment',
        'ap_allocation',
        'ap_withholding_profile',
        'idempotency_key',
        'audit_log',
    ]
    
    for table in tables:
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS created_by")
        op.execute(f"ALTER TABLE {table} DROP COLUMN IF EXISTS updated_by")
