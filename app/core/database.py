"""Database connection and session management"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.db_metadata import Base
from app.core.config import settings

# Import all models so metadata is populated at runtime (Alembic uses db_metadata + env.py imports)
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
from app.modules.affiliates.models import (
    AffiliatePartner,
    AffiliateAgreement,
    AffiliateEarningEvent,
    AffiliatePayout,
)
# PayRuleSet, PayRule, StatContributionRule, TaxWithholdingTable, PayrollExportTemplate, PayrollLiabilityBalance
# are not yet implemented in payroll.models; omit until pay_rule_model etc. exist
from app.modules.core.models import (
    AuditLog,
    IdempotencyKey,
)

# Re-export Base for backward compatibility (callers use app.core.database.Base)
__all__ = ["Base", "engine", "AsyncSessionLocal", "get_db_session"]

# Create async engine
engine = create_async_engine(
    settings.effective_database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    echo=settings.debug,
    connect_args={
        "statement_cache_size": 0,  # Required for Supabase transaction pooler (pgBouncer)
    },
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db_session() -> AsyncSession:
    """Dependency for getting database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
