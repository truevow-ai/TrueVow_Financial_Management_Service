"""Database connection and session management"""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from fastapi import Request
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
# DEFERRED (P1 cut): the affiliates module is scaffolding only (models, no
# services/repositories/API routes). It is parked to avoid creating unused
# tables. Files are preserved under app/modules/affiliates/. Re-enable this
# import when affiliate payouts are actually built.
# from app.modules.affiliates.models import (
#     AffiliatePartner,
#     AffiliateAgreement,
#     AffiliateEarningEvent,
#     AffiliatePayout,
# )
# PayRuleSet, PayRule, StatContributionRule, TaxWithholdingTable, PayrollExportTemplate, PayrollLiabilityBalance
# are not yet implemented in payroll.models; omit until pay_rule_model etc. exist
from app.modules.core.models import (
    AuditLog,
    IdempotencyKey,
    RowAuditLog,
    AuthAuditLog,
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


async def get_db_session(request: Request = None) -> AsyncSession:  # type: ignore[assignment]
    """
    Dependency for getting a tenant-scoped, audit-context-aware database session.

    Automatically injects three PostgreSQL GUC sets at the start of each
    transaction so that:
      1. RLS policies are enforced without any additional work in route handlers.
      2. The fn_row_audit_log() trigger captures actor identity on every mutation.

    GUCs set (all SET LOCAL — transaction-scoped, cleared at commit/rollback):

      app.current_tenant_id   — tenant UUID for RLS USING clauses
      app.current_user_id     — actor user ID for row_audit_log
      app.current_user_role   — actor role  for row_audit_log
      app.correlation_id      — request correlation ID for row_audit_log

    Tenant resolution order:
      1. Path parameter  : `entity_id`  (e.g. /entities/{entity_id}/...)
      2. Request header  : `X-Legal-Entity-ID`

    Actor resolution order (set by audit_context_middleware):
      request.state.user_id   — extracted from Bearer JWT (best-effort)
      request.state.user_role — extracted from Bearer JWT (best-effort)
      request.state.correlation_id — set by correlation_id_middleware

    All GUCs default to NULL / absent if not available (public routes,
    background tasks, migration scripts) — the audit trigger still fires
    and records the row with NULL actor fields.

    SET LOCAL is transaction-scoped — automatically cleared at commit/rollback.
    Safe for Supabase session pooler (pgBouncer).
    """
    async with AsyncSessionLocal() as session:
        try:
            if request is not None:
                # 1. Tenant context for RLS
                entity_id = (
                    request.path_params.get("entity_id")
                    or request.headers.get("X-Legal-Entity-ID")
                )
                if entity_id:
                    await session.execute(
                        text("SET LOCAL app.current_tenant_id = :eid"),
                        {"eid": str(entity_id)},
                    )

                # 2. Actor user ID for row_audit_log trigger
                user_id = getattr(request.state, "user_id", None)
                if user_id:
                    await session.execute(
                        text("SET LOCAL app.current_user_id = :uid"),
                        {"uid": str(user_id)},
                    )

                # 3. Actor role for row_audit_log trigger
                user_role = getattr(request.state, "user_role", None)
                if user_role:
                    await session.execute(
                        text("SET LOCAL app.current_user_role = :role"),
                        {"role": str(user_role)},
                    )

                # 4. Correlation ID for row_audit_log trigger
                correlation_id = getattr(request.state, "correlation_id", None)
                if correlation_id:
                    await session.execute(
                        text("SET LOCAL app.correlation_id = :cid"),
                        {"cid": str(correlation_id)},
                    )

                # 5. Canonical TEXT org_id (Security Contract v1 § 1.1)
                #    app.current_org_id = Clerk org_id (TEXT) — distinct from
                #    app.current_tenant_id which holds the UUID for RLS.
                auth_ctx = getattr(request.state, "auth_context", None)
                if auth_ctx is not None:
                    org_id = getattr(auth_ctx, "org_id", None)
                    if org_id:
                        await session.execute(
                            text("SET LOCAL app.current_org_id = :oid"),
                            {"oid": str(org_id)},
                        )
                    fm_role = getattr(auth_ctx, "fm_role", None)
                    if fm_role:
                        await session.execute(
                            text("SET LOCAL app.current_user_role = :role"),
                            {"role": str(fm_role)},
                        )

            yield session
        finally:
            await session.close()
