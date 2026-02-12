#!/usr/bin/env python3
"""
Script to verify database connection and schema

Usage:
    python scripts/verify_database.py
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set dummy JWT_SECRET_KEY if not present (for verification script only)
if "JWT_SECRET_KEY" not in os.environ:
    os.environ["JWT_SECRET_KEY"] = "dummy-secret-key-for-verification-only"

async def test_connection():
    """Test database connection"""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from app.core.config import settings
        
        print("[INFO] Testing database connection...")
        engine = create_async_engine(settings.effective_database_url, echo=False)
        async with engine.connect() as conn:
            from sqlalchemy import text
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("[OK] Database connection successful!")
                await engine.dispose()
                return True
            else:
                print("[FAIL] Database connection test failed")
                await engine.dispose()
                return False
    except Exception as e:
        print(f"[ERROR] Database connection error: {e}")
        return False

async def check_tables():
    """Check if tables exist"""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        from app.core.config import settings
        
        engine = create_async_engine(settings.effective_database_url, echo=False)
        
        # Expected tables from PRD
        expected_tables = {
            # Core
            'legal_entity', 'book', 'dimension', 'dimension_value', 'gl_account',
            'gl_account_mapping', 'accounting_period', 'journal_entry', 'journal_line',
            'journal_line_dimension',
            # AR
            'ar_customer', 'ar_invoice', 'ar_invoice_line', 'ar_payment', 'ar_allocation',
            'revenue_schedule', 'revenue_schedule_period',
            # AP
            'ap_vendor', 'ap_bill', 'ap_bill_line', 'ap_payment', 'ap_allocation',
            'ap_withholding_profile',
            # Treasury
            'treasury_bank_account', 'treasury_bank_transaction', 'treasury_settlement',
            'treasury_fx_conversion', 'treasury_transfer', 'treasury_sync_cursor',
            'reconciliation_session', 'reconciliation_match',
            # Payroll
            'hr_employee', 'hr_employee_bank', 'pay_group', 'pay_component_definition',
            'pay_component_assignment', 'pay_rule_set', 'pay_rule', 'stat_contribution_rule',
            'tax_withholding_table', 'payroll_run', 'payroll_run_item',
            'payroll_run_component_line', 'payroll_payment_batch', 'payroll_export_template',
            'payroll_liability_balance', 'commission_plan', 'commission_rule',
            'commission_ledger', 'bonus_plan', 'bonus_result',
            # Intercompany
            'intercompany_transfer', 'royalty_agreement', 'royalty_calculation',
            'intercompany_balance',
            # Affiliates
            'affiliate_partner', 'affiliate_agreement', 'affiliate_earning_event',
            'affiliate_payout',
            # External Sync
            'external_sync_cursor', 'source_object_map',
            # Core System
            'audit_log', 'idempotency_keys'
        }
        
        print("\n🔄 Checking database tables...")
        async with engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            existing_tables = {row[0] for row in result.fetchall()}
            
            if existing_tables:
                print(f"[OK] Found {len(existing_tables)} tables in database")
                
                # Check expected tables
                missing_tables = expected_tables - existing_tables
                found_tables = expected_tables & existing_tables
                extra_tables = existing_tables - expected_tables
                
                print(f"\n[STATUS] Table Status:")
                print(f"   [OK] Expected tables found: {len(found_tables)}/{len(expected_tables)}")
                
                if missing_tables:
                    print(f"   [WARN] Missing tables ({len(missing_tables)}):")
                    for table in sorted(missing_tables):
                        print(f"      - {table}")
                
                if extra_tables:
                    print(f"   [INFO] Extra tables ({len(extra_tables)}):")
                    for table in sorted(list(extra_tables)[:10]):
                        print(f"      - {table}")
                    if len(extra_tables) > 10:
                        print(f"      ... and {len(extra_tables) - 10} more")
                
                # Check ENUM types
                enum_result = await conn.execute(text("""
                    SELECT typname 
                    FROM pg_type 
                    WHERE typtype = 'e'
                    ORDER BY typname
                """))
                existing_enums = {row[0] for row in enum_result.fetchall()}
                expected_enums = {
                    'book_type', 'period_status', 'account_type', 'journal_entry_status',
                    'invoice_status', 'payment_status', 'schedule_status', 'transaction_type',
                    'transfer_type', 'reconciliation_status', 'payroll_run_status',
                    'component_type', 'pay_frequency', 'pay_day_rule', 'employee_type'
                }
                
                found_enums = expected_enums & existing_enums
                missing_enums = expected_enums - existing_enums
                
                print(f"\n[STATUS] ENUM Status:")
                print(f"   [OK] Expected ENUMs found: {len(found_enums)}/{len(expected_enums)}")
                if missing_enums:
                    print(f"   [WARN] Missing ENUMs ({len(missing_enums)}):")
                    for enum in sorted(missing_enums):
                        print(f"      - {enum}")
                
                await engine.dispose()
                return len(missing_tables) == 0 and len(missing_enums) == 0
            else:
                print("[WARN] No tables found. Run schema SQL file first.")
                await engine.dispose()
                return False
    except Exception as e:
        print(f"[ERROR] Error checking tables: {e}")
        import traceback
        traceback.print_exc()
        return False

async def check_audit_fields():
    """Check if tables have audit fields"""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        from sqlalchemy import text
        from app.core.config import settings
        
        engine = create_async_engine(settings.effective_database_url, echo=False)
        
        print("\n[INFO] Checking audit fields (created_by, updated_by)...")
        async with engine.connect() as conn:
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            
            tables_without_audit = []
            for table in tables:
                # Skip system tables
                if table.startswith('_') or table.startswith('pg_'):
                    continue
                    
                check_result = await conn.execute(text(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public' 
                    AND table_name = :table_name
                    AND column_name IN ('created_by', 'updated_by')
                """), {"table_name": table})
                audit_cols = {row[0] for row in check_result.fetchall()}
                
                if 'created_by' not in audit_cols or 'updated_by' not in audit_cols:
                    tables_without_audit.append(table)
            
            if tables_without_audit:
                print(f"   [WARN] Tables missing audit fields ({len(tables_without_audit)}):")
                for table in tables_without_audit[:10]:
                    print(f"      - {table}")
                if len(tables_without_audit) > 10:
                    print(f"      ... and {len(tables_without_audit) - 10} more")
                return False
            else:
                print(f"   [OK] All {len(tables)} tables have audit fields")
                await engine.dispose()
                return True
    except Exception as e:
        print(f"[ERROR] Error checking audit fields: {e}")
        return False

async def main():
    """Main function"""
    print("=" * 60)
    print("TrueVow FM Service - Database Verification")
    print("=" * 60)
    print()
    
    # Test connection
    if not await test_connection():
        print("\n[FAIL] Database verification failed")
        sys.exit(1)
    
    # Check tables
    tables_ok = await check_tables()
    
    # Check audit fields
    audit_ok = await check_audit_fields()
    
    # Overall status
    if tables_ok and audit_ok:
        print("\n[SUCCESS] Database verification complete! Schema is ready.")
    else:
        print("\n[WARN] Database verification found issues. Please review above.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
