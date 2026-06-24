"""Pytest configuration and fixtures"""
import os

# Load .env / .env.local before reading DATABASE_URL so tests use project DB when present
try:
    from dotenv import load_dotenv
    load_dotenv(".env")
    load_dotenv(".env.local")
except Exception:
    pass

# Ensure tests can load app config when JWT secret is not in env (e.g. minimal .env.local or CI)
if not os.environ.get("JWT_SECRET_KEY") and not os.environ.get("FINANCIAL_MANAGEMENT_SECRET_KEY"):
    os.environ["FINANCIAL_MANAGEMENT_SECRET_KEY"] = "test-secret-do-not-use-in-production"

import pytest
import asyncio
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool
from uuid import uuid4
from datetime import date, datetime

# Allow Postgres JSONB columns (e.g. row_audit_log.before_data) to be created
# under the in-memory SQLite engine used for offline unit tests.
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects.postgresql import JSONB, ARRAY as PG_ARRAY


@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):  # noqa: ANN001, ANN201
    return "JSON"


@compiles(PG_ARRAY, "sqlite")
def _compile_array_sqlite(element, compiler, **kw):  # noqa: ANN001, ANN201
    return "JSON"


from app.core.database import Base, get_db_session
from app.modules.general_ledger.models.legal_entity_model import LegalEntity
from app.modules.general_ledger.models.book_model import Book, BookType
from app.modules.general_ledger.models.accounting_period_model import AccountingPeriod, PeriodStatus
from app.modules.general_ledger.models.journal_entry_model import JournalEntry, JournalEntryStatus
from app.modules.general_ledger.models.gl_account_model import GLAccount, AccountType
from app.modules.payroll.models.payroll_run_model import PayrollRun, PayrollRunStatus
from app.modules.payroll.models.pay_group_model import PayGroup, PayFrequency, PayDayRule
from app.modules.treasury.models.bank_account_model import BankAccount
from app.modules.treasury.models.bank_transaction_model import BankTransaction, TransactionType


def _test_database_url() -> str:
    """Use TEST_DATABASE_URL when set; otherwise in-memory SQLite so pytest runs without network."""
    url = os.environ.get("TEST_DATABASE_URL")
    if url:
        if "postgresql" in url or "postgres://" in url:
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1).replace("postgres://", "postgresql+asyncpg://", 1)
        return url
    try:
        import aiosqlite  # noqa: F401
        return "sqlite+aiosqlite:///:memory:"
    except ImportError:
        pytest.skip(
            "Tests need aiosqlite (pip install aiosqlite) or TEST_DATABASE_URL set to Postgres."
        )


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session"""
    url = _test_database_url()
    kw = {"echo": False}
    if "sqlite" in url:
        kw["connect_args"] = {"check_same_thread": False}
        kw["poolclass"] = StaticPool
    engine = create_async_engine(url, **kw)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session_maker = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session_maker() as session:
        yield session
    
    async with engine.begin() as conn:
        if "postgresql" in url:
            # Use CASCADE to handle FK dependencies from unmanaged tables
            for table in reversed(Base.metadata.sorted_tables):
                await conn.execute(
                    text(f"DROP TABLE IF EXISTS {table.name} CASCADE")
                )
        else:
            await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture
async def test_legal_entity(test_db: AsyncSession) -> LegalEntity:
    """Create test legal entity"""
    entity = LegalEntity(
        id=uuid4(),
        name="Test Entity",
        code="TEST",
        country="US",
        functional_currency="USD",
        is_active=True
    )
    test_db.add(entity)
    await test_db.commit()
    await test_db.refresh(entity)
    return entity


@pytest.fixture
async def test_book(test_db: AsyncSession, test_legal_entity: LegalEntity) -> Book:
    """Create test book"""
    book = Book(
        id=uuid4(),
        legal_entity_id=test_legal_entity.id,
        book_type=BookType.ACCRUAL,
        name="Test ACCRUAL Book",
        is_active=True
    )
    test_db.add(book)
    await test_db.commit()
    await test_db.refresh(book)
    return book


@pytest.fixture
async def test_period(test_db: AsyncSession, test_book: Book) -> AccountingPeriod:
    """Create test accounting period covering the current month.

    Spanning the current month keeps tests that post entries dated
    ``date.today()`` working regardless of when they run.
    """
    import calendar
    today = date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    period = AccountingPeriod(
        id=uuid4(),
        book_id=test_book.id,
        period_name=today.strftime("%Y-%m"),
        period_start=today.replace(day=1),
        period_end=today.replace(day=last_day),
        status=PeriodStatus.OPEN
    )
    test_db.add(period)
    await test_db.commit()
    await test_db.refresh(period)
    return period


@pytest.fixture
async def test_gl_accounts(test_db: AsyncSession, test_book: Book):
    """Create two GL accounts (debit and credit) for test_book for balanced JE lines."""
    from decimal import Decimal
    dr_account = GLAccount(
        id=uuid4(),
        book_id=test_book.id,
        account_code="TEST-DR",
        account_name="Test Debit Account",
        account_type=AccountType.EXPENSE,
        is_active=True,
    )
    cr_account = GLAccount(
        id=uuid4(),
        book_id=test_book.id,
        account_code="TEST-CR",
        account_name="Test Credit Account",
        account_type=AccountType.LIABILITY,
        is_active=True,
    )
    test_db.add(dr_account)
    test_db.add(cr_account)
    await test_db.commit()
    await test_db.refresh(dr_account)
    await test_db.refresh(cr_account)
    return (dr_account, cr_account)


@pytest.fixture
async def test_pay_group(test_db: AsyncSession, test_legal_entity: LegalEntity):
    """Create a pay group for payroll run tests."""
    group = PayGroup(
        id=uuid4(),
        legal_entity_id=test_legal_entity.id,
        group_code="TEST-PG",
        group_name="Test Pay Group",
        frequency=PayFrequency.MONTHLY,
        payroll_currency="USD",
        pay_day_rule=PayDayRule.LAST_BUSINESS_DAY,
        is_active=True,
    )
    test_db.add(group)
    await test_db.commit()
    await test_db.refresh(group)
    return group


@pytest.fixture
async def test_user_id() -> str:
    """Test user ID"""
    return str(uuid4())
