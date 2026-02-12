"""API v1 routes"""
from fastapi import APIRouter
from app.modules.general_ledger.api.routes import (
    coa_routes,
    period_routes,
    journal_entry_routes,
    treasury_sync_routes,
    reconciliation_routes
)
from app.modules.treasury.api.routes import (
    bank_account_routes,
    bank_transaction_routes,
    transfer_routes,
    fx_conversion_routes,
    settlement_routes
)
from app.modules.ar.api.routes import (
    billing_sync_routes,
    deferred_revenue_routes,
    ar_routes
)
from app.modules.payroll.api.routes import (
    payroll_run_routes,
    payment_batch_routes
)
from app.modules.intercompany.api.routes import (
    intercompany_transfer_routes,
    royalty_routes,
    reconciliation_routes as intercompany_reconciliation_routes
)
from app.modules.reporting.api.routes import report_routes
from app.modules.ap.api.routes import ap_bill_routes

router = APIRouter()

# Include general ledger routes
router.include_router(coa_routes.router)
router.include_router(period_routes.router)
router.include_router(journal_entry_routes.router)
router.include_router(treasury_sync_routes.router)
router.include_router(reconciliation_routes.router)

# Include treasury routes
router.include_router(bank_account_routes.router)
router.include_router(bank_transaction_routes.router)
router.include_router(transfer_routes.router)
router.include_router(fx_conversion_routes.router)
router.include_router(settlement_routes.router)

# Include AR routes
router.include_router(billing_sync_routes.router)
router.include_router(deferred_revenue_routes.router)
router.include_router(ar_routes.router)

# Include payroll routes
router.include_router(payroll_run_routes.router)
router.include_router(payment_batch_routes.router)

# Include intercompany routes
router.include_router(intercompany_transfer_routes.router)
router.include_router(royalty_routes.router)
router.include_router(intercompany_reconciliation_routes.router)

# Include reporting routes
router.include_router(report_routes.router)

# Include AP routes
router.include_router(ap_bill_routes.router)

# Health endpoint is in main.py
# Other routes will be added as modules are implemented
