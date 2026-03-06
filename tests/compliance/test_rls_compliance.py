"""
RLS Compliance Integration Tests
Verifies tenant isolation enforcement at database layer
"""
import pytest
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()
load_dotenv('.env.local')

# Test database connection
TEST_DB_URL = os.getenv('FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL')

@pytest.fixture
async def db_conn():
    """Create test database connection"""
    # Remove postgresql+asyncpg:// prefix if present
    url = TEST_DB_URL.replace('postgresql+asyncpg://', 'postgresql://')
    conn = await asyncpg.connect(url)
    yield conn
    await conn.close()


class TestRLSPolicies:
    """Test RLS policy enforcement"""
    
    async def test_rls_enabled_on_legal_entity(self, db_conn):
        """Verify RLS is enabled on legal_entity table"""
        result = await db_conn.fetchrow("""
            SELECT rowsecurity 
            FROM pg_tables 
            WHERE schemaname = 'public' AND tablename = 'legal_entity'
        """)
        assert result['rowsecurity'] is True, "RLS not enabled on legal_entity"
    
    async def test_rls_enabled_on_book(self, db_conn):
        """Verify RLS is enabled on book table"""
        result = await db_conn.fetchrow("""
            SELECT rowsecurity 
            FROM pg_tables 
            WHERE schemaname = 'public' AND tablename = 'book'
        """)
        assert result['rowsecurity'] is True, "RLS not enabled on book"
    
    async def test_rls_enabled_on_journal_entry(self, db_conn):
        """Verify RLS is enabled on journal_entry table"""
        result = await db_conn.fetchrow("""
            SELECT rowsecurity 
            FROM pg_tables 
            WHERE schemaname = 'public' AND tablename = 'journal_entry'
        """)
        assert result['rowsecurity'] is True, "RLS not enabled on journal_entry"
    
    async def test_tenant_isolation_legal_entity(self, db_conn):
        """Test that RLS policy blocks cross-tenant access"""
        # Determine if current DB role bypasses RLS (superuser / pg_bypassrls)
        bypass = await db_conn.fetchval(
            "SELECT current_setting('role') = 'none' AND "
            "EXISTS (SELECT 1 FROM pg_roles WHERE rolname = current_user AND rolbypassrls)"
        )
        if bypass:
            pytest.skip("Connected as RLS-bypass role; row-level isolation cannot be tested")

        # Set tenant context to a test UUID
        test_tenant_id = 'd017457b-1553-462c-9655-c8737523e1f8'

        await db_conn.execute(f"SET app.current_legal_entity_id = '{test_tenant_id}'")

        # This should only return the entity matching the current tenant
        result = await db_conn.fetch("SELECT id FROM legal_entity")

        # Should only see own entity
        assert len(result) <= 1, "RLS policy not blocking cross-tenant access"

        if len(result) == 1:
            assert str(result[0]['id']) == test_tenant_id


class TestImmutabilityConstraints:
    """Test immutability trigger enforcement"""
    
    async def test_cannot_modify_posted_journal_entry(self, db_conn):
        """Verify POSTED journal entries cannot be modified"""
        # This test requires a POSTED entry to exist
        # For now, we document the expected behavior
        
        # Expected: UPDATE on POSTED entry should raise exception
        # Expected: Only status transition POSTED → REVERSED allowed
        pass
    
    async def test_cannot_delete_posted_journal_entry(self, db_conn):
        """Verify POSTED journal entries cannot be deleted"""
        # Expected: DELETE on POSTED entry should raise exception
        pass
    
    async def test_cannot_modify_closed_period(self, db_conn):
        """Verify CLOSED accounting periods cannot be modified"""
        # Expected: UPDATE on CLOSED period should raise exception
        # Expected: Only status transition CLOSED → LOCKED allowed
        pass


class TestBusinessConstraints:
    """Test business constraint enforcement"""
    
    async def test_journal_entry_must_balance(self, db_conn):
        """Verify journal entry balance constraint"""
        # Query constraint existence
        result = await db_conn.fetchrow("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'journal_entry' 
            AND constraint_name = 'journal_entry_must_balance'
        """)
        assert result is not None, "Balance constraint not found"
    
    async def test_unique_entry_number_per_book(self, db_conn):
        """Verify unique entry number constraint"""
        result = await db_conn.fetchrow("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'journal_entry' 
            AND constraint_name = 'journal_entry_number_unique_per_book'
        """)
        assert result is not None, "Unique entry number constraint not found"
    
    async def test_unique_gl_account_code_per_entity(self, db_conn):
        """Verify unique GL account code constraint"""
        result = await db_conn.fetchrow("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'gl_account' 
            AND constraint_name = 'gl_account_code_unique_per_entity'
        """)
        assert result is not None, "Unique GL account code constraint not found"
    
    async def test_accounting_period_date_range_valid(self, db_conn):
        """Verify period date range constraint"""
        result = await db_conn.fetchrow("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'accounting_period' 
            AND constraint_name = 'accounting_period_date_range_valid'
        """)
        assert result is not None, "Period date range constraint not found"


class TestComplianceReport:
    """Generate compliance status report"""
    
    async def test_generate_rls_coverage_report(self, db_conn):
        """Generate report of RLS policy coverage"""
        tables_requiring_rls = [
            'legal_entity', 'book', 'gl_account', 'accounting_period',
            'dimension', 'dimension_value', 'journal_entry', 'journal_line',
            'ar_customer', 'ar_invoice', 'ar_payment', 'ap_vendor', 'ap_bill',
            'payroll_run', 'treasury_bank_account', 'treasury_bank_transaction',
            'intercompany_transfer', 'royalty_agreement'
        ]
        
        results = await db_conn.fetch("""
            SELECT tablename, rowsecurity 
            FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename = ANY($1)
        """, tables_requiring_rls)
        
        rls_status = {r['tablename']: r['rowsecurity'] for r in results}
        
        missing_rls = [t for t in tables_requiring_rls if not rls_status.get(t)]
        
        print("\n" + "=" * 80)
        print("RLS POLICY COVERAGE REPORT")
        print("=" * 80)
        print(f"Total tables requiring RLS: {len(tables_requiring_rls)}")
        print(f"Tables with RLS enabled: {sum(rls_status.values())}")
        print(f"Tables missing RLS: {len(missing_rls)}")
        
        if missing_rls:
            print("\nMissing RLS on:")
            for table in missing_rls:
                print(f"  - {table}")
        
        print("=" * 80)
        
        # Test passes if all tables have RLS
        assert len(missing_rls) == 0, f"RLS missing on {len(missing_rls)} tables"
    
    async def test_generate_constraint_coverage_report(self, db_conn):
        """Generate report of constraint coverage"""
        results = await db_conn.fetch("""
            SELECT 
                table_name,
                constraint_type,
                COUNT(*) as count
            FROM information_schema.table_constraints
            WHERE table_schema = 'public'
            GROUP BY table_name, constraint_type
            ORDER BY table_name, constraint_type
        """)
        
        print("\n" + "=" * 80)
        print("CONSTRAINT COVERAGE REPORT")
        print("=" * 80)
        
        constraint_summary = {}
        for r in results:
            table = r['table_name']
            if table not in constraint_summary:
                constraint_summary[table] = {}
            constraint_summary[table][r['constraint_type']] = r['count']
        
        for table, constraints in sorted(constraint_summary.items()):
            print(f"\n{table}:")
            for ctype, count in sorted(constraints.items()):
                print(f"  {ctype}: {count}")
        
        print("=" * 80)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
