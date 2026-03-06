"""Alembic environment configuration.

Migrations use ONLY DATABASE_URL (or FINANCIAL_MANAGEMENT_DATABASE_URL).
No JWT_SECRET_KEY or other runtime/auth config. Do not import app.core.config
or app.core.database so that CI/CD and migration-only environments work.
"""
import os
from pathlib import Path

# Load .env / .env.local from repo root so "alembic upgrade head" works when run from repo
_repo_root = Path(__file__).resolve().parent.parent.parent  # migrations -> database -> repo
try:
    from dotenv import load_dotenv
    # CRITICAL: override=False means existing env vars (set by user) take precedence
    load_dotenv(_repo_root / ".env", override=False)
    load_dotenv(_repo_root / ".env.local", override=False)
    if Path.cwd() != _repo_root:
        load_dotenv(Path.cwd() / ".env", override=False)
        load_dotenv(Path.cwd() / ".env.local", override=False)
except ImportError:
    pass

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import asyncio

# DB-only: Base and metadata, no app settings
from app.core.db_metadata import Base

# Load all models so target_metadata is populated for autogenerate
from app.modules.general_ledger.models import (
    LegalEntity,
    Book,
    Dimension,
    DimensionValue,
    GLAccount,
    GLAccountMapping,
    AccountingPeriod,
    JournalEntry,
    JournalLine,
    JournalLineDimension,
    ReconciliationSession,
    ReconciliationMatch,
    ExternalSyncCursor,
    SourceObjectMap,
    PeriodCloseChecklist,
    TreasurySyncBatch,
)
from app.modules.ar.models import (
    ARCustomer,
    ARInvoice,
    ARInvoiceLine,
    ARPayment,
    ARAllocation,
    RevenueSchedule,
    RevenueSchedulePeriod,
    BillingSyncBatch,
)
from app.modules.payroll.models import (
    HREmployee,
    HREmployeeBank,
    PayGroup,
    PayComponentDefinition,
    PayComponentAssignment,
    PayrollRun,
    PayrollRunItem,
    PayrollRunComponentLine,
    PayrollPaymentBatch,
    CommissionPlan,
    CommissionRule,
    CommissionLedger,
    BonusPlan,
    BonusResult,
)
from app.modules.intercompany.models import (
    IntercompanyTransfer,
    RoyaltyAgreement,
    RoyaltyCalculation,
    IntercompanyBalance,
)
from app.modules.treasury.models import (
    BankAccount,
    BankTransaction,
    Settlement,
    FXConversion,
    Transfer,
    SyncCursor,
)
from app.modules.ap.models import (
    APVendor,
    APBill,
    APBillLine,
    APPayment,
    APAllocation,
    APWithholdingProfile,
)
# Affiliate models not yet implemented; omit so migrations can load
from app.modules.core.models.idempotency_model import IdempotencyKey
from app.modules.core.models.audit_log_model import AuditLog

# this is the Alembic Config object
config = context.config

# DATABASE_URL only: no JWT, no app settings. Prefer pooler when set (often more reachable).
def _get_url(name: str) -> str | None:
    v = os.getenv(name)
    return (v or "").strip() or None

 # Prefer Transaction pooler (port 6543) for migrations - more stable than session pooler for psycopg2
_db_url = (
    _get_url("FINANCIAL_MANAGEMENT_DATABASE_TRANSACTION_POOLER_URL")
    or _get_url("FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL")
    or _get_url("FINANCIAL_MANAGEMENT_DATABASE_POOLER_URL")
    or _get_url("DATABASE_URL")
    or _get_url("FINANCIAL_MANAGEMENT_DATABASE_URL")
)
if not _db_url:
    hint = (
        "Install python-dotenv and ensure .env or .env.local exists in the repo root, "
        "or set FINANCIAL_MANAGEMENT_DATABASE_SESSION_POOLER_URL, FINANCIAL_MANAGEMENT_DATABASE_POOLER_URL, "
        "DATABASE_URL, or FINANCIAL_MANAGEMENT_DATABASE_URL in your shell."
    )
    raise RuntimeError(
        "A database URL is required for migrations. "
        "Do not rely on app config (e.g. JWT_SECRET_KEY) here. " + hint
    )
db_url = _db_url.replace("+asyncpg", "") if "+asyncpg" in _db_url else _db_url
# SQLAlchemy requires "postgresql" dialect; Supabase/pooler often use postgres://
if db_url.startswith("postgres://"):
    db_url = "postgresql://" + db_url[len("postgres://"):]
# ConfigParser treats % as interpolation; escape for URLs like postgres:pass%40word
db_url_safe = db_url.replace("%", "%%")
config.set_main_option("sqlalchemy.url", db_url_safe)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Add your model's MetaData object here for 'autogenerate' support
target_metadata = Base.metadata

# Other values from the config
config.set_main_option("script_location", "infra/database/migrations")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """Run migrations with connection"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    import sqlalchemy.exc
    # For async, we need to create a sync engine for Alembic
    # Add connect_args for Supabase pooler compatibility
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args={
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        },
    )
    try:
        with connectable.connect() as connection:
            do_run_migrations(connection)
    except sqlalchemy.exc.OperationalError as e:
        pooler_hint = (
            " If the direct host (db.*.supabase.co) fails DNS, set FINANCIAL_MANAGEMENT_DATABASE_POOLER_URL "
            "in .env.local to the Session/Transaction pooler URL from Supabase (Project Settings → Database → "
            "Connection string → Transaction or Session; host like *.pooler.supabase.com:6543)."
        )
        raise RuntimeError(
            "Migrations could not connect to the database. "
            "Check that the URL host is reachable (DNS/network)." + pooler_hint
        ) from e
    finally:
        connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
