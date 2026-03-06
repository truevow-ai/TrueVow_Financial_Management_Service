"""
RLS Tenant Isolation Integration Tests

Tests verify that Row-Level Security policies correctly isolate tenant data.

IMPORTANT: These tests require a PostgreSQL database with RLS policies deployed.
Set TEST_DATABASE_URL to your PostgreSQL connection string.

Example:
    export TEST_DATABASE_URL="postgresql://user:pass@host:5432/dbname"
    pytest tests/integration/test_rls_tenant_isolation.py -v
"""

import os
import pytest
from uuid import uuid4
from datetime import date
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

# Skip all tests if no PostgreSQL URL is set
pytestmark = pytest.mark.skipif(
    not os.environ.get("TEST_DATABASE_URL"),
    reason="TEST_DATABASE_URL must be set to a PostgreSQL database for RLS tests"
)


def get_test_db_url():
    """Get PostgreSQL URL for RLS tests."""
    url = os.environ.get("TEST_DATABASE_URL")
    if "postgresql://" in url and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


@pytest.fixture
async def rls_session():
    """Create a session for RLS testing."""
    url = get_test_db_url()
    engine = create_async_engine(url, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_maker() as session:
        yield session
    
    await engine.dispose()


@pytest.fixture
async def tenant_a_id() -> str:
    """Generate tenant A UUID."""
    return str(uuid4())


@pytest.fixture
async def tenant_b_id() -> str:
    """Generate tenant B UUID."""
    return str(uuid4())


class TestRLSTenantIsolation:
    """Test Row-Level Security tenant isolation."""

    async def test_set_tenant_context(self, rls_session: AsyncSession, tenant_a_id: str):
        """Test that tenant context can be set."""
        # Set tenant context
        await rls_session.execute(
            text("SET LOCAL app.current_tenant_id = '" + tenant_a_id + "'")
        )
        
        # Verify context is set
        result = await rls_session.execute(text("SELECT app_current_tenant_id()"))
        tenant_id = result.scalar()
        
        # Compare as strings since result might be UUID object
        assert str(tenant_id) == str(tenant_a_id), f"Expected {tenant_a_id}, got {tenant_id}"

    async def test_rls_helper_function_returns_null_without_context(
        self, rls_session: AsyncSession
    ):
        """Test that app_current_tenant_id() returns NULL when no context is set."""
        result = await rls_session.execute(text("SELECT app_current_tenant_id()"))
        tenant_id = result.scalar()
        
        assert tenant_id is None, f"Expected NULL, got {tenant_id}"

    async def test_legal_entity_isolation(
        self, rls_session: AsyncSession, tenant_a_id: str, tenant_b_id: str
    ):
        """Test that RLS policies exist for legal_entity table.
        
        NOTE: When connecting with service_role (which we use for tests),
        RLS is bypassed. This test verifies that:
        1. RLS is enabled on the table
        2. Policies exist
        3. The helper function works correctly
        
        Actual RLS enforcement must be tested with non-service role.
        """
        # Verify RLS is enabled on legal_entity
        result = await rls_session.execute(text("""
            SELECT rowsecurity FROM pg_tables 
            WHERE schemaname = 'public' AND tablename = 'legal_entity'
        """))
        rls_enabled = result.scalar()
        assert rls_enabled == True, "RLS should be enabled on legal_entity table"
        
        # Verify policy exists
        result = await rls_session.execute(text("""
            SELECT COUNT(*) FROM pg_policies 
            WHERE schemaname = 'public' AND tablename = 'legal_entity'
        """))
        policy_count = result.scalar()
        assert policy_count >= 1, "At least one RLS policy should exist on legal_entity"

    async def test_book_isolation_via_legal_entity(
        self, rls_session: AsyncSession, tenant_a_id: str, tenant_b_id: str
    ):
        """Test that RLS policies exist for book table.
        
        NOTE: RLS is bypassed with service_role. This verifies policy existence.
        """
        # Verify RLS is enabled on book
        result = await rls_session.execute(text("""
            SELECT rowsecurity FROM pg_tables 
            WHERE schemaname = 'public' AND tablename = 'book'
        """))
        rls_enabled = result.scalar()
        assert rls_enabled == True, "RLS should be enabled on book table"
        
        # Verify policy exists
        result = await rls_session.execute(text("""
            SELECT COUNT(*) FROM pg_policies 
            WHERE schemaname = 'public' AND tablename = 'book'
        """))
        policy_count = result.scalar()
        assert policy_count >= 1, "At least one RLS policy should exist on book"

    async def test_journal_entry_isolation(
        self, rls_session: AsyncSession, tenant_a_id: str, tenant_b_id: str
    ):
        """Test that RLS policies exist for journal_entry table.
        
        NOTE: RLS is bypassed with service_role. This verifies policy existence.
        """
        # Verify RLS is enabled on journal_entry
        result = await rls_session.execute(text("""
            SELECT rowsecurity FROM pg_tables 
            WHERE schemaname = 'public' AND tablename = 'journal_entry'
        """))
        rls_enabled = result.scalar()
        assert rls_enabled == True, "RLS should be enabled on journal_entry table"
        
        # Verify policy exists
        result = await rls_session.execute(text("""
            SELECT COUNT(*) FROM pg_policies 
            WHERE schemaname = 'public' AND tablename = 'journal_entry'
        """))
        policy_count = result.scalar()
        assert policy_count >= 1, "At least one RLS policy should exist on journal_entry"


class TestImmutabilityConstraints:
    """Test immutability triggers."""

    async def test_cannot_modify_posted_journal_entry(
        self, rls_session: AsyncSession, tenant_a_id: str
    ):
        """Test that POSTED journal entries cannot be modified."""
        # Setup
        code_a = f"TENA{uuid4().hex[:4].upper()}"
        await rls_session.execute(text("""
            INSERT INTO legal_entity (id, code, name, country, functional_currency, is_active)
            VALUES (:id, :code, 'Tenant A', 'US', 'USD', true)
        """), {"id": tenant_a_id, "code": code_a})
        
        book_id = str(uuid4())
        await rls_session.execute(text("""
            INSERT INTO book (id, legal_entity_id, book_type, name, is_active)
            VALUES (:id, :le_id, 'ACCRUAL', 'Test Book', true)
        """), {"id": book_id, "le_id": tenant_a_id})
        
        period_id = str(uuid4())
        await rls_session.execute(text("""
            INSERT INTO accounting_period (id, book_id, period_name, start_date, end_date, status)
            VALUES (:id, :book_id, '2026-03', '2026-03-01', '2026-03-31', 'OPEN')
        """), {"id": period_id, "book_id": book_id})
        
        je_id = str(uuid4())
        entry_number = f"JE-POST-{uuid4().hex[:6]}"
        await rls_session.execute(text("""
            INSERT INTO journal_entry (id, book_id, period_id, legal_entity_id, entry_number, entry_date, status)
            VALUES (:id, :book_id, :period_id, :le_id, :entry_number, '2026-03-15', 'POSTED')
        """), {"id": je_id, "book_id": book_id, "period_id": period_id, "le_id": tenant_a_id, "entry_number": entry_number})
        
        await rls_session.commit()
        
        # Set context
        await rls_session.execute(
            text("SET LOCAL app.current_tenant_id = '" + tenant_a_id + "'")
        )
        
        # Try to modify posted entry - should fail
        with pytest.raises(Exception) as exc_info:
            await rls_session.execute(text("""
                UPDATE journal_entry SET description = 'modified' WHERE id = :id
            """), {"id": je_id})
        
        assert "POSTED" in str(exc_info.value) or "modify" in str(exc_info.value).lower()

    async def test_cannot_delete_closed_period(
        self, rls_session: AsyncSession, tenant_a_id: str
    ):
        """Test that CLOSED periods cannot be deleted."""
        # Setup
        code_a = f"TENA{uuid4().hex[:4].upper()}"
        await rls_session.execute(text("""
            INSERT INTO legal_entity (id, code, name, country, functional_currency, is_active)
            VALUES (:id, :code, 'Tenant A', 'US', 'USD', true)
        """), {"id": tenant_a_id, "code": code_a})
        
        book_id = str(uuid4())
        await rls_session.execute(text("""
            INSERT INTO book (id, legal_entity_id, book_type, name, is_active)
            VALUES (:id, :le_id, 'ACCRUAL', 'Test Book', true)
        """), {"id": book_id, "le_id": tenant_a_id})
        
        period_id = str(uuid4())
        await rls_session.execute(text("""
            INSERT INTO accounting_period (id, book_id, period_name, start_date, end_date, status)
            VALUES (:id, :book_id, '2026-02', '2026-02-01', '2026-02-28', 'CLOSED')
        """), {"id": period_id, "book_id": book_id})
        
        await rls_session.commit()
        
        # Set context
        await rls_session.execute(
            text("SET LOCAL app.current_tenant_id = '" + tenant_a_id + "'")
        )
        
        # Try to delete closed period - should fail
        with pytest.raises(Exception) as exc_info:
            await rls_session.execute(text("DELETE FROM accounting_period WHERE id = :id"), 
                                      {"id": period_id})
        
        assert "CLOSED" in str(exc_info.value) or "delete" in str(exc_info.value).lower()


class TestBusinessConstraints:
    """Test business constraint validation."""

    async def test_journal_line_debit_or_credit(
        self, rls_session: AsyncSession, tenant_a_id: str
    ):
        """Test that journal lines must have either debit or credit, not both."""
        # Setup (abbreviated)
        code_a = f"TENA{uuid4().hex[:4].upper()}"
        await rls_session.execute(text("""
            INSERT INTO legal_entity (id, code, name, country, functional_currency, is_active)
            VALUES (:id, :code, 'Tenant A', 'US', 'USD', true)
        """), {"id": tenant_a_id, "code": code_a})
        
        book_id = str(uuid4())
        await rls_session.execute(text("""
            INSERT INTO book (id, legal_entity_id, book_type, name, is_active)
            VALUES (:id, :le_id, 'ACCRUAL', 'Test Book', true)
        """), {"id": book_id, "le_id": tenant_a_id})
        
        period_id = str(uuid4())
        await rls_session.execute(text("""
            INSERT INTO accounting_period (id, book_id, period_name, start_date, end_date, status)
            VALUES (:id, :book_id, '2026-03', '2026-03-01', '2026-03-31', 'OPEN')
        """), {"id": period_id, "book_id": book_id})
        
        gl_account_id = str(uuid4())
        await rls_session.execute(text("""
            INSERT INTO gl_account (id, book_id, account_code, account_name, account_type, is_active)
            VALUES (:id, :book_id, 'CASH', 'Cash', 'ASSET', true)
        """), {"id": gl_account_id, "book_id": book_id})
        
        je_id = str(uuid4())
        entry_number = f"JE-TEST-{uuid4().hex[:6]}"
        await rls_session.execute(text("""
            INSERT INTO journal_entry (id, book_id, period_id, legal_entity_id, entry_number, entry_date, status)
            VALUES (:id, :book_id, :period_id, :le_id, :entry_number, '2026-03-15', 'DRAFT')
        """), {"id": je_id, "book_id": book_id, "period_id": period_id, "le_id": tenant_a_id, "entry_number": entry_number})
        
        await rls_session.commit()
        
        # Try to insert a line with both debit and credit - should fail
        with pytest.raises(Exception) as exc_info:
            await rls_session.execute(text("""
                INSERT INTO journal_line (id, journal_entry_id, book_id, gl_account_id, line_number, 
                                         debit_tc, credit_tc, currency)
                VALUES (:id, :je_id, :book_id, :gl_id, 1, 100.00, 100.00, 'USD')
            """), {"id": str(uuid4()), "je_id": je_id, "book_id": book_id, "gl_id": gl_account_id})
        
        # Check constraint should prevent this
        assert "chk_journal_line" in str(exc_info.value).lower() or "check" in str(exc_info.value).lower()

    async def test_valid_currency_format(
        self, rls_session: AsyncSession, tenant_a_id: str
    ):
        """Test that currency must be valid 3-letter code."""
        # Setup
        code_a = f"TENA{uuid4().hex[:4].upper()}"
        await rls_session.execute(text("""
            INSERT INTO legal_entity (id, code, name, country, functional_currency, is_active)
            VALUES (:id, :code, 'Tenant A', 'US', 'USD', true)
        """), {"id": tenant_a_id, "code": code_a})
        
        await rls_session.commit()
        
        # Try to insert with invalid currency - should fail
        with pytest.raises(Exception) as exc_info:
            await rls_session.execute(text("""
                INSERT INTO legal_entity (id, code, name, country, functional_currency, is_active)
                VALUES (:id, 'TEST', 'Test', 'US', 'INVALID', true)
            """), {"id": str(uuid4())})
        
        assert "currency" in str(exc_info.value).lower() or "chk_" in str(exc_info.value).lower()
